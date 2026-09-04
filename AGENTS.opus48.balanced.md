# AGENTS.md — <project_name> (variante Opus 4.8)

Fonte de verdade lida por todos os agentes neste repositório. Herda implicitamente o `AGENTS.balanced.md` da [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA).

**Versão**: <vX.Y.Z>  ·  **Status**: <Initial Setup | Active Development | Maintenance>  ·  **Tipo**: <one-line type>

> **Nota de proveniência (migração 2026-09).** Este arquivo nomeia e descreve o
> harness em termos do Opus 4.8 (a geração de modelo corrente quando foi
> escrito) — mantido como está, sem atualizar as referências de modelo, porque
> o nome do arquivo em si já é um artefato versionado (mesmo padrão de
> `.archive/agents-variants-pre-opus48/`). Antes de usar como variante ativa
> num repo hoje, confira se o corte "o que o harness já cumpre nativamente"
> ainda reflete a geração de modelo atual — o princípio por trás do corte
> (ver `AGENTS.assessment.md`) continua válido mesmo que os nomes não.

> **Por que esta variante existe.** Igual ao `AGENTS.balanced.md`, mas com as regras que o harness do Claude Code (Opus 4.8) já cumpre nativamente **removidas** — elas só gastavam contexto. O que sobrou é o que o modelo **não consegue inferir**: dados do projeto, regras invertidas, e protocolos com ordem/side-effects. Detalhe do corte em [`AGENTS.assessment.md`](AGENTS.assessment.md) (pass Opus 4.8).
>
> **Coberto pelo harness — NÃO repetido abaixo** (não é esquecimento): nunca commitar/push sem autorização explícita; autorização não vale para a operação seguinte; verificar estado real antes de ação irreversível; respostas tersas sem postâmbulo; não comentar o óbvio; referências de arquivo clicáveis; reportar falhas com fidelidade.

---

## §0 Protocolo Zero — Continuidade
Antes de qualquer ação:
1. **LER** `.agents/continuity-<seuagente>.md` (criar se não existir).
2. **ALINHAR** com o "Foco Atual" descrito.
3. **ATUALIZAR** o arquivo ao final da sessão.

Se o repo opera multi-agente (`multi_agent: true` abaixo):
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

Apenas regras **não-deriváveis** do código ou do harness. As natively-handled (commit/push, memory-vs-estado, autorização não-transitiva) vivem no harness — ver nota do cabeçalho.

🔒 **Nunca delete** arquivos. Mover para `.archive/` do repo. Apenas o User pode esvaziar `.archive/`. *(Regra invertida — o default do harness é só "olhe antes de apagar"; o `.archive/` é política deste projeto.)*
🔒 **Nunca commite segredos.** `.env` em `.gitignore`. Verificar antes de qualquer `git add` / `jj squash`.
🔒 **Cirúrgico.** Toque apenas no que a tarefa exige. Não faça refactor/cleanup oportunista.
🔒 **`jj` se disponível** (`<path>/bin\jj.exe`), senão `git`. Apenas leitura sem autorização.
🔒 **Estado ClickUp irreversível** (status → done, comment com @tag): além do "verifique antes" do harness, fazer `GET` da task e confirmar contra o frontmatter do `.md` canônico. (Lição: ciclo 1 gap G-08.)

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

Se item não se aplica, marcar `[N/A]` com justificativa de uma linha.
**Tarefa que não cumpre todos os itens permanece `In Progress`.**

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

### 4.5 Skills da org disponíveis
Antes de implementar do zero uma integração com ClickUp, Figma, WhatsApp ou afins, **verifique se já existe skill**. Inventário invocável em `guidelines_IA/.claude/skills/README.md`; referência humana em `guidelines_IA/.docs/skills/INDEX.md`.

**Invocáveis hoje** (`guidelines_IA/.claude/skills/`): `clickup-api`, `grill-me`, `figma-frontend-context`, `codebase-grounding`, `clickup-grounding`, `implement-figma-task`, `clickup-audit`.
**Documentadas / planned**: `whatsapp-clickup` (ready, vive em `<your-bot-repo>/`), `figma-api`, `builder`, `tester`, `notifier`.

Shims invocáveis: copiar/symlinkar de `guidelines_IA/.claude/skills/<name>/` pra `~/.claude/skills/` (user-global).

---

## §5 Rich Commentary

Tags de comentário — não-deriváveis, mantidas. (O "não comente o óbvio / não duplique type hint" é default do harness e foi removido.)

| Tag | Quando usar |
|---|---|
| Docstring com **propósito de negócio** ("por que existe", não "o que faz") | Sempre, em função/classe pública |
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

## §7 Comentários no ClickUp (canal-específico)

O harness já cobre estilo de resposta geral (terso, sem postâmbulo). O que **não** é default é o tom do canal ClickUp:
- Match the channel: ClickUp é coordenação, não documentação. Default ≤ 300 chars; humanos da org escrevem ainda mais curto.
- Estrutura (headers + bullets) **só** quando ≥ 4 pontos relacionados. Caveman pra status; SDD-template pra grilled tasks.
- Detalhes completos em [`.docs/conventions/clickup-comment-style.md`](https://github.com/your-org/guidelines_IA/blob/main/.docs/conventions/clickup-comment-style.md).

---

**Pointers cross-repo** (no repo [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA)):
- `AGENTS.balanced.md` — template genérico completo (meta-constituição). Esta variante é o subset Opus 4.8.
- `AGENTS.minimal.md` — variante para sessões curtas / repos pequenos.
- `MODEL-SELECTION.guidelines.md` — escolha de modelo por tarefa (Opus 4.8 / Sonnet 4.6 / Haiku 4.5).
- `GDFRSBT.md` — metodologia de desenvolvimento (Goal/Domain/Feature/Readme/Spec/Behavior/DDD-tactical/Test).
- `.docs/architecture/reverse-analysis/INDEX.md` — SDD reverso dos módulos canônicos (gitignored; específico do projeto original).
- `.docs/strategy/double-diamond-prototype-pipeline.md` — estratégia agêntica double-diamond.
