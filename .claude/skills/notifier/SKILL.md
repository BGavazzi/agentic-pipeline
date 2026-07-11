---
name: notifier
description: Posts structured comments to GitHub PR (mandatory) and ClickUp (opt-in — only when clickup_id present in payload AND CLICKUP_API_KEY set) at the end of the cycle (task.done, pr.opened, deploy.success/fail). Triggers - "notify closed cycle", "post comment to PR", "close the loop", OR direct invocation by builder/librarian downstream. STATUS - ready (V1 = GitHub PR always + ClickUp opt-in; Slack/WA/Telegram = backlog).
tools: Bash, Write, Read
---

# Notifier

**Runtime: open Claude Code session.** Human spec: `.docs/skills/notifier.md`.

V1 scope: **GitHub PR comment** (always) + **ClickUp comment** (opt-in). Slack/WhatsApp/Telegram/Discord go to V2.

**ClickUp opt-in:** if `clickup_id` absent from payload OR `CLICKUP_API_KEY` not set in environment → skip §3 entirely, jump to §4 (GitHub). No error, no STOP — ClickUp is an additional channel, not the primary one.

Composed inline by Librarian at cycle end, or invoked manually to post a structured update.

## 1. Inputs

- `event_type`: `task.done` | `pr.opened` | `pr.merged` | `pr.review.requested` | `deploy.success` | `deploy.fail`
- `payload`:
  - `clickup_id`: string (optional — absent or CLICKUP_API_KEY not set → skip ClickUp silently)
  - `pr_number`: int (mandatory if event touches GitHub)
  - `repo`: string `<org>/<repo>` (mandatory with `pr_number`)
  - `title`: string (1-line summary)
  - `body`: string (detail; can have newlines/accents/emoji)
  - `mentions`: list of strings (human name) — resolve via table below
- `channels_override`: optional — forces subset (`["clickup"]` or `["github"]`)

## 2. Mention resolution — members table

ClickUp user_ids (update via `GET /v2/list/<list_id>/member` as needed):

| Name | ClickUp user_id | GitHub handle |
|---|---|---|
| (add your team members here) | — | — |

If `mentions` contains a name **not in the table**: BEFORE posting, resolve via `curl GET .../v2/list/<list_id>/member` (local cache in `<repo>/.docs/notifier-mentions-cache.json` 24h) or `gh api search/users?q=<query>`. Failed → STOP, ask the user.

## 3. ClickUp comment — UTF-8-safe method (CRITICAL)

**Precondition:** `clickup_id` present AND `CLICKUP_API_KEY` set → execute §3. Otherwise: skip to §4.

**Inline `curl -d '...'` on Windows CORRUPTS UTF-8** (accents/emoji become U+FFFD irreversibly in ClickUp). Always use Write tool + `--data-binary` as below:

### 3.1. Build payload JSON via Write tool

```python
# Pseudo — this skill uses only Bash + Write
payload = {
  "comment": [
    # Each block {text, type, attributes} is a span; mention is type=tag.
    {"text": "TL;DR: ", "type": "text"},
    {"text": "<title>", "type": "text"},
    {"text": "\n\n", "type": "text"},
    {"text": "<body>", "type": "text"},
    # Structured mentions:
    {"text": " @<username>", "type": "tag",
     "attributes": {"user": {"id": <clickup_user_id>}}}
  ],
  "notify_all": false,
  "assignee": null
}
```

Write the JSON via **Write tool** (saves clean UTF-8, no BOM) to a temp file:

```
Write file: <path>/_tmp/notifier-<ts>.json
Content: <serialized JSON>
```

### 3.2. Post via curl --data-binary

```bash
curl -X POST \
  "https://api.clickup.com/api/v2/task/<CLICKUP_ID>/comment" \
  -H "Authorization: $CLICKUP_API_KEY" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @<path>/_tmp/notifier-<ts>.json
```

**Why `--data-binary` and not `-d`**: `-d` strips and re-encodes (losing UTF-8 on the Windows shell). `--data-binary` preserves the file's literal bytes.

### 3.3. Verify post

```bash
# Fetch the newly created comment
curl -s "https://api.clickup.com/api/v2/task/<CLICKUP_ID>/comment" \
  -H "Authorization: $CLICKUP_API_KEY" | \
  python -c "
import sys, json, os
os.environ['PYTHONUTF8']='1'
data = json.load(sys.stdin)
last = data['comments'][0]  # most recent
text = last.get('comment_text', '')
assert '?' not in text, 'CORRUPTION DETECTED'
print('OK:', last['id'])
"
```

If corrupted (despite the correct method): `DELETE /v2/comment/<comment_id>` + retry. If it persists 2x: STOP, report.

### 3.4. Cleanup

```bash
rm <path>/_tmp/notifier-<ts>.json
```

## 4. GitHub PR comment — gh CLI

```bash
gh pr comment <PR_NUMBER> --repo <REPO> --body "$(cat <<'EOF'
<title>

<body>

cc @<reviewer_handle>
EOF
)"
```

Mentions: `@<github_handle>` from table §2. If handle unknown: use `gh api search/users?q=<email>` or ask.

**Heredoc with `'EOF'` single-quoted** preserves `$` / backticks as literals.

## 5. Verification pre-irreversible (A5')

If `event_type ∈ {pr.merged, deploy.success}`, BEFORE posting:

```bash
# Confirm PR is actually merged
gh pr view <PR_NUMBER> --repo <REPO> --json state,mergedAt,reviews | \
  python -c "
import json, sys
d = json.load(sys.stdin)
assert d['state'] == 'MERGED', f'NOT MERGED: {d[\"state\"]}'
print('verified merged at', d['mergedAt'])
"
```

If mismatch between `payload` and actual state: STOP, report to user. **Memory ≠ source of truth** — verify against real state before posting.

## 6. Templates per event

### task.done

```
TL;DR: V1 of <feature> delivered.

Backend: PR <#NNN> ✅
Frontend: PR <#MMM> ✅
Validation: <smoke OK | product OK>

@<PO> — all good. Task status: done.
```

### pr.opened

```
PR <#NNN> opened: <title>

Branch: <branch>
Changes: <X files, +Y -Z>
Tests: <unit + e2e | smoke pending>

@<reviewer> — review request. Details in PR body §"What to ask the reviewer to focus on".
```

### deploy.fail

```
⚠️ Deploy fail — <service> <env>

Error: <1 factual line>
Logs: <link>

@<tech_lead> — escalated.
```

## 7. Idempotency

Local cache: `<repo>/.docs/notifier-idempotency.json` (gitignored).

Schema:
```json
{ "<event_id>:<channel>": <unix_ms>, ... }
```

Where `event_id = sha1(event_type + clickup_id + pr_number)`.

Pre-post: if entry exists and `< 24h`, log "duplicate skipped" + no-op.

## 8. Output

```
✅ Notifier — event: <event_type>
Channels:
  - GitHub <REPO>#<PR_NUMBER>: comment ✅
  - ClickUp <CLICKUP_ID>: comment <comment_id> ✅ (UTF-8 verified)  | skipped (no clickup_id or no CLICKUP_API_KEY)
Mentions resolved: <N>
Verification: <state=MERGED, mergedAt=...>
```

## 9. Hard rules

- **NEVER `curl -d` inline with UTF-8** — always Write tool + `--data-binary @file` + `charset=utf-8` (§3).
- **NEVER post credentials** ([[feedback-never-post-secrets-to-external-systems]]) in comments.
- **NEVER use `notify_all: true`** in ClickUp without explicit user authorization (spam → entire team).
- **Verify `gh pr view` BEFORE** asserting PR merged/approved (§5, rule A5').
- **Truncate body > 5000 chars** (ClickUp limit) and link to PR.
- **Mention IDs table** (§2) is NOT hardcoded forever — when user_id resolution fails 2x, hydrate via API + update.
- **Idempotency by event_id**, never by body hash.

## 10. Failure modes

| Error | What to do |
|---|---|
| CLICKUP_API_KEY absent but clickup_id present | Log "ClickUp skipped — CLICKUP_API_KEY not set"; continue with GitHub |
| ClickUp 401/403 | Check key wasn't rotated; log + STOP |
| ClickUp 429 (rate limit) | Backoff 90s, retry 1x |
| Encoding check fails post-post | DELETE comment + retry 1x; persists → STOP |
| `gh` 401 | `gh auth status` — if logged in, repo path is wrong |
| Mention name unresolved | Cache hit? Try API; failed → STOP, ask |
| pr.merged event but PR open | A5' triggered — STOP, alert caller |
| Network timeout > 30s | Backoff + retry 1x; persists → STOP |

## 11. Anti-patterns

- ❌ `curl -d '{"comment_text":"hello with accent"}'` — will corrupt. Always §3.
- ❌ Posting PR comment without verifying PR exists via `gh pr view`.
- ❌ Hardcode `notify_all: true` — becomes spam, team ignores it.
- ❌ Mention via free text `"@username"` in comment_text — becomes a string without structural tag. Use `type: tag` + `attributes.user.id`.
- ❌ Post `deploy.success` every time — V1 has no digest, but avoid noise (1x/deploy).
- ❌ Truncate stack error "to clean it up" in deploy.fail — preserve line 1; link log.

## 12. Skills consumed

- [[clickup-api]] — auth + rate limit reference (optional; only relevant if ClickUp is active).

## 13. Downstream skills

- None — Notifier is the last stage of the cycle.

## 14. V2 backlog (companion spec covers)

- WhatsApp via Evolution API (bot config)
- Slack incoming webhook (#shipped, #dev-alerts)
- Telegram bot
- Discord webhook
- Daily digest (aggregates `task.done` etc — off the critical path)
