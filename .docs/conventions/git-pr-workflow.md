# Convenção — fluxo Git / PR (org-wide)

Leis de versionamento e pull-request válidas em **todos** os repos da org. Referenciado pelo §2 Hard Rules das constituições (`AGENTS.balanced.md`, `.template/AGENTS.md`, `dist/core/AGENTS.template.md`).

> Origem: lições reais de produção (mai–jun/2026), promovidas de memória pessoal para a constituição porque são leis de engenharia, não preferências de uma pessoa.

---

## 1. 🔒 Nunca reciclar um PR

O PR é uma **unidade de merge limpa, completa e correta**. Se um PR está errado, incompleto ou precisa ser refeito → **abrir um PR NOVO** contendo **tudo que precisa dar merge**, e **fechar o PR anterior errado**.

**NÃO:**
- empilhar commits de fixup num PR torto pra tentar consertá-lo;
- dar `git merge origin/main` de volta na branch do PR pra resolver conflito e "salvar" o PR;
- reaproveitar uma branch/PR aberta pra propósito diferente do original.

**Resolver conflito:** rebasear a branch em cima da `origin/main` atual (ou, se já sujo, branch nova rebaseada + PR novo). **Nunca** `merge origin/main` dentro da branch do PR.

**Why:** reutilizar PR suja histórico e review, mistura o errado com o certo, deixa a unidade-de-merge ambígua. Um PR fresco com o diff completo é fácil de revisar e mergear; o errado simplesmente fecha. Gatilho: um `merge origin/main` numa branch de PR ao tentar "resolver conflito".

Não confundir com **iteração normal de review** (responder comentário num PR vivo é OK). O foco é PR **errado/refeito** — esse não se recicla.

---

## 2. Checar merge ANTES de empilhar commit

Antes de `git push` numa branch de feature que já tem PR, **checar o estado do PR**:

```bash
gh pr view <n> --json state,mergedAt
# ou
gh pr list --head <branch> --state all
```

Se **MERGED/CLOSED**: criar **branch novo a partir da `origin/main` atual** e abrir **PR novo** — nunca reusar branch já mergeada.

```bash
git -c credential.helper='!gh auth git-credential' fetch origin main
git checkout -b <novo> origin/main
git cherry-pick <commits órfãos>   # se houver
```

Detectar commits órfãos (no branch, fora da main, sem PR): `git log origin/main..HEAD`.

**Why:** empilhar fix atrás de fix numa branch já mergeada deixa os commits órfãos — no branch, fora da main, sem review. (Flagrado 2026-06-01 no `feat/event-importer-iv-forum` após o #1278 ter mergeado.)

---

## 3. Topologia de branch e base do PR

Em repos **com deploy automático** (staging dispara em `push→main`, prod em `push de tag`) a base do PR é **`integration`**, não `main`:

- **`integration`** = branch de junção. **PRs de feature miram `integration`.** Push aqui **não dispara build nenhum** (não há gatilho `pull_request` nem deploy em branch ≠ main).
- **`main`** = espelho do homolog. Todo push **deploya staging**. Recebe **merge em lote** da `integration` (`git merge --no-ff integration` → 1 build), **não** PRs avulsos.
- **tags** (`*`) = release de prod, **100% imediato**. Cortadas da `main`, ou de um commit específico p/ hotfix isolado.

Repos **sem deploy** (docs/tooling como `guidelines_IA`, libs) continuam com base = **`main`** direto (não master/develop/staging).

Fluxo: `feat/x` (da `integration`) → PR p/ `integration` → build local (§6) → merge → … → lote pronto → `merge integration→main` (1 build de staging) → testa homolog → `tag` (deploy prod).

**Why:** cada merge em `main` = 1 build de staging pago; PRs avulsos na main multiplicam build **e** fazem a main acumular o trabalho de vários times entre a sua feature e o release → força cherry-pick ou release-cheia (todo o homolog vai junto). A `integration` batela (9 features = 1 build), mantém a `main` sempre num estado "pode taggear agora", e isola o que vai pra prod.

---

## 4. PR aprovado fecha a task (Lei de Fechamento §3, item 8)

Uma task que gera código **só fecha** (`status: done` + mover pra `completed/`) quando o **PR está aprovado** (review approved). O ciclo de vida:

```
task todo → in_progress → (código + PR aberto) → in_progress/review → PR aprovado → done + completed/
                                                  ^ NÃO é done aqui
```

- PR **apenas aberto/pushado não fecha a task** — ela fica `in_progress` (em review) até a aprovação humana.
- Fechar a task na abertura do PR, ou mergear sem aprovação, **viola** a Lei de Fechamento.
- Checagem antes de fechar: `gh pr view <n> --json reviewDecision` → fecha só se `APPROVED`.
- Task sem código (doc puro / chore sem PR) fecha pelos itens 1-7 da §3, sem item 8.

**Implicação pro dispatcher** (e qualquer loop autônomo): NÃO mover a task pra `completed/` ao abrir o PR. Deixar `in_progress` e reportar "aguardando aprovação". O flip pra `done` acontece depois que um humano aprova (passo manual ou um watcher futuro).

**Why:** PR aberto ≠ trabalho aceito. Fechar na abertura marca como pronto algo que pode voltar no review; quebra o rastreio de "o que de fato entrou".

---

## 5. Disciplina geral

- **Branch novo da `integration` fresca** (ou `main` em repos sem deploy) pra cada unidade de trabalho — fetch antes (helper `'!gh auth git-credential'` evita o hang de credencial AFK).
- Mensagem de commit factual; sem `--no-verify` / bypass de hooks sem autorização explícita.
- Push e merge **só quando o user pedir**. O agente abre PR; humano revisa/mergeia no GitHub.

---

## 6. Build local antes do CI

Validar **local** antes de empurrar — é de graça e pega a maioria das quebras de CI (tipo/compilação) sem gastar runner:

- **NestJS / backend:** `npm run build` (nest build); stack completa com banco: `docker compose -f docker-compose.dev.yml up`; ou `npm run start:dev`.
- **Next.js / frontend:** `npm run build` (next build); rodar a tela: `npm run dev` (usa `.env.local`).

Se `npm run build` passa local, o build do CI quase nunca quebra — e dá pra clicar na tela sem subir no homolog.

**Custo de cada gatilho de git** (por isso build local + base `integration`):

| Evento | Dispara | Custo |
|---|---|---|
| PR (qualquer alvo) | nada (sem gatilho `pull_request`) | **zero** |
| push em `integration` / qualquer branch ≠ `main` | nada | **zero** |
| push/merge em **`main`** | build + deploy **staging** | 1 build |
| push de **tag** (`*`) | build + deploy **prod** (100% imediato) | 1 build |

**Why:** o gasto de CI mora em push→`main` e tag, não em PR. Batelar na `integration` e validar local antes corta build desperdiçado e a maioria dos vermelhos de pipeline.
