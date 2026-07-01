---
name: meta-test
description: Roda fixtures de teste para skills do pipeline (builder/tester/notifier) usando Agent tool — spawnar subagent isolado por fixture, validar git state + task state + trajectory contra expected.yaml. Triggers - "/test-builder", "/test-skills", "roda os testes das skills", ou usuário pede pra validar mudança em SKILL.md. Runtime - Claude Code session (kept open) — consome subscription quota, não API tokens.
tools: Bash, Read, Glob, Agent
---

# meta-test

**Runtime: sessão Claude Code aberta.** Skill de **teste de skills** — sem API tokens, sem CI gate-on-PR; use manualmente após mudança em qualquer `.claude/skills/<X>/SKILL.md` ou periodicamente via `/loop /test-builder`.

Arquitetura "tests in-session":
- Cada fixture é um **subagent isolado** spawned via `Agent` tool.
- Subagent herda contexto da sessão pai, recebe prompt enxuto apontando pra task seed.
- Sessão pai valida: git state + task.md state + trajetória (do report do subagent) vs `expected.yaml`.
- Nenhum processo externo, nenhuma chamada API direta — tudo dentro da sessão.

## Quando invocar

- Após editar `.claude/skills/<X>/SKILL.md` em qualquer skill testada.
- Quando uma fixture nova é adicionada em `tests/skills/fixtures/`.
- Periodicamente em loop (`/loop /test-builder`) — manual, não automatizado externamente.

## O que testa hoje

| Skill | Fixtures cobertas | Status |
|---|---|---|
| `builder` | 1: 001-trivial-readme-edit | baseline (happy path) |
| `tester` | — | TODO |
| `notifier` | — | TODO |

Cada fixture deve cobrir um caso distinto: happy path, decision-tree branch, anti-pattern detection. Não duplicar.

## Loop principal

```
1. Glob: tests/skills/fixtures/*/expected.yaml
   → lista de fixtures executáveis

2. Para cada fixture:
   a. Bash: tests/skills/lib/setup.sh <fixture_name>
      → cria /tmp/test-<fixture_name>/ com seed-repo extraído
      → retorna path absoluto do sandbox

   b. Agent tool spawn:
      subagent_type: general-purpose
      description: "Test <skill> via <fixture_name>"
      prompt: see "Subagent prompt template" §below

   c. Subagent retorna texto descrevendo o que fez:
      - lista de tool calls em ordem
      - commits criados (sha + msg)
      - status final da task
      - quaisquer erros encontrados

   d. Bash: tests/skills/lib/assert.sh <fixture_name> <sandbox_path>
      → compara git state + task.md vs expected.yaml
      → retorna 0 (pass) ou 1 (fail) + diff humano

   e. Bash: tests/skills/lib/teardown.sh <fixture_name> (limpa sandbox)
      ← OPCIONAL: skip teardown se TESTS_KEEP=1 (debug)

3. Output: summary table
   fixture | skill | pass | duration | notes
   001     | builder | ✅ | 45s | -
   002     | builder | ❌ | 32s | §Condição [3] não marcada
```

## Subagent prompt template

Passa via `Agent` tool, ajustando `<placeholders>`:

```
You are a Builder subagent under test. Read your full instructions from
.claude/skills/builder/SKILL.md and behave exactly as production would.

Test context:
  Sandbox repo: <sandbox_path>
  Task to execute: <sandbox_path>/.docs/tasks/<task_filename>
  Working directory: <sandbox_path>

Constraints (NON-NEGOTIABLE — same as production):
  - Surgical changes only — §Arquivos Afetados is contract
  - Tests must pass at commit
  - Lei de Fechamento §3 completa or [N/A] with justification
  - NEVER --no-verify, --force, commit secrets
  - NEVER push (this is a sandbox)

At the end, report back in this exact format:

  RESULT
  ======
  Task status final: <todo|in_progress|done>
  Branch created: <branch_name>
  Commits: <count>
    - <sha1> <subject>
    - <sha2> <subject>
  Files touched: [<path1>, <path2>, ...]
  §Condições marked done: <count>/<total>
  Lei de Fechamento §3 items addressed:
    - CHANGELOG: <yes|no|N/A>
    - function-catalog: <yes|no|N/A>
    - SDD_KIT: <yes|no|N/A>
    - README: <yes|no|N/A>
    - continuity: <yes|no|N/A>
    - tests passing: <yes|no|N/A>
    - ROUTE_BEHAVIOR_MAP: <yes|no|N/A>
  Errors encountered: [<list or 'none'>]
  Tool call sequence (high level): [Read, Read, Edit, Bash, Edit, Bash, Edit, Bash]

Begin execution.
```

## Fixture structure

```
tests/skills/fixtures/<NNN>-<slug>/
├─ seed-repo.tar.gz        bundled mini-repo with AGENTS.md + .docs/tasks/ + initial state
├─ task-id.txt             contains the task filename to execute (e.g., 0001-add-greeting.md)
├─ skill.txt               which skill is under test (builder | tester | notifier)
├─ expected.yaml           assertions to compare against subagent report + git state
└─ README.md               short description of what this fixture covers
```

`expected.yaml` schema:

```yaml
skill: builder
task_id: 0001-add-greeting
expected:
  task_status_final: done
  branch_pattern: "^feat/0001-"               # regex
  commits_min: 1
  commits_max: 3
  files_touched: [src/greeting.ts, .docs/tasks/0001-add-greeting.md, CHANGELOG.md]
  files_NOT_touched: [.env, package-lock.json]
  conditions_marked_done: 3                    # all conditions
  lei_de_fechamento:
    CHANGELOG: yes
    continuity: yes
    tests: yes
    # rest: N/A acceptable
  tool_calls_must_include_in_order:
    - Read         # AGENTS.md first
    - Read         # task
    - Edit         # implementation
    - Bash         # test
  tool_calls_must_NOT_include:
    - "git push"   # sandbox: no push allowed
  errors_expected: []
```

## Assertions (tests/skills/lib/assert.sh)

Bash script lê:
- expected.yaml
- subagent report (texto)
- git state via `git -C <sandbox> log --oneline`, `git -C <sandbox> diff --stat`, `git -C <sandbox> branch`
- task file frontmatter via `head -20 <task_file>`

Compara campo por campo, output `PASS` ou `FAIL: <campo>: expected <X> got <Y>`. Exit 0 se tudo verde.

## Decision tree — falhas

```
Subagent estourou quota / timeout:
├─ Fixture demora > 5min → marca SKIP, continua próxima.
│
Subagent retornou texto fora do formato RESULT:
├─ Parsing falha → log o texto, marca FAIL com motivo "report format".
│
Git state assertion falha:
├─ Anota diff entre expected e actual, marca FAIL.
├─ NÃO faz teardown (preserva sandbox pra inspeção manual).
│
Task.md frontmatter ainda em "todo" no fim:
├─ Subagent não cumpriu o ciclo. FAIL: "task not advanced".
│
Tool call sequence violou must_include_in_order:
├─ FAIL: "trajectory: missed <X> before <Y>".
```

## Hard rules

- **Nunca executa contra repo real** — sempre sandbox em `/tmp/test-*/`.
- **Nunca commitar resultados de teste** no guidelines_IA — `tests/skills/.last-run/` está em `.gitignore`.
- **Nunca chama API direto** (`curl https://api.anthropic.com/...`) — sempre `Agent` tool.
- **Idempotent**: rodar duas vezes seguidas deve dar mesmo resultado (teardown completo).
- **Subagent é isolado**: cada fixture spawna 1 subagent novo, sem leak de contexto entre fixtures.

## Output format ao final

```
META-TEST run @ <timestamp>
=============================
fixture                          skill    pass   duration   notes
001-trivial-readme-edit          builder  ✅     42s        —
002-failing-test-regression      builder  ❌     31s        Tests: did not stop at red
003-files-afetados-drift         builder  ✅     58s        Updated §Arquivos Afetados (1 commit extra OK)
004-lock-conflict-parallel       builder  SKIP   —          multi_agent: false in fixture AGENTS.md
005-push-blocked                 builder  ✅     38s        Reported branch local, no push

TOTAL: 3 pass / 1 fail / 1 skip out of 5 (60% pass)

Failed details:
  002-failing-test-regression:
    expected.errors_expected: ["task: blocked by fix/<NNNN>-broke-by-builder"]
    actual.errors_encountered: []
    → subagent did not detect the broken pre-existing test
```

## Anti-patterns

- ❌ Fixture que assume estado de outro fixture (cross-contamination).
- ❌ Assertions sobre stdout do subagent texto (frágil) — usar git state + task.md.
- ❌ Spawnar subagent sem sandbox (vai modificar repo real).
- ❌ `tool_calls_must_include` muito específico (ex: "Bash com argumento exato X") — quebra com refactor do SKILL.md sem ganho.

## Roadmap de fixtures

| Fixture | Cobre | Status |
|---|---|---|
| `001-trivial-readme-edit` | happy path mais simples — edita 1 arquivo, 1 commit | ✅ baseline (smoke + e2e validated 2026-05-21) |
| `002-failing-test-regression` | trap: test pre-existente quebra durante implementação — Builder deve STOP + criar fix-task + blocked_by | ✅ smoke validated 2026-05-22 |
| `003-files-afetados-drift` | trap: §O Que Fazer precisa de arquivo fora de §Arquivos Afetados — Builder atualiza contrato primeiro | ✅ smoke validated 2026-05-22 |
| `004-never-delete-archive-instead` | trap: task pede "remover" mas AGENTS §2 proíbe delete — Builder usa `mv .archive/` | ✅ smoke validated 2026-05-22 |
| `005-lock-conflict-parallel` | trap: 3 subagents, 1 lock conflict resolvido (parallelism via Agent tool) | TODO — exige instrumentação extra |
| `006-tester-prototype-mode` | tester skill, boots-and-responds | TODO (após tester upgrade) |
| `007-notifier-clickup-comment` | notifier skill, post comment com TL;DR | TODO (após notifier upgrade) |

## Como adicionar fixture

1. `mkdir tests/skills/fixtures/<NNN>-<slug>/`
2. Criar `seed-repo.tar.gz` com mini-repo (5-15 arquivos máx — pequeno é importante)
3. Criar `task-id.txt`, `skill.txt`, `expected.yaml`, `README.md`
4. Roda `/test-builder` localmente; verifica que passa
5. Commit + PR
