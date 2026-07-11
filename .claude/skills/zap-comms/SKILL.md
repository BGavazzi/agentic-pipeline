---
name: zap-comms
description: Generic WhatsApp messaging via a self-hosted Evolution API instance — send text/media messages, read inbound messages, and manage webhook-delivered events. Use when the user wants to send a WhatsApp notification, read a conversation, or wire WhatsApp as a notification channel. BYO instance — no phone number or contact list baked in. STATUS - reference skill (auth + send/receive), consumed by whatsapp-clickup and notifier's WhatsApp channel (V2 backlog).
tools: Bash, WebFetch, Read
---

# Zap Comms — WhatsApp via Evolution API

Generic messaging primitive over a self-hosted [Evolution API](https://
github.com/EvolutionAPI/evolution-api) instance. No phone number, contact,
or bot persona is hardcoded — every recipient and instance name is supplied
by the caller or read from env.

`whatsapp-clickup` builds a specific ClickUp-creation flow on top of this;
`notifier`'s WhatsApp channel (V2 backlog) would also call through here
rather than talking to Evolution API directly.

---

## When to Use

- Send a WhatsApp text/media message to a number or group
- Read recent inbound messages from an instance
- Set up or verify a webhook so inbound messages reach this session/pipeline
- Any operation where the user says "WhatsApp", "zap", "send a message to"

---

## Auth & Setup

### Environment variables

| Variable | Purpose |
|---|---|
| `EVOLUTION_API_URL` | Base URL of the self-hosted instance, e.g. `https://<host>:<port>` |
| `EVOLUTION_API_KEY` | Global or instance-scoped API key. Header: `apikey: <key>` |
| `EVOLUTION_INSTANCE_NAME` | Which WhatsApp session/instance to act as (Evolution API supports multiple instances per deployment) |

Read from the process environment only. Never echo the key into logs or commits.

### Required header

```
apikey: <EVOLUTION_API_KEY>
Content-Type: application/json
```

---

## Core operations

### Send a text message

```bash
POST {EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}
{
  "number": "<E.164 without '+', e.g. 5511999999999>",
  "text": "<message>"
}
```

### Send media

```bash
POST {EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE_NAME}
{
  "number": "<E.164 without '+'>",
  "mediatype": "image | video | document",
  "media": "<URL or base64>",
  "caption": "<optional>"
}
```

### Read recent messages (chat history)

```bash
GET {EVOLUTION_API_URL}/chat/findMessages/{EVOLUTION_INSTANCE_NAME}
{ "where": { "key": { "remoteJid": "<jid>" } }, "limit": 20 }
```

### Instance status

```bash
GET {EVOLUTION_API_URL}/instance/connectionState/{EVOLUTION_INSTANCE_NAME}
# → { "state": "open" | "connecting" | "close" }
```

`state != "open"` → the instance is logged out or disconnected; don't attempt
sends, surface the state to the caller instead.

### Webhook (inbound messages)

Evolution API pushes inbound events to a configured webhook URL rather than
this skill polling for them. Setup (one-time, per instance):

```bash
POST {EVOLUTION_API_URL}/webhook/set/{EVOLUTION_INSTANCE_NAME}
{
  "url": "<your receiving endpoint>",
  "events": ["MESSAGES_UPSERT"]
}
```

This skill does not run a receiving server — that's the calling
application's responsibility (e.g. `whatsapp-clickup`'s bot process). If no
receiving endpoint exists yet, this skill can still be used purely to send.

---

## Number/JID formatting

WhatsApp JIDs look like `<number>@s.whatsapp.net` (individual) or
`<group_id>@g.us` (group). Most send endpoints accept the bare number and
handle the suffix internally — confirm against the specific Evolution API
version deployed, since endpoint shapes have changed across releases.

---

## Error handling

| Code | Meaning | Action |
|---|---|---|
| `400` | Malformed number or payload | Check E.164 formatting |
| `401`/`403` | Invalid/missing `apikey` | Check `EVOLUTION_API_KEY` |
| `404` | Instance name doesn't exist | Check `EVOLUTION_INSTANCE_NAME`, list instances via `/instance/fetchInstances` |
| Instance `state != "open"` | Session logged out / QR not scanned | Surface to caller; don't retry sends blindly |
| Network timeout | Self-hosted instance may be down | Backoff + retry once; then STOP, report |

---

## Hard rules

- **Never hardcode a phone number or instance name** in this file — always caller-supplied or env.
- **`EVOLUTION_API_KEY` never committed.** Check before `git add`.
- **Check instance state before sending** — a send against a disconnected instance fails silently in some Evolution API versions; verifying state first gives a clearer error.
- **Never post credentials or secrets in a message body.**

## Failure modes

| Error | What to do |
|---|---|
| Instance disconnected | Report state, don't send, don't loop-retry |
| Recipient number malformed | Report the exact malformed value, don't guess a correction |
| Webhook URL unreachable from the Evolution API host | Inbound flow silently stops; this is infra outside this skill's scope — flag to the user, don't debug their network |

## Skills consumed / produced

- Consumed by: [[whatsapp-clickup]], and `notifier`'s WhatsApp channel (V2 backlog — see `../notifier/SKILL.md` §14).
- Upstream: none — base adapter.
