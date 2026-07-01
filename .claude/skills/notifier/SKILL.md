---
name: notifier
description: Posta comments estruturados em ClickUp + GitHub PR no fim do ciclo (task.done, pr.opened, deploy.success/fail) usando os patterns UTF-8-safe + structured mentions já cravados em memória. Triggers - "notifica ciclo fechado", "manda comment pro PR e ClickUp", "fecha o loop", OU invocação direta por builder/librarian downstream. STATUS - ready (V1 = ClickUp + GitHub PR; Slack/WA/Telegram = backlog).
tools: Bash, Write, Read
---

# Notifier

**Runtime: sessão Claude Code aberta.** Spec humana: `.docs/skills/notifier.md`.

V1 escopo: **ClickUp comment + GitHub PR comment.** Slack/WhatsApp/Telegram/Discord ficam pra V2 (specificados no companion mas não runnable aqui).

Composta inline pelo Librarian no fim do ciclo, ou invocada manualmente pra postar update estruturado.

## 1. Inputs

- `event_type`: `task.done` | `pr.opened` | `pr.merged` | `pr.review.requested` | `deploy.success` | `deploy.fail`
- `payload`:
  - `clickup_id`: string (obrigatório se evento toca ClickUp)
  - `pr_number`: int (obrigatório se evento toca GitHub)
  - `repo`: string `<org>/<repo>` (obrigatório com `pr_number`)
  - `title`: string (1 linha resumo)
  - `body`: string (detalhe; pode ter newlines/acentos/emoji)
  - `mentions`: lista de strings (nome humano) — resolver via tabela abaixo
- `channels_override`: opcional — força subset (`["clickup"]` ou `["github"]`)

## 2. Mention resolution — tabela de membros

ClickUp user_ids (atualizar via `GET /v2/list/<list_id>/member` conforme necessário):

| Nome | ClickUp user_id | GitHub handle |
|---|---|---|
| (adicione membros da sua equipe aqui) | — | — |

Se `mentions` contém nome **não na tabela**: ANTES de postar, resolver via `curl GET .../v2/list/<list_id>/member` (cache local em `<repo>/.docs/notifier-mentions-cache.json` 24h) ou `gh api search/users?q=<query>`. Falhou → STOP, perguntar ao usuário.

## 3. ClickUp comment — método UTF-8-safe (CRÍTICO)

**Inline `curl -d '...'` no Windows CORROMPE UTF-8** (acentos/emoji viram U+FFFD irrecuperáveis no ClickUp). Memória [[clickup-api-org-conventions]] doc o gotcha — sempre seguir:

### 3.1. Build payload JSON via Write tool

```python
# Pseudo — esta skill usa Bash + Write apenas
payload = {
  "comment": [
    # Cada bloco {text, type, attributes} é um span; mention é type=tag.
    {"text": "TL;DR: ", "type": "text"},
    {"text": "<title>", "type": "text"},
    {"text": "\n\n", "type": "text"},
    {"text": "<body>", "type": "text"},
    # Mentions estruturadas:
    {"text": " @<username>", "type": "tag",
     "attributes": {"user": {"id": <clickup_user_id>}}}
  ],
  "notify_all": false,
  "assignee": null
}
```

Escrever o JSON via **Write tool** (grava UTF-8 limpo, sem BOM) num arquivo temp:

```
Write file: <path>/_tmp/notifier-<ts>.json
Content: <JSON serializado>
```

### 3.2. Post via curl --data-binary

```bash
curl -X POST \
  "https://api.clickup.com/api/v2/task/<CLICKUP_ID>/comment" \
  -H "Authorization: $CLICKUP_API_KEY" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @<path>/_tmp/notifier-<ts>.json
```

**Por que `--data-binary` e não `-d`**: `-d` strippa e re-encoda (perdendo UTF-8 no shell do Windows). `--data-binary` preserva bytes literais do arquivo.

### 3.3. Verificar pós-post

```bash
# Fetch o comment recém-criado
curl -s "https://api.clickup.com/api/v2/task/<CLICKUP_ID>/comment" \
  -H "Authorization: $CLICKUP_API_KEY" | \
  python -c "
import sys, json, os
os.environ['PYTHONUTF8']='1'
data = json.load(sys.stdin)
last = data['comments'][0]  # mais recente
text = last.get('comment_text', '')
assert '�' not in text, 'CORRUPTION DETECTED'
print('OK:', last['id'])
"
```

Se corrompeu (apesar do método correto): `DELETE /v2/comment/<comment_id>` + retry. Se persiste 2x: STOP, reportar.

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

Mentions: `@<github_handle>` da tabela §2. Se handle desconhecido: usar `gh api search/users?q=<email>` ou perguntar.

**Heredoc com `'EOF'` single-quoted** preserva `$` / backticks como literais.

## 5. Verification pre-irreversible (A5')

Se `event_type ∈ {pr.merged, deploy.success}`, ANTES de postar:

```bash
# Confirmar PR realmente merged
gh pr view <PR_NUMBER> --repo <REPO> --json state,mergedAt,reviews | \
  python -c "
import json, sys
d = json.load(sys.stdin)
assert d['state'] == 'MERGED', f'NOT MERGED: {d[\"state\"]}'
print('verified merged at', d['mergedAt'])
"
```

Se mismatch entre `payload` e estado real: STOP, reportar ao usuário. **Memory ≠ source of truth** — verificar contra o estado real antes de postar.

## 6. Templates por evento

### task.done

```
TL;DR: V1 da <feature> entregue.

Backend: PR <#NNN> ✅
Frontend: PR <#MMM> ✅
Validation: <smoke OK | product OK>

@<PO> — tudo certo. Status do task: done.
```

### pr.opened

```
PR <#NNN> aberto: <title>

Branch: <branch>
Mudanças: <X arquivos, +Y -Z>
Tests: <unit + e2e | smoke pendente>

@<reviewer> — review request. Detalhes no PR body §"O que pedir pro reviewer focar".
```

### deploy.fail

```
⚠️ Deploy fail — <service> <env>

Erro: <1 linha factual>
Logs: <link>

@<tech_lead> — escalada.
```

## 7. Idempotency

Cache local: `<repo>/.docs/notifier-idempotency.json` (gitignored).

Schema:
```json
{ "<event_id>:<channel>": <unix_ms>, ... }
```

Onde `event_id = sha1(event_type + clickup_id + pr_number)`.

Pre-post: se entrada existe e `< 24h`, log "duplicate skipped" + no-op.

## 8. Output

```
✅ Notifier — event: <event_type>
Channels:
  - ClickUp <CLICKUP_ID>: comment <comment_id> ✅ (UTF-8 verified)
  - GitHub <REPO>#<PR_NUMBER>: comment ✅
Mentions resolvidos: <N>
Verification: <state=MERGED, mergedAt=...>
```

## 9. Hard rules

- **NUNCA `curl -d` inline com UTF-8** — sempre Write tool + `--data-binary @file` + `charset=utf-8` (§3).
- **NUNCA postar credenciais** ([[feedback-never-post-secrets-to-external-systems]]) em comments.
- **NUNCA usar `notify_all: true`** em ClickUp sem autorização explícita do usuário (spam → equipe inteira).
- **Verificar `gh pr view` ANTES** de afirmar PR merged/approved (§5, regra A5').
- **Truncar body > 5000 chars** (limite ClickUp) e linkar pro PR.
- **Tabela de mention IDs** (§2) NÃO é hardcoded forever — quando user_id resolver falhar 2x, hidratar via API + atualizar.
- **Idempotency by event_id**, nunca por hash do body.

## 10. Failure modes

| Erro | O que fazer |
|---|---|
| CLICKUP_API_KEY ausente | STOP, perguntar (não auto-fetch — segredo) |
| ClickUp 401/403 | Verificar key não rotacionou; log + STOP |
| ClickUp 429 (rate limit) | Backoff 90s, retry 1x |
| Encoding check falha pós-post | DELETE comment + retry 1x; persiste → STOP |
| `gh` 401 | `gh auth status` — se logado, repo path errado |
| Mention name unresolved | Cache hit? Tentar API; falhou → STOP, perguntar |
| pr.merged event mas PR open | A5' triggered — STOP, alertar caller |
| Network timeout > 30s | Backoff + retry 1x; persiste → STOP |

## 11. Anti-patterns

- ❌ `curl -d '{"comment_text":"olá com acento"}'` — vai corromper. Sempre §3.
- ❌ Postar PR comment sem verificar PR existe via `gh pr view`.
- ❌ Hardcode `notify_all: true` — vira spam, equipe ignora.
- ❌ Mention via texto livre `"@username"` no comment_text — vira string sem tag estrutural. Use `type: tag` + `attributes.user.id`.
- ❌ Postar `deploy.success` toda hora — V1 sem digest, mas evita ruído (1x/deploy).
- ❌ Truncar erro de stack pra "ficar limpo" em deploy.fail — preserve linha 1; linkar log.

## 12. Skills consumidas

- [[clickup-api]] — referência de auth + rate limit.
- (memória) [[clickup-api-org-conventions]] — UTF-8 gotcha + tabela de mention IDs.

## 13. Skills downstream

- Nenhuma — Notifier é o último estágio do ciclo.

## 14. V2 backlog (companion spec cobre)

- WhatsApp via Evolution API (bot config)
- Slack incoming webhook (#shipped, #dev-alerts)
- Telegram bot
- Discord webhook
- Digest diário (agrega `task.done` etc — fora do path crítico)
