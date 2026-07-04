# AGENTS.md — <project_name>

Local constitution. **Inherits the agentic core** vendored from
[BGavazzi/agentic-pipeline](https://github.com/BGavazzi/agentic-pipeline)
(`.agentic-core/`, projected into `.claude/skills/` + `scripts/` by `sync-core.sh`).
This file is repo-specific and is NEVER overwritten by a core sync — edit it freely.

**Versão**: 0.1.0  ·  **Status**: <tier>  ·  **Tipo**: <one-line type>

---

## §0 Protocolo Zero — Continuidade

1. **LER** `.agents/continuity-<seuagente>.md` (criar se não existir).
2. **ALINHAR** com o "Foco Atual".
3. **ATUALIZAR** ao final da sessão.

```yaml
multi_agent: false
sdd_kit_path: docs/SDD_KIT.md
function_catalog: .docs/function-catalog.md
route_map: .docs/ROUTE_BEHAVIOR_MAP.md
task_dir: .docs/tasks
clickup_list_id: <opcional, se sincronizado>
agentic_core: .agentic-core      # vendored pipeline; sync via .agentic-core/sync-core.sh
```

---

## §1 Identidade e Escopo

**Nome**: <project_name>
**Mantido por**: <maintainer>
**Tipo**: <type>
**Tier**: <prototype | active | canonical>

### 1.1 Stack
| Camada | Tecnologia |
|---|---|
| <ex: Runtime> | <ex: FastAPI + Docker> |

---

## §2 Hard Rules

🔒 **Nunca delete** arquivos. `mv` pra `.archive/`.
🔒 **Nunca commit NEM poste segredos.** `.env` em `.gitignore`. Nunca escrever credencial em sistema externo (ClickUp/GitHub/Slack/SaaS), nem a pedido — pausar e propor alternativa.
🔒 **Core é read-only.** Skills sob `.claude/skills/` projetadas de `.agentic-core/` não se
edita aqui — corrige upstream no guidelines_IA e re-sincroniza. Skills locais usam nome distinto.
🔒 **PR é unidade de merge limpa.** Nunca reciclar PR errado — PR novo + fecha o velho. Conflito = rebase na base (`integration`/`main`).
🔒 **"Keep going" ≠ inventar escopo.** Em modo autônomo (dispatcher/loop), só pedido explícito; não derivar de backlog/spec velho sem confirmação per-feature.

**Convenções org-wide** (no agentic-pipeline): [`git-pr-workflow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/git-pr-workflow.md) · [`engineering-defaults.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/engineering-defaults.md) · [`frontend-screen-flow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/frontend-screen-flow.md) · [`agent-conduct.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/agent-conduct.md)

---

## §3 Lei de Fechamento de Tarefa

Antes de marcar task `done`, todos atualizados (`validate_closure.py` checa):

| # | Artefato | Quando |
|---|---|---|
| 1 | `CHANGELOG.md` | Sempre |
| 2 | `<function_catalog>` | Mudança de assinatura |
| 3 | `<sdd_kit_path>` | Nova decisão Dxx |
| 4 | `README.md` | Mudança visível ao user |
| 5 | `.agents/continuity-<agente>.md` | Sempre |
| 6 | Testes passando | Sempre |
| 7 | `<route_map>` | Rota/handler/modelo alterado |
| 8 | **PR aprovado** | Task que gera código |

`[N/A]` com justificativa de 1 linha se não aplica.
🔒 **Task só fecha com PR aprovada** — task com código só vira `done`/vai pra `completed/` com o PR aprovado; PR aberto não basta (fica `in_progress` em review até aprovação humana). O dispatcher NÃO fecha a task ao abrir o PR.

---

## §4 Tarefas

### 4.1 Naming (org-wide)
`<task_dir>/NNNN-tipo-slug.md` — `NNNN` 4 dígitos; `tipo`: feat/fix/refactor/docs/chore/audit/proposal/infra/test.
`validate_task.py` valida o frontmatter (F1–F12).

### 4.2 Frontmatter mínimo
```yaml
---
status: todo | in_progress | done
priority: P0 | P1 | P2
type: feat | fix | ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
clickup_id: <id|null>
parent: null
blocks: []
blocked_by: []
---
```

### 4.3 Estado
- Aberta: `<task_dir>/NNNN-...md` · Concluída: `<task_dir>/completed/NNNN-...md` (mover ao fechar) · Planning: `<task_dir>/planning/`

### 4.4 Skills herdadas do core

| Skill | Para quê |
|---|---|
| `grill-me` | Entrevistar o autor da task até a spec ficar acionável |
| `codebase-grounding` | Mapear o repo antes de mexer |
| `builder` | Executar uma task em código |
| `tester` | Validar §Condições de Saída (modo prototype) |
| `librarian` | Lei de Fechamento §3 |
| `notifier` | Postar resumo em ClickUp + GitHub |
| `dispatcher` | Orquestrar a fila `<task_dir>` (TOS-aware; só em sessão interativa) |
| `codebase-audit` | Checks read-only de saúde do repo |

---

## §5 Estilo

ClickUp comments: caveman/terse, TL;DR acima de 200c. Ver convenção no guidelines_IA.
