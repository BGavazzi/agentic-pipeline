---
name: codebase-audit
description: Audita um repo (read-only) contra suas próprias regras declaradas em CLAUDE.md/AGENTS.md/SDD_KIT.md. Produz report de violações em 10 dimensões (endpoint docs faltando, swagger missing, route não em map, Dxx órfão, migration sem rollback, entity sem migration, test orphan, route sem teste, continuity stale, claude.md self-violation). Triggers - "audita o repo", "scan de drift", "checa violações de CLAUDE.md", "housekeeping mensal". STATUS - ready (V1 = 5 checks core; outros 5 = backlog).
tools: Read, Bash, Glob, Grep, Write
---

# Codebase Audit

**Runtime: sessão Claude Code aberta. Read-only.** Spec humana: `.docs/skills/codebase-audit.md`.

**NÃO confundir com [[clickup-audit]]** (workspace ClickUp). Este audita um **repo** contra a constituição declarada nele mesmo.

V1 implementa 5 checks core:
1. `endpoint_doc_missing`
2. `route_not_in_map`
3. `sdd_decision_orphan`
4. `claude_md_self_violation`
5. `continuity_stale`

V2 backlog (specificado mas não V1): swagger_decorators_missing, migration_no_rollback, entity_no_migration, test_orphan, route_no_test.

## 1. Inputs

- `repo_path`: working tree (obrigatório)
- `checks`: opcional — subset por nome (default: todos V1)
- `severity_floor`: `info | warn | error` (default: `warn`)
- `since`: opcional — só audita arquivos modificados após ISO date

## 2. Preconditions

```bash
test -d "$repo_path/.git" || STOP "repo_path não é repo git"
ls "$repo_path/CLAUDE.md" "$repo_path/AGENTS.md" "$repo_path/AGENTS.balanced.md" 2>/dev/null | \
  head -1 || STOP "repo sem constituição declarada — audit no-op"
mkdir -p "$repo_path/.docs/audit-reports/"
```

## 3. Loop principal

```
1. Load constitution (mesmo flow do Step 0 codebase-grounding):
   - Read CLAUDE.md (se existe)
   - Read AGENTS.md / AGENTS.balanced.md (se existe)
   - Read SDD_KIT.md (se existe)
   - Read ROUTE_BEHAVIOR_MAP.md (se existe)
   - Capturar hard_rules (frases must/never/always/sempre/nunca/obrigatório)

2. Para cada check em `checks`:
   a. Aplicar regra ao codebase (§4 abaixo)
   b. Listar violations [(file, line, endpoint?, severity)]
   c. Filtrar por severity_floor

3. Write report:
   - Markdown: <repo>/.docs/audit-reports/<YYYY-MM-DD>-codebase-audit.md
   - JSON: <repo>/.docs/audit-reports/<YYYY-MM-DD>-codebase-audit.json

4. Output summary ao usuário (§5 abaixo).

5. NÃO criar tasks. Humano triagem decide.
```

## 4. Checks — implementação

### 4.1. endpoint_doc_missing

Aplica-se quando constituição tem regra tipo "todo endpoint exige .bru" ou "todo endpoint precisa de docs em docs/api/...".

```bash
# Encontrar handlers HTTP (NestJS pattern)
grep -rn -E "@(Get|Post|Put|Patch|Delete)\(" --include="*.ts" "$repo_path/src/"
# → lista de arquivos:linha → endpoint paths

# Encontrar .bru files
find "$repo_path" -name "*.bru" -type f | xargs grep -l "post:\|get:\|put:\|patch:\|delete:"
# → set de endpoints documentados

# Diff: handlers SEM .bru correspondente
```

Severity: `error` (regra "must/exige").

### 4.2. route_not_in_map

Se `ROUTE_BEHAVIOR_MAP.md` existe: cada handler deveria ter entry.

```bash
# Set de rotas no map
grep -E "^- (GET|POST|PUT|PATCH|DELETE) " "$repo_path/ROUTE_BEHAVIOR_MAP.md"
# Set de rotas no código (do check anterior)
# Diff
```

Severity: `warn` (mapa é honra-prática, não bloqueante).

### 4.3. sdd_decision_orphan

`Dxx` references em código sem entry no SDD_KIT.md.

```bash
# Capturar todos `// D01`, `// D02`, etc no código
grep -rn -E "//\s*D[0-9]+|#\s*D[0-9]+" --include="*.ts" --include="*.py" --include="*.js" "$repo_path/src/"

# Capturar D's documentados no SDD_KIT
grep -E "^##?\s+D[0-9]+" "$repo_path/SDD_KIT.md" | sed -E 's/.*D([0-9]+).*/D\1/'

# Diff: códigos sem entry
```

Severity: `warn`.

### 4.4. claude_md_self_violation

CLAUDE.md cita arquivo/path/diretório que não existe.

```bash
# Extrair refs do CLAUDE.md (paths que começam com src/, docs/, .docs/, etc)
grep -oE "\`[a-zA-Z0-9_./\-]+\.(ts|tsx|js|jsx|md|py|sql|yaml|yml|json|bru)\`" "$repo_path/CLAUDE.md"

# Para cada path: test -e (relativo ao repo_path)
# Listar broken refs
```

Severity: `error` (rules apontando pra vazio = regras quebradas).

### 4.5. continuity_stale

`.agents/continuity-*.md` com mtime > 90d se houver atividade recente na branch.

```bash
# Listar continuity files
ls -la "$repo_path/.agents/continuity-"*.md 2>/dev/null

# Para cada: mtime + comparar com último commit do repo
last_commit_ts=$(git -C "$repo_path" log -1 --format=%ct)
for f in continuity-*.md; do
  mtime=$(stat -c %Y "$f")
  delta_days=$(( (last_commit_ts - mtime) / 86400 ))
  if [ "$delta_days" -gt 90 ]; then echo "STALE $f $delta_days days"; fi
done
```

Severity: `info` (humano decide se mantém).

## 5. Output

```
✅ Audit — <repo>
Constitution: CLAUDE.md, AGENTS.balanced.md, SDD_KIT.md
Checks: 5/5 V1

Violations:
  error: <N>
  warn:  <M>
  info:  <K>

Top 3 (error):
  1. endpoint_doc_missing — POST /notifications/register-token (src/notifications/notificationController.ts:42)
  2. endpoint_doc_missing — POST /notifications/test-notification (src/notifications/notificationController.ts:68)
  3. claude_md_self_violation — `docs/api/Notifications/` (CLAUDE.md §1, target dir não existe)

Report: <repo>/.docs/audit-reports/2026-05-28-codebase-audit.md
JSON:   <repo>/.docs/audit-reports/2026-05-28-codebase-audit.json

Próximo: humano triagem → criar tasks chore/<NNNN> pro que vale a pena fixar.
```

## 6. Report format (markdown)

```markdown
# Codebase Audit — <repo>

**Data**: <YYYY-MM-DD>
**Constitution sources**: CLAUDE.md, AGENTS.balanced.md
**Checks rodados**: 5
**Severity floor**: warn

## Sumário

| Severity | Count |
|---|---|
| error | 2 |
| warn | 5 |
| info | 10 |

## Violations — error

### endpoint_doc_missing (regra: CLAUDE.md §1)

> "Every HTTP endpoint requires a .bru file under docs/api/Blue Events API/"

- `src/notifications/notificationController.ts:42` — POST /notifications/register-token
- `src/notifications/notificationController.ts:68` — POST /notifications/test-notification

**Suggested action**: criar .bru files OU documentar em SDD_KIT como exceção justificada.

### claude_md_self_violation

- `CLAUDE.md` linha 23: refer `docs/api/Notifications/` — diretório não existe

## Violations — warn

[...]
```

## 7. Hard rules

- **Read-only.** Nenhum arquivo do repo audit-alvo é modificado fora de `.docs/audit-reports/`.
- **Não cria tasks.** Humano triagem decide.
- **Não auto-fix.** Mesmo se violação é trivial (faltou .bru), audit não cria — pra forçar humano ver agregado.
- **Não inventa regras.** Se CLAUDE.md não cita `.bru`, audit não checa `.bru`.
- **Performance**: cap em 60s. Excedeu → particionar por path + warn.

## 8. Failure modes

| Erro | O que fazer |
|---|---|
| Repo sem constituição | No-op + log "repo sem CLAUDE.md/AGENTS.md — audit incompleta" |
| Glob retorna 10k+ matches | Particionar por subdir, warn no report |
| Check específico crasha | Skip, log, continuar outros |
| Audit interrompido | Salvar parcial com flag `"incomplete": true` no JSON |
| .docs/audit-reports/ não existe | Criar (única exceção ao read-only) |
| Constituição contraditória detectada | Report separado `<date>-constitution-conflicts.md` |

## 9. Anti-patterns

- ❌ Auto-criar tasks ClickUp pra cada violação (humano triagem é parte do design).
- ❌ Edit/Write em arquivos do repo audit-alvo fora de `.docs/audit-reports/`.
- ❌ Reportar "boas práticas universais" não declaradas (use TS, use ESLint).
- ❌ Rodar como gate no ciclo crítico Builder→Tester→Librarian (audit é fora do ciclo).
- ❌ Severity inflada — toda regra `error` vira ruído.
- ❌ Audit chamado em loop pelo ciclo — 1x mensal por repo é o pattern.

## 10. Skills relacionadas

- [[codebase-grounding]] — reusa Step 0 (constitution loading).
- [[librarian]] — escopo NNNN; este escopo agregado. Complementares.
- [[clickup-audit]] — workspace, não repo.
