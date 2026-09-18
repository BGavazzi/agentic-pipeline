#!/usr/bin/env node
/**
 * Capture a protected Storybook view set for playwright_visual_producer.py.
 *
 * The caller owns the view manifest and the Storybook process. This adapter
 * only navigates exact story IDs, uses the declared viewports, and emits the
 * producer's bounded JSON manifest on stdout. It never uploads screenshots,
 * talks to Chromatic, or accepts a candidate-supplied baseline.
 */
import fs from "node:fs/promises";
import path from "node:path";

const CAPTURE_ADAPTER_VERSION = 1;

const usage = `Usage: node storybook_capture.mjs --views-file MANIFEST [options]

Options:
  --views-file FILE       Protected schema-v1 baseline manifest (required)
  --storybook-url URL     Storybook origin (default: PIPELINE_VISUAL_STORYBOOK_URL or http://127.0.0.1:6006)
  --timeout-ms NUMBER     Per-view timeout (default: 30000)
  --help                  Show this help

Environment:
  PIPELINE_VISUAL_CAPTURE_DIR  Directory where candidate PNGs are written
`;

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const result = {
    viewsFile: null,
    storybookUrl: process.env.PIPELINE_VISUAL_STORYBOOK_URL || "http://127.0.0.1:6006",
    timeoutMs: 30000,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--help") {
      console.log(usage);
      process.exit(0);
    }
    if (value === "--views-file") result.viewsFile = argv[++index];
    else if (value === "--storybook-url") result.storybookUrl = argv[++index];
    else if (value === "--timeout-ms") result.timeoutMs = Number(argv[++index]);
    else fail(`unknown argument: ${value}`);
  }
  if (!result.viewsFile) fail("--views-file is required");
  if (!Number.isInteger(result.timeoutMs) || result.timeoutMs <= 0) {
    fail("--timeout-ms must be a positive integer");
  }
  return result;
}

async function readManifest(filename) {
  const value = JSON.parse(await fs.readFile(filename, "utf8"));
  if (value?.schema_version !== 1 || !Array.isArray(value.views) || value.views.length === 0) {
    fail("views manifest must be schema_version 1 with a non-empty views array");
  }
  const seen = new Set();
  return value.views.map((view) => {
    if (!view || typeof view.id !== "string" || typeof view.path !== "string" ||
        typeof view.viewport !== "string") {
      fail("each view needs id, path and viewport strings");
    }
    if (seen.has(view.id)) fail(`duplicate view id: ${view.id}`);
    seen.add(view.id);
    const match = /^(\d{2,4})x(\d{2,4})$/.exec(view.viewport);
    if (!match) fail(`invalid viewport for ${view.id}`);
    const width = Number(match[1]);
    const height = Number(match[2]);
    if (width < 240 || height < 240 || width > 4096 || height > 4096) {
      fail(`viewport out of bounds for ${view.id}`);
    }
    const normalizedPath = view.path.replaceAll("\\\\", "/");
    const basename = path.posix.basename(normalizedPath);
    if (!normalizedPath.startsWith(".pipeline-visual-captures/") ||
        normalizedPath.split("/").length !== 2 || !basename.endsWith(".png")) {
      fail(`view path must end in one PNG filename: ${view.id}`);
    }
    return { ...view, width, height, basename };
  });
}

async function waitForStorybook(origin, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const indexUrl = new URL("/index.json", origin);
  let lastError = "unavailable";
  while (Date.now() < deadline) {
    try {
      const response = await fetch(indexUrl);
      if (response.ok) return await response.json();
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error);
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  fail(`Storybook index did not become ready: ${lastError}`);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const origin = new URL(args.storybookUrl);
  if (!/^https?:$/.test(origin.protocol)) fail("Storybook URL must use http or https");
  const views = await readManifest(path.resolve(args.viewsFile));
  const index = await waitForStorybook(origin, args.timeoutMs);
  const entries = index?.entries || {};
  for (const view of views) {
    if (!Object.prototype.hasOwnProperty.call(entries, view.id)) {
      fail(`protected Storybook view is not present: ${view.id}`);
    }
  }

  const captureRoot = path.resolve(
    process.env.PIPELINE_VISUAL_CAPTURE_DIR || path.join(process.cwd(), ".pipeline-visual-captures"),
  );
  await fs.mkdir(captureRoot, { recursive: true });
  const { chromium } = await import("playwright");
  const browser = await chromium.launch({ headless: true });
  const captured = [];
  try {
    for (const view of views) {
      const output = path.join(captureRoot, view.basename);
      const page = await browser.newPage({ viewport: { width: view.width, height: view.height } });
      const pageErrors = [];
      page.on("pageerror", (error) => pageErrors.push(error.message));
      try {
        const storyUrl = new URL("/iframe.html", origin);
        storyUrl.searchParams.set("id", view.id);
        storyUrl.searchParams.set("viewMode", "story");
        await page.goto(storyUrl.toString(), { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
        await page.locator("#storybook-root").waitFor({ state: "visible", timeout: args.timeoutMs });
        await page.evaluate(async () => {
          if (document.fonts?.ready) await document.fonts.ready;
        });
        await page.screenshot({ path: output, animations: "disabled", caret: "hide" });
        if (pageErrors.length > 0) fail(`page error in ${view.id}: ${pageErrors[0]}`);
        captured.push({ id: view.id, path: `.pipeline-visual-captures/${view.basename}` });
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  process.stdout.write(`${JSON.stringify({
    schema_version: 1,
    adapter: "storybook-capture",
    adapter_version: CAPTURE_ADAPTER_VERSION,
    views: captured,
  })}\n`);
}

main().catch((error) => {
  process.stderr.write(`storybook_capture: ${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 2;
});
