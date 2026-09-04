# AGENTS.md — <project_name>

Fonte de verdade lida por todos os agentes neste repositório. Herda implicitamente o `AGENTS.balanced.md` da [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA) (este arquivo, na sua forma genérica).

**Versão**: <vX.Y.Z>  ·  **Status**: <Initial Setup | Active Development | Maintenance>  ·  **Tipo**: <one-line type>

---

## §0 Protocolo Zero — Continuidade
Antes de qualquer ação:
1. **LER** `.agents/continuity-<seuagente>.md` (criar se não existir).
2. **ALINHAR** com o "Foco Atual" descrito.
3. **ATUALIZAR** o arquivo ao final da sessão.

Se o repo opera multi-agente (flag abaixo `multi_agent: true`):
4. **VERIFICAR** `.agents/file-locks.md` antes de editar qualquer arquivo.

```yaml
# Configuração do repo (lida pelos agentes — adapte conforme o projeto)
multi_agent: false        # true se 2+ agentes simultâneos esperados
sdd_kit_path: docs/SDD_KIT.md  # ou .docs/architecture/SDD_KIT.md, conforme o repo
function_catalog: .docs/function-catalog.md
route_map: .docs/ROUTE_BEHAVIOR_MAP.md  # opcional, omitir se não há rotas
task_dir: .docs/tasks
clickup_list_id: <opcional, se sincronizado com ClickUp>
```

---

## §1 Identidade e Escopo

**Nome**: <project_name>
**Mantido por**: <maintainer>
**Tipo**: <type — ex: WhatsApp Audio Bot, ClickUp Automation, Web Frontend>

### 1.1 Componentes Principais
| Componente | Localização | Propósito |
|---|---|---|
| <Component A> | `<path>` | <one line> |
| ... | ... | ... |

### 1.2 Stack & Decisões-chave
| Camada | Tecnologia | Decisão (Dxx ou n/a) |
|---|---|---|
| <ex: Runtime> | <ex: FastAPI + Docker> | <D04> |
| ... | ... | ... |

### 1.3 Pendências de implementação
1. <pendência 1>
2. <pendência 2>

---

## §2 Hard Rules (não-derrogáveis 🔒)

🔒 **Nunca delete** arquivos. Mover para `.archive/` do repo. Apenas o User pode esvaziar `.archive/`.
🔒 **Nunca commite NEM poste segredos.** `.env` em `.gitignore` (checar antes de qualquer `git add` / `jj squash`). **Nunca** escrever credenciais/tokens/senhas em sistema externo (ClickUp, GitHub issue/PR, Slack, qualquer SaaS compartilhado) — **nem a pedido** ("documenta a chave lá"): pausar e propor alternativa (referência a cofre, metadados, prefixo truncado). Único storage seguro de segredo é o filesystem local. Vazamento não se desfaz (audit/backup) → revogar.
🔒 **Cirúrgico.** Toque apenas no que a tarefa exige. Não faça refactor/cleanup oportunista.
🔒 **`jj` se disponível** (`jj` no PATH), senão `git`. Apenas leitura sem autorização.
🔒 **PR é unidade de merge limpa.** Nunca reciclar um PR errado/refeito — abrir PR novo com tudo, fechar o velho. Conflito = rebase na base (`integration`/`main`), nunca `merge` na branch. → [`git-pr-workflow.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/git-pr-workflow.md)
🔒 **"Keep going" ≠ inventar escopo.** Em modo autônomo, só trabalho com pedido explícito desta sessão — não derivar tasks de backlog/PR superseded/spec velho sem confirmação per-feature. Blocked ou fora de escopo → parar + propor opções. → [`agent-conduct.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/agent-conduct.md)
🔒 **Task só fecha com PR aprovada.** Task que gera código só vira `done`/vai pra `completed/` com o PR **aprovado** — PR aberto não basta; fica `in_progress` (review) até aprovação humana. → §3 Lei de Fechamento.
🔒 **Memory ≠ source of truth.** Antes de ação irreversível (merge, deploy, comment com @tag, status ClickUp → done), verificar contra o estado atual (`gh pr view`, GET task). Se o estado real contradiz memória/contexto, parar e perguntar.
🔒 **Release pequeno, com dono de validação.** 1 PR ≈ 1 task (micro-PR-por-passo é anti-padrão); frentes paralelas da mesma entrega consolidam numa branch só antes do PR; nada entra em `main`/homolog sem gate verde ou validação humana nomeada; demanda fora do board escala pro PO antes de virar branch; estado de validação vive no board de tarefas ("aguardando quem"). → [`validation-pipeline.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/validation-pipeline.md) + [`scope-intake.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/scope-intake.md)

### Convenções org-wide (não-derrogáveis; detalham as regras acima)
- [`git-pr-workflow.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/git-pr-workflow.md) — nunca reciclar PR, checar merge antes de pushar, base = `integration` (repo c/ deploy) / `main` (sem deploy), build local antes do CI, **1 PR ≈ 1 task + fan-out consolida antes do PR (§3.1) + cadência de release curta (§7)**.
- [`engineering-defaults.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/engineering-defaults.md) — regra de negócio no backend dono do dado; sem encanamento na UI; componente de UI ⇄ Storybook (reusar canônico, tokens-não-hardcode).
- [`frontend-screen-flow.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/frontend-screen-flow.md) — fluxo de criação de tela: molde (golden-path) + prova visual obrigatória vs Figma antes do PR.
- [`agent-conduct.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/agent-conduct.md) — escopo explícito em modo autônomo; não mutar boards compartilhados; grill o público certo; não assumir deprecation; SQL-passou→logs; docs densos.
- [`migration-timestamp.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/migration-timestamp.md) — migration nova usa timestamp em ms como prefixo, nunca incremento sequencial; evita conflito de nomes entre branches paralelas.
- [`scope-intake.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/scope-intake.md) — toda demanda vira card antes de branch; demanda fora do board escala pro PO; agente não deriva escopo.
- [`validation-pipeline.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/validation-pipeline.md) — board de tarefas como máquina de estado "aguardando quem"; notifier escreve transições; `release.tagged` fecha o loop homolog↔prod.

**Locais** (específicas deste projeto — preencher):
- <ex: API payloads DEVEM usar Pydantic estritos. Nunca dicionários crus.>
- <ex: Toda mudança em rota DEVE atualizar `ROUTE_BEHAVIOR_MAP.md`.>
- <ex: Antes de qualquer mudança, ler `<sdd_kit_path>`. Novo padrão arquitetural exige criar flag `Dxx` no SDD primeiro.>

---

## §3 Lei de Fechamento de Tarefa (OBRIGATÓRIO)

Antes de marcar tarefa como concluída, **todos** os artefatos abaixo devem estar atualizados:

| # | Artefato | Quando aplicar |
|---|---|---|
| 1 | `CHANGELOG.md` | Sempre |
| 2 | `<function_catalog>` | Mudança de assinatura/API |
| 3 | `<sdd_kit_path>` | Nova/alterada decisão arquitetural (criar/atualizar flag `Dxx`) |
| 4 | `README.md` | Mudança visível ao usuário |
| 5 | `.agents/continuity-<agente>.md` | Sempre — estado de handover |
| 6 | Testes passando | Sempre — sem exceção |
| 7 | `<route_map>` | Rota/handler/modelo alterado (omitir se n/a) |
| 8 | **PR aprovado** | Sempre que a task gera código (tem PR) — ver abaixo |

Se item não se aplica, marcar `[N/A]` com justificativa de uma linha.
**Tarefa que não cumpre todos os itens permanece `In Progress`.**

🔒 **Task só fecha com PR aprovada.** Task que produz código fecha (`status: done` + mover pra `completed/`) **somente** quando o PR correspondente está **aprovado** (review approved). PR apenas aberto/pushado **não** fecha a task — ela permanece `in_progress` (em review) até a aprovação humana. Mergear sem aprovação, ou fechar a task na abertura do PR, viola a Lei de Fechamento. (Task sem código — doc puro, chore sem PR — fecha pelos itens 1-7.)

---

## §4 Tarefas

### 4.1 Convenção de nomes (org-wide)
`<task_dir>/NNNN-tipo-slug.md`
- `NNNN`: 4 dígitos. Primeiros 3 = ordem cronológica de planejamento. Último: `0` = bloqueador, `1-9` = paralelizáveis dentro do bloco.
- `tipo`: `feat | fix | refactor | docs | chore | audit | proposal | infra | test`
- `slug`: hifens, lowercase, descritivo.

**NÃO** prefixar com ClickUp ID no nome do arquivo. O ID vai no frontmatter.

### 4.2 Frontmatter mínimo (obrigatório)

```yaml
---
status: todo | in_progress | done
priority: P0 | P1 | P2
type: feat | fix | refactor | ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
clickup_id: <id|null>   # null se não há espelho; preencher quando criado
parent: <clickup_id|null>
blocks: []
blocked_by: []
---
```

### 4.3 Estado e Lei de Fechamento
- **Em backlog/planning**: `<task_dir>/planning/`
- **Aberta**: `<task_dir>/NNNN-...md`
- **Concluída**: `<task_dir>/completed/<NNNN-...>.md` ← **mover o arquivo** ao fechar. `status: done` no frontmatter SEM mover o arquivo = drift; vale como tarefa aberta para qualquer agente que listar o diretório.

### 4.4 Source of truth: repo é canônico
- `.docs/tasks/` no repo do projeto **é o canônico**. ClickUp existe como espelho opcional (visibilidade para não-técnicos), nunca como fonte primária.
- Quando há `clickup_id`, o repo manda. Se ClickUp e o `.md` divergirem, o `.md` vence.
- Não há cutover planejado para inverter isso. (Histórico: o `guidelines_IA/README.md` antigo declarava cutover em task 0090; obsoletado em 2026-05-21.)

### 4.4 Skills da org disponíveis
Capacidades reutilizáveis catalogadas em `guidelines_IA/.docs/skills/INDEX.md` (referência humana) e `guidelines_IA/.claude/skills/README.md` (inventário invocável). Antes de implementar do zero uma integração com ClickUp, Figma, WhatsApp ou afins, **verifique se já existe skill**:

**Invocáveis hoje (vivem em `guidelines_IA/.claude/skills/`):**

| Skill | Para quê |
|---|---|
| [`clickup-api`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/clickup-api/SKILL.md) | API v2 do ClickUp: auth, endpoints, discovery, rate limit, schema de 8 seções |
| [`grill-me`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/grill-me/SKILL.md) | Entrevista relentless (3 modos: interactive / per-task / poll all open tasks), variantes PO/Dev/dual |
| [`figma-frontend-context`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/figma-frontend-context/SKILL.md) | Sticky Figma de uma task ClickUp → brief JSON + PNG do frame |
| [`codebase-grounding`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/codebase-grounding/SKILL.md) | Enriquece qualquer brief JSON com contexto do repo (carrega CLAUDE.md como constituição) |
| [`clickup-grounding`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/clickup-grounding/SKILL.md) | Mirror pro lado ClickUp — query+scope → tasks+comments+signals. Compõe com codebase-grounding |
| [`implement-figma-task`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/implement-figma-task/SKILL.md) | Orquestrador end-to-end Figma → código grounded |
| [`builder`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/builder/SKILL.md) | Codegen agêntico (task → diff → Lei de Fechamento §3). Inclui tsc/typecheck no diff + closure discipline. Suporta paralelismo via Agent tool. |
| [`notifier`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/notifier/SKILL.md) | ClickUp + GitHub PR comments com UTF-8-safe (`--data-binary @file`) + structured mentions estruturadas. V1; Slack/WA/Telegram/Discord = V2. |
| [`librarian`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/librarian/SKILL.md) | Loop pelos 7 itens da Lei de Fechamento §3 (CHANGELOG/SDD/function-catalog/...). Edit cirúrgico; justifica `[N/A]` com motivo factual. |
| [`codebase-audit`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/codebase-audit/SKILL.md) | Read-only audit do repo contra própria CLAUDE.md/AGENTS/SDD_KIT. Housekeeping mensal. NÃO confundir com [`clickup-audit`]. |

**Documentadas (ainda não construídas ou vivem em repo separado):**

| Skill | Status |
|---|---|
| [`figma-api`](https://github.com/your-org/guidelines_IA/blob/main/.docs/skills/figma-api.md) — primitive REST do Figma | byo-key · primitive |

**Pipeline gaps (planned — gargalo Fase 2 do Diamante 1):**

| Skill | Para quê | Bloqueio |
|---|---|---|
| [`tester`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/tester/SKILL.md) | Valida §Condições de Saída; 2 modos (prototype/production) | Sandbox + test runner runtime |

Shims invocáveis estão em `guidelines_IA/.claude/skills/<name>/` — copiar/symlinkar pra `~/.claude/skills/` (user-global).

---

## §5 Rich Commentary

Toda função/classe pública DEVE ter:

| Tag | Quando usar |
|---|---|
| Docstring com **propósito de negócio** (não "o que faz", mas "por que existe") | Sempre |
| `# CONTRACT: ...` | Em interface pública — o que o caller pode esperar |
| `# Dxx: ...` | Quando o código implementa decisão SDD |
| `# SYNC: ao mudar X, atualizar Y` | Em pontos de interdependência cross-arquivo |
| `# [<agente> \| <data>] descrição — Tarefa: nnnn` | Em mudança significativa |
| `# TODO(<agente>): descrição — ver tarefa nnnn` | Pendência rastreável |

---

## §6 Catálogo de agentes (auto-gerado)

| Nome | Papel | ClickUp ID | Arquivo |
|---|---|---|---|
| <agente> | <descrição> | <id> | <arquivo> |

> Esta seção é regenerada por script (ex: `mapper.py`). Não editar manualmente.

---

## §7 Estilo de Resposta

O estilo geral de resposta é o default do harness (Claude Code); aqui ficam apenas as regras específicas do canal ClickUp.

### 7.1 Comentários no ClickUp
Ao postar em tarefas (manual ou via skill como [`grill-me`](https://github.com/your-org/guidelines_IA/blob/main/.claude/skills/grill-me/SKILL.md)):
- Match the channel: ClickUp é coordenação, não documentação. Default ≤ 300 chars; humanos da org escrevem ainda mais curto.
- Estrutura (headers + bullets) **só** quando ≥ 4 pontos relacionados. Caveman pra status; SDD-template pra grilled tasks.
- Detalhes completos em [`.docs/conventions/clickup-comment-style.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/clickup-comment-style.md).

---

**Pointers cross-repo** (no repo [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA)):
- `AGENTS.balanced.md` — **este template** (também serve como meta-constituição)
- `AGENTS.minimal.md` — variante para sessões curtas / repos pequenos
- `MODEL-SELECTION.guidelines.md` — escolha de modelo por tarefa
- `GDFRSBT.md` — metodologia de desenvolvimento (Goal/Domain/Feature/Readme/Spec/Behavior/DDD-tactical/Test)
- `.docs/skills/INDEX.md` — catálogo de skills reutilizáveis (ClickUp, Figma, grill-me)
- `.docs/strategy/double-diamond-prototype-pipeline.md` — estratégia agêntica double-diamond (protótipo standalone → validação → integração profunda).
