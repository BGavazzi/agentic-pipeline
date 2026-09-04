# Prototype template — Diamante 1 bootstrap

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor
> deste (`guidelines_IA`, tombstoned). Fluxo de bootstrap reescrito: onde o
> original usava `git subtree`/`dist/core` (mecanismo específico de
> `guidelines_IA`), aqui usa-se [`core_sync.py`](../README.md#quick-start),
> que já existe neste repo pra exatamente esse fim — vendorar skills/scripts
> num repo alvo. `.template/` continua tendo um papel complementar: o
> bootstrap de um repo **novo do zero** (README/CHANGELOG/PRD/gitignore
> iniciais), que `core_sync.py` deliberadamente não cobre.

Esqueleto **minimal** pra um repo novo de protótipo. Vive em `agentic-pipeline/.template/` como referência.

## O que tem aqui

```
.template/
├─ README.md                    ← este arquivo (instruções)
├─ AGENTS.md                    ← já preenchido com defaults sane pra protótipo
├─ CHANGELOG.md                 ← cabeçalho vazio pronto pra primeira entry
├─ .gitignore                   ← Node + Python + IDE comum + segredos
└─ .docs/
   └─ PRD.md                    ← template PRD vazio
```

(O template de task fica em `.docs/tasks/000-template.md` na raiz deste repo — não duplicado aqui; `core_sync.py` não copia `.docs/tasks/`, então copie esse arquivo manualmente na primeira task do protótipo, ou aponte pra ele.)

## Como usar — bootstrap de um Diamante 1

```bash
# 1. Repo novo, vazio
mkdir <slug> && cd <slug> && git init

# 2. Esqueleto deste template
cp -r <path-to-agentic-pipeline>/.template/* .
cp -r <path-to-agentic-pipeline>/.template/.docs/* .docs/
cp <path-to-agentic-pipeline>/.template/.gitignore .

# 3. Core: skills + gate scripts + conventions + AGENTS.md
python <path-to-agentic-pipeline>/scripts/core_sync.py .
# core_sync.py NÃO sobrescreve o AGENTS.md que veio do .template/ acima
# (só cria um se o alvo não tiver nenhum) — a ordem 2 → 3 importa.

# 4. Editar AGENTS.md substituindo <placeholders> por valores reais
#    (project_name, version, stack)

# 5. Primeira task
cp <path-to-agentic-pipeline>/.docs/tasks/000-template.md .docs/tasks/0001-....md
# editar, preencher §What To Do e §Exit Conditions

git add -A && git commit -m "chore: bootstrap from prototype template"
gh repo create <namespace>/<slug> --source=. --private --push
```

## O que o protótipo herda (via `core_sync.py`)

- Skills do pipeline (`grill-me`, `codebase-grounding`, `builder`, `tester`, `notifier`, e as demais — filtrar com `--skills` se só precisar de algumas)
- Gate scripts (`validate_task.py`, `validate_closure.py`, `blast_radius.py`, `scan_gate.py`, `quota_gate.py`)
- `.docs/conventions/*.md`

## O que NÃO entra na Diamante 1 (lembrete)

Ver [`.docs/strategy/double-diamond-prototype-pipeline.md`](../.docs/strategy/double-diamond-prototype-pipeline.md) neste repo:
- Integração com auth canônica (mock OK)
- Multi-tenant isolation
- RBAC granular
- Pipeline de dados real (clusters, allocations)
- Observabilidade plena
- Migrations reversíveis
- Soft delete consistente

Tudo isso vive na Diamante 2 (após o gate humano).

## Critério de saída da Diamante 1

- [ ] README do protótipo (1 parágrafo demo)
- [ ] `docker compose up` ou equivalente roda local
- [ ] `.docs/PRD.md` preenchido
- [ ] Screenshots/GIF do happy path
- [ ] Tests do happy path passando
- [ ] Link de preview / domínio temporário
