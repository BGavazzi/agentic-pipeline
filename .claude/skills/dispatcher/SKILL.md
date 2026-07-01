---
name: dispatcher
description: Orquestrador local do pipeline agêntico. Processa fila de tasks em <cwd>/.docs/tasks/*.md (status=todo) — invoca grounding → builder → tester → librarian → notifier sequencialmente; push + PR automáticos quando ciclo verde; ClickUp comment opcional (só quando task tem clickup_id E CLICKUP_API_KEY está set). Trust mode (sem pause-confirm entre tasks; fila é o gate). Loop noturno bounded por quota REAL do plano (quota_gate.py lê rate_limits da statusline: para em 70% da janela 5h, 10pts/dia e 50pts/semana da janela 7d, cap de tasks). Scripts do pipeline em PIPELINE_SCRIPTS_DIR (default: <repo>/scripts/). Triggers - "/dispatcher", "rodar fila", "processa as tasks", "pega próxima task". Suporta /loop /dispatcher via ScheduleWakeup. STATUS - V1.1 quota-bounded, TOS-safe (dentro da sessão Claude Code interativa).
tools: Bash, Read, Edit, Write, Glob, Grep, Skill, ScheduleWakeup
---

# Dispatcher

**Runtime: sessão Claude Code aberta + interativa.** Spec humana: `.docs/skills/dispatcher.md`.

Orquestrador. Quando invocado: pega 1 task ready da fila, roda pipeline end-to-end, fecha. Em `/loop` mode usa ScheduleWakeup pra re-fire.

## 1. Inputs

- `cwd`: working dir da sessão Claude Code (assumido = repo target)
- `repo_path`: opcional override (default = cwd)
- `loop_mode`: detectado via prompt `/loop /dispatcher` (Claude Code primitive)

**Fonte de quota (loop mode):** `<repo_path>/.claude/quota-state.json`, escrito pelo statusline (`.claude/statusline_quota.py`) a partir do bloco `rate_limits` que o Claude Code injeta (janelas `five_hour`/`seven_day`, só Pro/Max, populado após a 1ª resposta da API). Pré-requisito: `.claude/settings.json` com `statusLine` apontando pro script. Se ausente, o gate dá STOP fail-safe. Estado do loop em `<repo_path>/.claude/dispatcher-loop-state.json` (gitignored).

## 2. Find next ready task

```bash
# Locate pipeline scripts — set PIPELINE_SCRIPTS_DIR env var to override
SCRIPTS_DIR="${PIPELINE_SCRIPTS_DIR:-$repo_path/scripts}"
# (copy agentic-pipeline/scripts/ into your repo root, or point PIPELINE_SCRIPTS_DIR
#  at wherever validate_task.py / validate_closure.py / quota_gate.py live)

# Scan task dir
TASK_DIR="$repo_path/.docs/tasks"
test -d "$TASK_DIR" || exit "no .docs/tasks/ in repo"

# Iterate tasks in priority + NNNN order
for task in $(ls "$TASK_DIR"/*.md | sort); do
  # Parse frontmatter status + priority + blocked_by
  # (use head -30 + grep/awk; OR Python one-liner via PyYAML)

  # Filter: status==todo
  # Filter: blocked_by tasks all in completed/
  # Filter: no PR already open for feat/<NNNN>-*

  echo "$task"  # first match wins
  break
done
```

**Priority order**:
1. `priority: P0` first
2. then `P1`
3. then `P2`
4. Within same priority: ascending NNNN

**Skip criteria**:
- `status != todo`
- Any `blocked_by` task is NOT in `completed/` (still active)
- Branch `feat/<NNNN>-*` already exists on origin with open PR

Se queue empty → §6 (exit sem ScheduleWakeup).

## 3. Validate task (deterministic gate)

```bash
python "$SCRIPTS_DIR/validate_task.py" "$task"
```

- exit 0 → prosseguir
- exit 1 → mark task como blocked + append erro do validator em §Pendências Honestas; continue queue (não trava)
- exit 2 → script erro (PyYAML missing) → STOP, log fatal

## 4. Loop principal (per task)

```
1. Read task: parse frontmatter (status, priority, type, target_repo, clickup_id, blocks, blocked_by, arquivos_afetados)
2. Update task: status: in_progress, updated: <today>
3. Branch (base = integration em repo com deploy; senão main):
   BASE=$(git ls-remote --heads origin integration | grep -q . && echo integration || echo main)
   git checkout "$BASE"
   git pull --rebase origin "$BASE"
   git checkout -b feat/<NNNN>-<slug>  (ou checkout existente se já criada)
4. Invoke Skill(codebase-grounding) com task_path + repo_path
   → resultado: contexto + constitution loaded
5. Invoke Skill(builder) com task_path + brief from grounding
   → resultado: commits no branch, checkboxes da task marcadas
6. Invoke Skill(tester) com task_path + branch + mode='prototype'
   → resultado: report em prosa + ARTEFATO .docs/test-reports/<NNNN>.{xml,json}
   - GATE NO ARTEFATO, não na prosa (anti-AI-pitfall): ler o .json e exigir
     existe? · git_rev == HEAD da branch? · todos os steps exit 0? · cobertura ≥ threshold (se §Condição exige)?
   - Qualquer um falha/ausente:
     → append §Pendências Honestas na task com link pro report
     → SKIP downstream; jump pra §5 (continue queue)
6b. Invoke Skill(ultrareview) com task_path + branch + test_report + risk_level
    (subagente INDEPENDENTE — não herda o "passei" do tester)
    → re-executa a suíte + fake-green scan + (alto risco) maioria adversarial
    → resultado: .docs/review-reports/<NNNN>-<ts>.md com verdict PASS|BLOCK
    - risk_level: 'high' se a task toca schema/RBAC/migration/contract; senão 'normal'
    - BLOCK → append §Pendências + link; SKIP downstream; jump §5
7. Invoke Skill(librarian) com task_path + branch + tester_report_path
   → librarian roda validate_closure.py internamente (já wired)
   → resultado: docs commitados, frontmatter librarian_pass set
   - Se librarian falha: idem § anterior (skip downstream, continue)
8. Push + PR + notificação:
   git push origin feat/<NNNN>-<slug>  (non-interactive — token cached / SSH key)
   gh pr create --base "$BASE" --title "<title from task>" --body-file <prepared from CHANGELOG_BRANCH>   # $BASE do §3
   - Sem --reviewer flag (sem @-mention; pattern solo)
   # ClickUp é opt-in: só notifica se task tem clickup_id E CLICKUP_API_KEY está set
   if task.clickup_id AND env.CLICKUP_API_KEY:
     Invoke Skill(notifier) com event='pr.opened' + payload {clickup_id, pr_url, title, channels=['clickup','github']}
     → notifier posta comment ClickUp + GitHub PR comment
   else:
     Invoke Skill(notifier) com event='pr.opened' + payload {pr_url, title, channels=['github']}
     → notifier posta só GitHub PR comment
9. Move task → completed/:
   git mv .docs/tasks/<NNNN>-*.md .docs/tasks/completed/
   git commit -m "chore(NNNN): move task to completed/"
   git push
10. Log:
    Write <repo>/.docs/dispatcher-log/<YYYY-MM-DD>-<NNNN>.md com TL;DR
11. Quota gate (loop mode) — roda o gate determinístico marcando esta task como concluída:
    python "$SCRIPTS_DIR/quota_gate.py" --repo "$repo_path" --record --json
    Guarda o verdict + números de quota (5h/7d, consumo do dia, dia do loop). O exit code
    (0=CONTINUE / 1=STOP) decide o §6. Single-shot mode: rodar sem --record só pra reportar.
12. Output ao caller (§5)
```

## 5. Output (per task)

```
✅ Dispatcher — task <NNNN>: <título>
Repo: <repo>
Branch: feat/<NNNN>-<slug>
PR: #<num> https://github.com/<org>/<repo>/pull/<num>
Commits: <N>
Tests: <pass details OR pending>
Librarian: 7/7 Lei de Fechamento §3 OK
ClickUp: <comment_id | skipped (no clickup_id or no CLICKUP_API_KEY)>
Quota: 5h <X%> · 7d <Y%> · consumo do loop hoje <D>/10pts · dia <N> do ciclo · tasks <T>/5
Próximo: <CONTINUE → ScheduleWakeup 60s | STOP <motivo do gate> → loop encerra>
```

Se task SKIPPED (validator fail OR tester red OR librarian fail):
```
⚠️ Dispatcher — task <NNNN> SKIPPED: <reason>
Estado: status remains in_progress, §Pendências Honestas atualizada
Branch: <branch_status — created/dirty/clean>
Próximo: humano triagem necessária ANTES da próxima invocação
```

## 6. Stop / ScheduleWakeup

Após task processada (success OR skip):

**Single-shot mode** (`/dispatcher`):
- Exit normal. Sem ScheduleWakeup. Aguarda nova invocação humana.

**Loop mode** (`/loop /dispatcher`):

Decisão gated pela quota REAL do plano. Só dispara o próximo wake se **TODAS** verdadeiras:
1. queue ainda tem ready task, E
2. `quota_gate.py` (§4 passo 11) retornou **exit 0 (CONTINUE)**.

→ `ScheduleWakeup(60, '/dispatcher', 'next task in queue')`

**Para o loop (sem ScheduleWakeup) se QUALQUER:**
- queue empty → "queue vazia, loop termina".
- `quota_gate.py` exit 1 (**STOP**) → reportar o motivo exato do gate (ex: "5h em 71%", "budget diário 7d gasto: 10pts", "budget semanal 50pts", "cap de tasks 5/5", "quota signal missing — fail-safe"). **NÃO contornar, NÃO re-tentar.** O loop encerra limpo; retoma na próxima noite (novo loop-day) ou quando a janela resetar.
- 3 tasks consecutivas SKIPPED → exit (humano triagem).

O gate é a única autoridade de "pode continuar?". O dispatcher NUNCA estima quota por conta própria nem ignora um STOP. Se `quota-state.json` não existe (statusline não configurado), o gate dá STOP fail-safe — configurar `.claude/settings.json` + `statusline_quota.py` é pré-requisito do loop mode.

## 7. Hard rules

- **TOS-safe**: roda APENAS dentro da sessão Claude Code interativa aberta pelo humano. NUNCA invocar `claude` CLI como subprocess.
- **Quota é lei.** No loop mode, `quota_gate.py` é a única autoridade de "pode continuar?". STOP do gate = loop encerra, sem exceção, sem contornar, sem re-tentar (alinhado à mitigação ToS: volume bounded → [[anthropic-tos-loop-considerations]]). Tetos: 70% da janela 5h; 10pts/dia e 50pts/semana da janela 7d; cap de tasks. Sinal de quota ausente → STOP fail-safe (nunca CONTINUE no escuro).
- **Não inventa tasks.** Só processa o que existe em `.docs/tasks/` com `status: todo`. (Ver memória [[feedback-keep-going-not-scope-inventing]].)
- **Não modifica spec da task.** Lê §O Que Fazer + §Condições; se ambíguo, marca blocked em §Pendências.
- **Não @-menciona reviewer** em comments ClickUp/GitHub. Pattern solo. Notifier sem `mentions` payload.
- **Não faz merge** no GitHub. Só push + PR. Merge sempre humano.
- **Não escolhe modelo.** Roda no modelo da sessão atual.
- **Idempotency**: task já em `completed/` = no-op. Branch já com PR aberto = skip create; se ClickUp ativo, atualiza comment.
- **Crash safety**: se Claude Code morre, task em `in_progress` é re-pickable na próxima invocação (validate_task detecta estado e re-tenta).
- **Push non-interactive**: se push prompt credentials, ABORTA + log + skip task. Não fica esperando input (referência [[git-push-hang-is-afk-timeout]]).

## 8. Failure modes

| Erro | O que fazer |
|---|---|
| Queue vazia | Exit, no ScheduleWakeup. Log "queue empty, /loop terminates". |
| `validate_task.py` exit 1 | Append erro em §Pendências, continue queue |
| Branch já existe + PR aberto | Skip create; se ClickUp ativo (clickup_id + key), atualiza comment |
| `git push` rejected (não-fast-forward) | `git pull --rebase origin main`; se conflito → mark blocked, continue |
| `git push` hang (credential prompt) | Timeout 30s → kill + skip task + log [[git-push-hang-is-afk-timeout]] |
| `gh pr create` falha (auth) | Log + continue queue (próxima invocação tenta de novo) |
| Tester vermelho / artefato ausente | Continue queue; report em .docs/test-reports/. Sem artefato = gate trava (tester não rodou). |
| Ultrareview BLOCK | Continue queue; task fica in_progress; .docs/review-reports/ tem o finding. NÃO contornar (é o anti-pitfall). |
| Librarian erro | Continue queue; task fica in_progress pra re-run |
| Notifier falha (ClickUp 4xx) | Loga; não bloqueia (PR já aberto) |
| 3 tasks consecutivas SKIPPED | Exit /loop. Sinal de problema na fila ou no ambiente. |
| `quota_gate.py` exit 1 (STOP) | Exit /loop limpo. Reportar o motivo (5h/diário/semanal/cap/fail-safe). Não contornar. Retoma na próxima noite ou no reset da janela. |
| `quota-state.json` ausente/vazio | Gate dá STOP fail-safe. Verificar `.claude/settings.json` statusLine + 1ª resposta da API ocorreu. |
| Network down | Retry com backoff (15s, 60s, 300s); depois marca task blocked, continue |
| Sessão Claude Code interrompida (Ctrl+C) | Task atual fica `in_progress`; fila não progride. Próxima invocação re-pega. |

## 9. Anti-patterns

- ❌ Pollar `.docs/tasks/` em paralelo (race condition no `status: in_progress` update)
- ❌ Push automático com `--force` (regra: nunca force push)
- ❌ Comentário no ClickUp tentando "vender" trabalho ("Looks great! All tests passing! 🎉") — caveman + factual (ver convenção de comentário ClickUp)
- ❌ Pular validator com `|| true` ("ah, deve estar ok")
- ❌ Processar task com `priority` ausente — validate_task falha de qualquer jeito
- ❌ Spawn subagents pra tasks diferentes em paralelo V1 (race condition em git branches)
- ❌ Inventar `status: todo` em task que não tinha (= inventar trabalho)

## 10. Skills consumidas

Upstream (nenhuma — dispatcher é o topo).

Downstream (orquestradas por este skill):
- [[codebase-grounding]] (Step 0 constitution loading)
- [[builder]] (impl + commits)
- [[tester]] (V1 prototype mode — emite o artefato de prova-de-execução)
- [[ultrareview]] (gate adversarial independente; gateia no artefato + re-run, não na prosa)
- [[librarian]] (Lei de Fechamento §3, roda validate_closure.py)
- [[notifier]] (ClickUp comment + GH comment se aplicável)

Validators / gates (em `$PIPELINE_SCRIPTS_DIR`, default `<repo>/scripts/`):
- `validate_task.py` (antes do builder)
- `validate_closure.py` (dentro do librarian)
- `quota_gate.py` (fim de cada task no loop mode — decide ScheduleWakeup)

## 11. Concrete example

User invoca `/loop /dispatcher` no Claude Code aberto em `<path>/guidelines_IA/`:

```
Turn 1:
  - Scan .docs/tasks/ → P0 first → encontra 0095-feat-something.md (status: todo)
  - Validate task: PASS
  - Update status: in_progress
  - git checkout -b feat/0095-something main
  - Skill(codebase-grounding) → constituição carregada
  - Skill(builder) → 5 commits, checkboxes [x]
  - Skill(tester) → type-check + lint + boots OK
  - Skill(librarian) → CHANGELOG, SDD entry, continuity; validate_closure PASS
  - git push, gh pr create → PR #N
  - Skill(notifier) → ClickUp comment ✅
  - git mv task → completed/, commit, push
  - quota_gate.py --record → CONTINUE (5h 22% · 7d +3pts hoje · dia 1 · tasks 1/5)
  - ScheduleWakeup(60s, '/dispatcher', 'next task')

Turn 2 (60s later):
  - Scan → 0096-fix-xyz.md (status: todo)
  - ... mesmo ciclo → quota_gate CONTINUE (tasks 2/5) → ScheduleWakeup

Turn N (uma destas encerra o loop):
  - Scan → queue vazia  → exit, "/loop termina"
  - OU quota_gate STOP "5h em 71%" / "budget diário 10pts" / "cap 5/5" → exit, reporta motivo
  - OU 3 SKIPPED seguidas → exit
```

User pode `/stop` o /loop a qualquer momento. O gate garante que, AFK, o loop
para sozinho ao bater qualquer teto de quota — não estoura o plano.

## 12. V2 backlog

- ClickUp `AI: ready to start!` tag polling (requer proxy/webhook)
- Multi-repo scan (`--repos R1,R2,R3`)
- Model selection per task (consulta [`MODEL-SELECTION.guidelines.md`])
- Concurrent dispatch via Agent subagents pra tasks independentes
- Métricas: tokens/task, wallclock, % first-try pass — escreve `.docs/dispatcher-metrics.jsonl`
- Resume após crash: detect `in_progress` tasks e oferecer re-run vs abandon
