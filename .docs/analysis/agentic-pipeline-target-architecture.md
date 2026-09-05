# Playbook do Pipeline Agêntico End-to-End (arquitetura-alvo)

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor
> deste (`guidelines_IA`, tombstoned). Este é o **fluxo-alvo completo**
> (ticket → PR sem intervenção humana, exceto nos pontos onde ela é
> obrigatória) — hoje partes existem neste repo (skills individuais, gate
> scripts), mas o orquestrador webhook-driven completo (§07-B a §07-E, §07-I)
> **não foi construído**. `dispatcher` cobre uma versão simplificada, session-
> driven (não webhook-driven) do meio do fluxo (estágios 4-7). Nomes de
> modelo atualizados pra geração corrente (Opus 5 / Sonnet 5 / Haiku 4.5);
> menção a "FIS" removida de um exemplo de sprint.

Como um ticket vira um PR sem intervenção humana — exceto nos pontos em que humano é obrigatório (autorização de commit, decisão de produto, code review).

Este é o **fluxo-alvo**. O playbook define cada estágio, quem é responsável, o contrato de entrada e saída, e os arquivos onde mora cada peça.

---

## A · Visão de alto nível

```
[Humano cria ticket]
            │
            ▼
[Webhook  ──→  Listener]
            │
            ▼
[Validator: schema da tarefa OK?]  ──não──▶  [Tag "AI: more info needed", encerra]
            │ sim
            ▼
[Classifier: AI-ready? Quem é o owner?]  ──não-AI──▶  [Tag "AI: human only", encerra]
            │ sim
            ▼
[Agent Dispatcher escolhe modelo + prompt + repo]
            │
            ▼
[Agente cria revisão nova: "task-nnnn"]
            │
            ▼
[Loop: ler tarefa → planejar → editar → testar]
            │
            ▼
[Lei de Fechamento: validador roda]  ──fail──▶  [Tag "lei-fechamento:incomplete", agente revisa]
            │ pass
            ▼
[Agent push para branch]
            │
            ▼
[PR aberto → comentário no ticket com link do PR]
            │
            ▼
[Humano review → merge → tag "completed" → status atualizado por webhook reverso]
```

---

## B · Estágio 1 — Listener de webhook

**Responsabilidade**: receber eventos do board de tarefas e enfileirar para processamento.

**Contrato de entrada** (request body do webhook):

```json
{
  "event": "taskCreated | taskUpdated | taskTagUpdated",
  "task_id": "86xxxxxxx",
  "history_items": [...],
  "webhook_id": "..."
}
```

**Comportamento**:

1. Validar HMAC.
2. Filtrar: ignorar eventos onde `tag` não é `AI: ready to start!` ou onde `status` não muda para `to do | open`.
3. Enfileirar em uma queue local (ex: SQLite WAL).
4. Retornar 202 imediato (não bloquear webhook).

**Custo de implementação**: ~1 dia.

---

## C · Estágio 2 — Validador de schema da tarefa

**Responsabilidade**: garantir que a tarefa segue o schema de [`clickup-task-schema.md`](../conventions/clickup-task-schema.md) antes de invocar agente.

**Comportamento**:

1. `GET /v2/task/{task_id}`.
2. Parsear `markdown_description` com regex de seções (`## Context`, `## Problem`, `## What To Do`, etc.).
3. Validar os critérios do schema.
4. Se fail: postar comentário no ticket explicando o que falta + adicionar tag `AI: more info needed` + remover `AI: ready to start!`. Encerra.
5. Se warn: prossegue mas anota no log.
6. Se pass: passa adiante.

**Comentário automático em caso de fail** (template):

```
🤖 **Validador de Schema** — Não pude prosseguir. O ticket precisa de:
- [ ] Seção "## Exit Conditions" (encontrei 0 critérios verificáveis)
- [ ] Pelo menos 1 path em "## Affected Files"

Ver template em `.docs/tasks/000-template.md`.
Ao corrigir, marque a tag `AI: ready to start!` novamente e o pipeline retoma.
```

**Custo**: ~3-4h.

---

## D · Estágio 3 — Classifier (AI-ready?)

**Responsabilidade**: decidir se a tarefa é candidata a execução agêntica e, se sim, qual repo + modelo + prompt.

**Heurística de baseline (sem LLM)**:

| Sinal | Sugestão |
|---|---|
| Frontmatter `type: feat` + arquivos de teste listados | AI-ready |
| `type: fix` + reprodução clara | AI-ready |
| `type: refactor` + escopo cirúrgico (≤3 arquivos) | AI-ready |
| `type: docs` | AI-ready (Sonnet ou Haiku) |
| `type: proposal` | NÃO — é planning, requer humano |
| `type: audit` | Marginal — pode ser AI-ready se for auditoria executável (rodar grep + reportar). NÃO se for revisão arquitetural. |
| Menciona "Figma" ou "design" | NÃO — humano |
| Menciona "decisão de produto" ou "stakeholders" | NÃO — humano |
| `priority: P0` + `type: fix` | AI-ready com flag de urgência (modelo de raciocínio mais profundo) |

**Saída do classifier**:

```python
@dataclass
class ClassifierVerdict:
    ai_ready: bool
    reason: str
    suggested_model: Literal["haiku-4.5", "sonnet-5", "opus-5"]
    target_repo: str
    estimated_difficulty: Literal["trivial", "moderate", "hard"]
    needs_thinking: bool    # se sim, prompt incluirá pedido de mais deliberação
```

**Modelo escolhido**: do [`MODEL-SELECTION.guidelines.md`](../../MODEL-SELECTION.guidelines.md). Mapping:

- `trivial` + `docs/chore` → Haiku 4.5
- `moderate` + `feat/fix/refactor` → Sonnet 5
- `hard` + arquitetural → Opus 5 (`/fast` quando latência importar)
- `priority: P0` ou `audit` crítico → Opus 5 (`/fast`)

> O harness auto-gerencia o esforço de raciocínio; não há budget fixo por palavra-mágica. "Pense mais"/"ultrathink" são apenas nudges suaves.

**Custo**: ~1-2 dias se for puramente heurística; +1 dia se incluir LLM call para casos ambíguos.

---

## E · Estágio 4 — Agent Dispatcher

**Responsabilidade**: efetivamente lançar o agente com o contexto certo.

**Implementação**: depende da ferramenta de agente (Claude Code CLI, etc.). Pode ser um shell script que:

1. `cd <target_repo>`
2. Cria uma revisão isolada nova para a tarefa
3. Prepara o prompt:
   - System: `cat AGENTS.md` + `cat <sdd_kit_path>` + `cat function-catalog.md` (se aplicável) — anexar em ordem para cache hit em sessões subsequentes da mesma tarefa
   - User (primeiro turno): "Você está trabalhando na tarefa <task_id>. Leia <task_path>, alinhe com `.agents/continuity-<seunome>.md`, e proceda. Reserve mais deliberação no planejamento se a tarefa for `hard`."
4. Invoca o agente.

**Custo**: ~2-3 dias para chegar a uma versão útil que cobre 1 ferramenta de agente.

---

## F · Estágio 5 — Loop de execução (o que o `builder` já faz neste repo)

Este é o **agente trabalhando**. Não é um estágio do pipeline em si — é o que o agente faz dentro da revisão. Mas o pipeline depende de o agente seguir corretamente:

**Sequência canônica do agente**:

1. Lê `AGENTS.md` (já carregado em contexto pelo dispatcher).
2. Lê `.agents/continuity-<seunome>.md` (Protocolo Zero).
3. Lê a tarefa (`.docs/tasks/nnnn-...md` ou via API).
4. Se a tarefa é `multi_agent: true`: registra lock em `.agents/file-locks.md` para os arquivos da seção "Affected Files".
5. **Pensa** (deliberação mais profunda como nudge suave se o classifier marcou `hard`): produz plano breve.
6. Edita arquivos.
7. Roda testes. Se falham: itera.
8. Atualiza: `CHANGELOG.md`, function-catalog (se assinatura mudou), `SDD_KIT.md` (se nova decisão — flag `Dxx`), `README.md` (se aplicável), continuity, route map (se rota alterada).
9. Marca cada item da "Required Documentation" do ticket como `[x]` ou `[N/A]`.
10. Libera lock em `.agents/file-locks.md`.
11. Para — não dá push sozinho. Notifica o pipeline que está pronto para validação.

**Importante**: o passo 11 é hard rule. **Agente nunca dá push sozinho.** O passo seguinte (validador de fechamento + autorização de push) é responsabilidade do pipeline.

---

## G · Estágio 6 — Validador de Fechamento (o que `validate_closure.py` já faz neste repo)

**Responsabilidade**: validar que a Lei de Fechamento foi cumprida antes de permitir push.

**Comportamento**:

1. Lê o arquivo da tarefa pós-execução.
2. Valida:
   - Todos os `[ ]` da seção "Required Documentation" estão `[x]` ou `[N/A]` (com justificativa).
   - Última modificação dos arquivos referenciados é posterior ao início da revisão.
   - Testes passam — roda na revisão atual.
   - Não há `# TODO(<agente>):` introduzidos sem rastreio em tarefa existente.
   - `CHANGELOG.md` tem entrada nova no topo, com `**Author**: <agente>`.
3. Saída JSON:

```json
{
  "task_id": "86xxxxxxx",
  "status": "pass | warn | fail",
  "checks": [
    {"name": "checklist_complete", "result": "pass"},
    {"name": "function_catalog_updated", "result": "pass"},
    {"name": "tests_passing", "result": "pass"},
    {"name": "changelog_entry", "result": "pass"},
    {"name": "no_orphan_todos", "result": "warn", "detail": "TODO em src/foo.py:34 sem tarefa rastreada"}
  ]
}
```

4. Se `pass`: prossegue para Estágio 7.
5. Se `warn`: prossegue mas registra; humano vê no PR.
6. Se `fail`: para. Posta comentário detalhado no ticket. Tag `lei-fechamento:incomplete`.

---

## H · Estágio 7 — Push e PR

**Responsabilidade**: criar PR + linkar ao ticket.

**Comportamento**:

1. **Pede autorização ao usuário** no chat. (Hard rule, não-derrogável.)
2. Se autorizado: cria branch, push, cria PR via API.
3. Posta comentário no ticket:
   ```
   🤖 PR criado: <link>
   Branch: task-nnnn
   Validator: PASS
   Tests: 168/168 passando
   Documentação: ✅ Lei de Fechamento cumprida
   ```
4. Atualiza status para `review`.
5. Atualiza tag `AI: in-progress:<agente>` → `AI: in-review`.

---

## I · Estágio 8 — Pós-merge

**Responsabilidade**: fechar o ciclo quando o PR é mergado.

**Trigger**: webhook do GitHub (`pull_request.closed` com `merged: true`).

**Comportamento**:

1. Encontrar o ticket associado (do título do PR ou comentário).
2. Atualizar status para `completed`.
3. Mover `.docs/tasks/nnnn-...md` para `.docs/tasks/completed/`.
4. Postar comentário no ticket: "✅ Mergeado em <commit-hash>."

---

## J · Onde humanos entram (e por quê)

| Ponto | Humano obrigatório? | Razão |
|---|---|---|
| Criar ticket | Sim — humano descreve o que quer | Decisão de produto |
| Ticket validar schema | Não | Mecânico |
| Classificar AI-ready | Não (mas humano pode forçar) | Heurística |
| Agente executar | Não | Esse é o ponto |
| Push para remote | **Sim — autorização explícita** | Hard rule, segurança |
| Code review | Sim | Sempre |
| Merge | Sim | Sempre |

O humano não é gargalo na execução, só nos **pontos de decisão**. A maioria dos tickets passa do estágio 1 ao 7 sem intervenção, o humano só atua na criação e na review/merge.

---

## K · Métricas para monitorar o pipeline

| Métrica | Fonte | Como interpretar |
|---|---|---|
| Tickets criados / dia | board de tarefas | Saúde do funil |
| % tickets `AI: ready to start!` no momento de criação | Validador | Se baixo: humanos não conhecem o template |
| Tempo médio: ticket criado → PR aberto | Logs do dispatcher | Se >2h: agente está travando |
| % de PRs com `validator: pass` | CI | Saúde da Lei de Fechamento |
| % de PRs mergeados sem mudanças do reviewer humano | GitHub | Saúde do agente |
| % de tickets que entram em loop "AI: more info needed" e voltam | board de tarefas | Qualidade dos tickets criados |

---

## L · Roadmap de implementação (exemplo genérico)

| Sprint | Foco | Entregável |
|---|---|---|
| **Sprint 1** | Schema + validador | Schema aplicado em todos os repos alvo; validadores rodando como pre-commit hook |
| **Sprint 2** | Webhook listener + dispatcher | Listener + dispatcher mínimo que invoca Claude Code CLI; primeira execução end-to-end manual |
| **Sprint 3** | Auto-execução com supervisão | Tarefas reais passam pelo pipeline com humano dando autorizações; ajustes finos |
| **Sprint 4** | Métricas + relatório | Dashboard mínimo, `success rate > 70%` como meta inicial |

---

## M · Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Agente "ganha competência" no schema e ignora a tarefa real | Validador de fechamento checa testes — testes são a verdade |
| Múltiplos agentes pegam mesma tarefa | Custom field `agent_owner` com lock; webhook só dispatcha quando o field está vazio |
| Webhook falha silenciosamente | Recovery poller — loop periódico verificando tickets `AI: ready` sem `agent_owner` |
| Push automático sem autorização | Não existe nesse design. Hard rule. |
| Token/custo explode | Métricas de tokens/PR; alerta se média sobe >30% |
| Drift entre `.docs/tasks/` e o board | Source of truth declarado no footer de cada ticket; script daily-diff que reporta divergências |
