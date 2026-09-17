# Playwright visual pilot — 2026-09

## Result

An approved private Storybook consumer was exercised locally through the
versioned `storybook-capture` adapter and the existing
`playwright_visual_producer.py`. The private repository name, source tree,
baseline files and screenshots are deliberately not published in this repo.

| Metric | Observed value |
|---|---:|
| Capture adapter version | 1 |
| Producer schema version | 1 |
| Browser | Chromium 145.0.7632.6 |
| Protected views | 3 |
| Viewport | 1280 × 720 |
| Comparisons | 3 |
| Total pixels | 2,764,800 |
| Changed pixels | 0 |
| Diff ratio | 0.000000 |
| Threshold | 0.0 |
| Producer duration | 4.547 s |
| Receipt status | pass |

## What this proves

- A real browser launched locally and rendered the exact protected Storybook
  view set.
- The adapter rejected the possibility of silently expanding coverage: story
  IDs, viewports and PNG output paths are manifest-bound.
- The producer decoded candidate and baseline images, generated diff artifacts,
  and emitted a provenance-bound zero-diff receipt.

## What this does not prove

- It is not a CI trust anchor, signed attestation or branch-protection check.
- It does not select the browser image, baseline owner, artifact retention or
  homelab isolation policy.
- It does not authorize uploading private screenshots to GitHub, Chromatic or
  any other service.

The next activation decision is therefore operational: choose an immutable
browser/OS image, protected baseline storage, a disposable worker boundary and
an approval policy for baseline updates. The deterministic receipt contract is
ready for that decision.
