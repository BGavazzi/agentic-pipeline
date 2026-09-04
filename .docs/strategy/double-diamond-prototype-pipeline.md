---
title: Triple-Diamond Dev Process
status: draft
owner: <maintainer-email>
created: 2026-05-20
updated: 2026-05-29
related:
  - README.md
  - AGENTS.balanced.md
  - .template/README.md
---

# Processo de desenvolvimento — Triple Diamond

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor deste
> (`guidelines_IA`, tombstoned). Este É o documento que define "Triple-Diamond" /
> "Diamante 2" — termos que o `README.md` deste repo usa e explicitamente diz
> não estarem "spelled out anywhere in this repo yet". Agora estão. Links
> ajustados: referências a `dist/core/` (o antigo mecanismo `git subtree` de
> guidelines_IA) trocadas por `core_sync.py` (o mecanismo atual deste repo);
> "CEO" generalizado pra "decisor sênior/PO", que é o papel real descrito.

> **Nota de nomenclatura.** Este doc nasceu "Double Diamond" (2 diamantes: prototipagem + integração). Em 2026-05-29 evoluiu pra **3 diamantes nomeados**, separando a **Ideação** pra fora da prototipagem — realinhando com o double-diamond clássico, onde o 1º diamante É descobrir/definir o problema. O arquivo mantém o nome antigo pra não quebrar links de entrada; o modelo é triple. Mapa: Prototipagem = antigo "Diamante 1"; Integração = antigo "Diamante 2"; Ideação = novo.

Geramos software em **três diamantes**, cada um um ciclo **diverge → converge**, **repetíveis ad infinitum**. Não é um funil one-way: os loops de feedback entre os diamantes são first-class (ver [§Os loops](#os-loops--ad-infinitum)).

| Diamante | Diverge → Converge | Casa | Output entregue ao próximo | Dirige | Agêntico? |
|---|---|---|---|---|---|
| **I · Ideação** | ideias / sketches → 1 PRD + design escolhido | board de tarefas + Figma | **spec** (PRD + brief visual), não código | humano | parcial — `grill-me` + skills figma assistem |
| **II · Prototipagem** | implementações → 1 protótipo rodando | repo novo **OU** branch num repo existente | **código provando o conceito** | agêntico (pipeline de skills) | **total** |
| **III · Integração** | absorver no canônico → PRs close-to-merge | repos canônicos | **prod** | humano sênior | **NÃO — fora do fluxo agêntico, até 2ª ordem** |

O **fluxo agêntico cobre I (parcial) + II (total) e PARA no handoff II → III.** A Integração é deliberadamente humana e fora do fluxo — ver [§Diamante III](#diamante-iii--integração).

---

## Por que três (e por que a fronteira agêntica está onde está)

| Eixo | Ideação | Prototipagem | Integração |
|---|---|---|---|
| **Custo de explorar** | baixo (conversa + sketch) | baixo (agentes geram, não pessoas) | alto (gente sênior é cara) |
| **Reversibilidade** | total (é só spec) | alta (mock data, decisões descartáveis) | baixa (código integrado tem dependências) |
| **Risco de drift arquitetural** | n/a | aceitável e contido (protótipo ignora DDD canônico de propósito) | controlado pela gente sênior |
| **Quem decide trade-offs** | PO/humano | o pipeline, dentro de trilhos reversíveis | tech lead humano |

A separação Ideação ↔ Prototipagem evita codar antes de definir. A fronteira Prototipagem ↔ Integração é o gate caro: ninguém sênior toca código antes dele.

---

## Diamante I — Ideação

**Diverge → converge sobre o *problema*.** Explora ideias, sketches, alternativas no Figma; converge num PRD enxuto + design escolhido.

- **Casa:** board de tarefas (ticket + discussão) + Figma (sticky → frame).
- **Output:** `spec` — `.docs/PRD.md` + brief visual JSON/PNG. **Não é código.**
- **Agêntico?** Parcial: `grill-me` (PRDfier — entrevista o autor até a spec ficar acionável) e `figma-frontend-context` (Designer — extrai brief do frame) assistem. A *decisão* do que vale fazer é humana.

Critério de saída: PRD acionável + design referenciável, prontos pra virar tasks.

---

## Diamante II — Prototipagem

**Diverge → converge sobre a *solução*.** Do PRD/brief ao protótipo rodando, conduzido end-to-end pelo pipeline agêntico.

### Onde o código nasce — repo novo OU branch

Prototipagem **não é só "repo novo"**. A propriedade que a define é **reversibilidade / descartabilidade** (mock data, SQLite, decisões reversíveis), não *onde* o código mora:

- **Greenfield** → repo novo bootstrapado a partir do esqueleto em [`.template/`](../../.template/README.md), num namespace separado de prototypes.
- **Brownfield** → branch num repo canônico existente.

Os dois são Prototipagem desde que o output seja reversível. Amarrar a "repo novo" excluiria ~80% do trabalho real.

### O que o repo herda — o agentic core

Tanto greenfield quanto brownfield rodam sobre o **agentic core** deste repo: skills do pipeline + validators, vendorados via [`core_sync.py`](../../README.md#quick-start) em `.claude/skills/` + `scripts/`. **O core é o substrato que torna a Prototipagem barata e repetível entre repos — não é um diamante, é o trilho.**

### Etapas (pipeline 9-stage)

| # | Etapa | Skill canônica | Input | Output |
|---|---|---|---|---|
| 1 | **PRDfier** | `grill-me` | Ticket + product knowledge | PRD em `.docs/PRD.md` *(borda com Ideação)* |
| 2 | **Designer** | `figma-frontend-context` | Sticky Figma → frame | Brief JSON + PNG *(borda com Ideação)* |
| 3 | **Engineer** | `codebase-grounding` (+ `implement-figma-task` se UI) | Brief + repo | Tasks atômicas em `.docs/tasks/NNNN-*.md` |
| 4 | **Tasks** | `.docs/tasks/` (`validate_task.py`) | Output do Engineer | Estado mutável (todo/in-progress/done) |
| 5 | **Builder × N** | `builder` | Task `NNNN-*.md` | Commit(s) que fecham a task |
| 6 | **Reviewer** | `ultrareview` | Branch com commits | Review report + comments |
| 7 | **Tester** | `tester` (modo `prototype`) | Branch revisada | Verde/vermelho + log + screenshots |
| 8 | **Librarian** | `librarian` (`validate_closure.py`) | Branch verde | CHANGELOG, function-catalog, SDD_KIT, ROUTE_MAP atualizados |
| 9 | **Notifier** | `notifier` | Estado final do PR | Comentário no board + PR GitHub |
| 0 | **Dispatcher** | `dispatcher` | Fila `.docs/tasks/` | Orquestra 1→9 (quota-aware; só sessão interativa) |

### Runtime — sessão Claude Code aberta

Builder/Tester/Notifier **não são serviços standalone**; são skills invocadas por **uma sessão que orquestra o ciclo** (o `dispatcher` faz isso sobre a fila). Contexto carregado uma vez, handoff in-memory, falha volta pro humano via interrupt, paralelismo via subagents. Sem infra extra: `claude` com `/loop` já é o pipeline.

### Critério de saída do Diamante II

Protótipo merece chegar ao gate quando as etapas 1–9 fecharam ≥1 vez e o repo tem:

- [ ] README com 1-parágrafo de demo
- [ ] `docker compose up` (ou equivalente) roda local
- [ ] PRD em `.docs/PRD.md`
- [ ] Screenshots/GIF do happy path
- [ ] Tests do happy path passando (cobertura baixa OK)
- [ ] Link de preview / domínio temporário

Divergência de design system e **estrutura de dados descartável** (SQLite/JSON/in-memory) são aceitáveis aqui.

### O que NÃO entra na Prototipagem

Auth canônica (`<auth-api-repo>`) — mock OK · multi-tenant · RBAC granular · pipeline de dados real · observabilidade além de log básico · performance budget · migrations reversíveis · soft delete consistente · i18n não-trivial. Tudo isso é Integração.

---

## O gate II → III — reunião humana

**Trigger humano, não automatizado.** Sem tag `AI: greenlit`, sem hook, sem comentário-trigger. **Por design**: aprovar um protótipo pra integração merece o atrito de uma conversa — força discutir escopo, custo da Integração e prioridade vs backlog sênior.

O decisor sênior/PO decide:
- **Go** → entra Integração.
- **No-go** → repo vai pro `.archive/`; retro de 1 página.
- **Iterate** → volta pra Prototipagem (ou Ideação) com refinamentos. *(este é um dos loops — ver abaixo.)*

Após Go, o humano: promove o repo pro namespace canônico (se greenfield); cria task pai; atribui senior tech lead.

---

## Diamante III — Integração

**Diverge → converge sobre o *encaixe no canônico*.** Absorve o que o protótipo provou nos sistemas de produção. Saída: **PRs close-to-merge** nos repos canônicos.

### Fronteira: fora do fluxo agêntico — "até 2ª ordem"

**Decisão explícita:** a Integração fica **fora do fluxo agêntico**. O pipeline para no handoff II → III. Agente **não dirige** migration, DDD-mapping ou PR-canônico — **gente sênior humana lidera**. É boundary **deliberado e revisitável** ("até 2ª ordem"): quando o pipeline amadurecer e a confiança subir, dá pra reabrir parte da Integração pra assistência agêntica. Hoje, não.

Aqui (diferente da Prototipagem): DDD on data structure é mandatório · design system converge · migrations reais · observabilidade plena · segurança (RBAC, multi-tenant, secret rotation).

### Input vital — documentação do macrossistema

A Integração **não começa sem** consultar a documentação arquitetural do(s) repo(s) canônico(s) alvo (schema, ADRs retroativos, state machines, permissions matrix, API contract, design tokens, lacunas/divergências — o que existir por repo). Antes de qualquer migration nova: já existe entidade equivalente? Regra de soft delete? O state flow casa?

---

## Os loops — ad infinitum

Os três diamantes **ciclam**; as setas de volta são onde mora o valor:

```
      ┌──────────────────────── learnings de prod re-abrem problema ──────────────────────┐
      ▼                                                                                     │
  ┌─────────┐   spec    ┌──────────────┐  código  ┌──[gate humano]──┐  Go   ┌─────────────┐
  │ IDEAÇÃO │ ────────▶ │ PROTOTIPAGEM │ ───────▶ │ reunião decisor │ ────▶ │ INTEGRAÇÃO  │
  └─────────┘           └──────────────┘          └────────┬────────┘       └─────────────┘
      ▲                        ▲                            │
      │                        │  Iterate                   │ No-go → .archive + retro
      └── re-ideação ──────────┴────────────────────────────┘
```

- **Iterate** (gate → Prototipagem): refina o protótipo sem subir pra Integração. Um output de Prototipagem pode ficar como versão final por tempo indeterminado — "good enough" é decisão válida.
- **No-go** (gate → arquivo): morre limpo, com aprendizado registrado.
- **Re-ideação** (qualquer estágio → Ideação): protótipo que falha ou prod que ensina algo re-abre o problema.

Cada diamante é também internamente iterável — "Prototipagem again" é o caso comum.

---

## Eixos ortogonais (não confundir com o diamante)

- **Rigor de teste** (`prototype` vs `production` mode do `tester`) é ortogonal — rigor pode subir DENTRO da Prototipagem sem virar Integração.
- **Escopo V1 → V2** (features novas) é ortogonal — features V2 cabem na Prototipagem.
- **Merge na main ≠ Integração** — smoke + merge são gates leves na borda do agêntico; o código pode estar na main e ainda ser Prototipagem.

---

## Decisões em aberto

- **Quando um protótipo "morre"?** Sem reunião em N semanas → `.archive/`? Quem dá o veredito?
- **Notifier comenta no ticket ou só em chat?** Provavelmente os dois (chat=urgência, ticket=histórico).
- **Integração sempre destrói o repo do protótipo?** Sugestão: não — manter num namespace de archive como referência pra retro.
- **Reabrir a fronteira agêntica da Integração** — revisitar "2ª ordem" quando o pipeline amadurecer.
