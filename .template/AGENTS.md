# AGENTS.md — <project_name> (prototype)

Constituição local. Herda de `AGENTS.balanced.md` neste repo
([BGavazzi/agentic-pipeline](https://github.com/BGavazzi/agentic-pipeline)).

**Versão**: 0.1.0  ·  **Status**: Diamante 1 — prototype  ·  **Tipo**: <one-line type>

---

## §0 Protocolo Zero — Continuidade

1. **LER** `.agents/continuity-<seuagente>.md` (criar se não existir).
2. **ALINHAR** com o "Foco Atual".
3. **ATUALIZAR** ao final da sessão.

```yaml
multi_agent: false          # Diamante 1 default: 1 builder por vez. Mudar pra true só após validação.
sdd_kit_path: docs/SDD_KIT.md
function_catalog: .docs/function-catalog.md
route_map: .docs/ROUTE_BEHAVIOR_MAP.md
task_dir: .docs/tasks
clickup_list_id: <opcional, se sincronizado>
```

---

## §1 Identidade e Escopo

**Nome**: <project_name>
**Mantido por**: <maintainer>
**Tipo**: <type — ex: WhatsApp Audio Bot, ClickUp Automation, Web Frontend>
**Tier**: prototype (Diamante 1)

### 1.1 Stack
| Camada | Tecnologia |
|---|---|
| <ex: Runtime> | <ex: FastAPI + Docker> |
| ... | ... |

### 1.2 Mock layers (Diamante 1 — substituir na Diamante 2)
- Auth: mock local (auth canônica substituirá)
- Storage: SQLite local OU in-memory (storage canônico vem na D2)
- LLM: chave dev (rotation/RBAC vem na D2)

---

## §2 Hard Rules

🔒 **Nunca delete** arquivos. `mv` pra `.archive/`.
🔒 **Nunca commit NEM poste segredos.** `.env` em `.gitignore`. Nunca escrever credencial em sistema externo, nem a pedido — pausar e propor alternativa.
🔒 **PR é unidade de merge limpa.** Nunca reciclar PR errado — PR novo + fecha o velho. Conflito = rebase na base (`integration`/`main`).
🔒 **"Keep going" ≠ inventar escopo.** Em modo autônomo, só pedido explícito desta sessão; não derivar de backlog/spec velho.

**Convenções compartilhadas** (neste repo): [`git-pr-workflow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/git-pr-workflow.md) · [`engineering-defaults.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/engineering-defaults.md) · [`frontend-screen-flow.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/frontend-screen-flow.md) · [`agent-conduct.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/agent-conduct.md) · [`scope-intake.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/scope-intake.md)

---

## §3 Lei de Fechamento de Tarefa

Antes de marcar task como `done`, todos atualizados:

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
🔒 **Task só fecha com PR aprovada** — task com código só vira `done`/vai pra `completed/` com o PR aprovado; PR aberto não basta (fica `in_progress` em review até aprovação humana).

---

## §4 Tarefas

### 4.1 Naming (convenção compartilhada)
`<task_dir>/NNNN-tipo-slug.md`
- `NNNN`: 4 dígitos
- `tipo`: feat/fix/refactor/docs/chore/audit/proposal/infra/test

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
- Aberta: `<task_dir>/NNNN-...md`
- Concluída: `<task_dir>/completed/NNNN-...md` ← mover arquivo ao fechar
- Planning: `<task_dir>/planning/`

### 4.4 Skills disponíveis (vendoradas via `core_sync.py`)

| Skill | Para quê |
|---|---|
| `clickup-api` | CRUD em tasks/comments/tags |
| `grill-me` | Entrevistar autor da task até spec ficar acionável |
| `codebase-grounding` | Mapear repo antes de mexer |
| `builder` | Executar uma task em código |
| `tester` | Validar §Condições de Saída (modo prototype) |
| `notifier` | Postar resumo em chat |

---

## §5 Estilo

Estilo de resposta geral é default do harness (terso, sem postâmbulo). Específico daqui:
ClickUp comments — ver [`clickup-comment-style.md`](https://github.com/BGavazzi/agentic-pipeline/blob/main/.docs/conventions/clickup-comment-style.md) neste repo.

---

## §6 Promoção pra Diamante 2

Quando atingir critério de saída (README + docker compose + PRD + happy path + tests + preview link), agendar reunião com o decisor sênior/PO. Decisão é humana, fora do código.

Se **Go**: repo migra pro namespace canônico; task pai criada; senior tech lead atribuído; expectativas de §1.2 mock layers viram dívida explícita.

Se **No-go**: repo vai pro `.archive/`. Retro em 1 página: o que aprendeu, o que mudou na hipótese.
