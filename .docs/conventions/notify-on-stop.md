# Convention — Notify the Human When the Agent Stops (Stop hook)

> Status: active. Generalizes the pattern "notify me every time you stop working."

## Principle

In long/autonomous runs, the human isn't watching the terminal. When the agent **stops** (end of turn, idle, end of task), it must **push a notification** to the human's async channel (WhatsApp/Slack/etc.), so the person knows they can re-engage — without having to guess the cadence.

This is an **event-triggered automatic behavior** → **it must be a hook** in `settings.json`. Memory/preference does NOT trigger automatic action; only the harness executes hooks. Right event: **`Stop`** (fires when Claude stops, including clear/resume/compact).

Related: responses in a public channel call for follow-up in the same channel; see also the "convergence is not closure" rule (keep going until an explicit stop signal).

## Form (generic)

`.claude/settings.json` (project or user scope):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "shell": "bash",
            "command": "<notification-command> || true",
            "timeout": 30,
            "statusMessage": "Notifying the human…"
          }
        ]
      }
    ]
  }
}
```

Rules:
- **Never block the stop.** Always exit with success (`|| true`, and silence stderr in the script).
- **`shell: "bash"`** on Windows to avoid falling into PowerShell (assumes Git Bash is present).
- **CONTEXTUAL message, not static.** Stop fires at EVERY end of turn — a static string ("Claude stopped") becomes useless spam. The agent writes a short note about what it did in the turn to a file (e.g.: `~/.claude/claude-stop-note.txt`) and the script sends its contents.
- **Dedup by content.** The script saves the last sent message; if the note hasn't changed, do NOT resend → turns with no news don't ping. Without this the user receives ~1 msg/turn (every few minutes in a long run) and complains — real learning from the `teste_refactor_whitelabel` run.
- **Script, not a giant one-liner.** Encapsulate in a script (`~/.claude/zap_notify.sh`) and reference it.
- The command MUST NOT leak secrets: delegate sending to a component that already has the credentials (e.g.: the bot container), instead of reading API keys in the hook.

## Local implementation (WhatsApp via bot)

Dependencies (specific to the WhatsApp channel — which is why this does NOT go in the repo-shared `settings.json`, only in the local/user settings of whoever has the environment):
- WhatsApp bot container running (Docker), with Evolution configured (`EVOLUTION_API_URL`, `EVOLUTION_INSTANCE`, `EVOLUTION_API_KEY` in the container env — see `<your-bot-repo>`).
- Script `~/.claude/zap_notify.sh` that does `docker exec <bot-container> python3 …` posting to `POST {EVOLUTION_API_URL}/message/sendText/{INSTANCE}` with `apikey` header and `{number,text}` body. Credentials stay inside the container — the hook never reads them.
- Destination: human's JID (e.g.: `<phone-number>`). See JID directory in `<your-bot-repo>`.

Hook command (example):
```
bash "~/.claude/zap_notify.sh" || true
```
`zap_notify.sh` reads `~/.claude/claude-stop-note.txt` (contextual note the agent updates at the end of each turn), applies dedup against `~/.claude/.claude-stop-note.last`, and only then sends.

## Companion: polling for replies

When the agent SENDS something on the messaging channel and is waiting, it must **poll for replies every ~10 min** (in autonomous run, via ScheduleWakeup ~600s) until the human responds or the subject closes. This is agent behavior (not a hook), but it goes hand in hand with this convention.

## How to adopt in another repo/profile

1. Ensure the sending channel (e.g.: bot container + `~/.claude/zap_notify.sh`).
2. Add the `hooks.Stop` block to `settings.json` in the **appropriate scope**:
   - **user** (`~/.claude/settings.json`) if you want it across all projects on the machine;
   - **local** (`.claude/settings.local.json`, gitignored) for a project without affecting the team;
   - **NOT** in the repo-shared `.claude/settings.json` (would break for anyone without the channel/credentials).
3. Open `/hooks` once (or restart) if the watcher didn't have settings at session start.
