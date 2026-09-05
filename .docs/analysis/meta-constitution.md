# Meta-AGENTS.md — a constituição acima dos repos individuais

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor
> deste (`guidelines_IA`, tombstoned), onde era proposto como
> `<ecossistema>/AGENTS.md` na raiz de todos os repos de um usuário/org — um
> nível acima do `AGENTS.md` de cada repo individual. Não implementado em
> lugar nenhum ainda; registrado aqui como conceito, não como algo já ativo.
> Nome da pessoa/org genericizado.

Hoje não existe um `AGENTS.md` na raiz do diretório que contém todos os repos de um dado usuário/org — só cada repo individual tem o seu. A proposta original: criar um, com este conteúdo (~30 linhas, ~800 tokens):

````markdown
# AGENTS.md — Ecossistema <nome> (meta-constituição)

> Este é o `AGENTS.md` da raiz do ecossistema. Cada repo tem seu próprio `AGENTS.md` local que **herda implicitamente** as regras aqui e adiciona regras específicas.
>
> Hierarquia: regra local > regra global, exceto onde a regra global declara "não-derrogável" (marcadas com 🔒).

## §0 Identidade e Persona
Você é um agente de software trabalhando no ecossistema de repos de **<maintainer>**.
Ao iniciar uma sessão, escolha um nome de agente baseado na sua ferramenta (ex: `claude-code`, `gemini-cli`, `cursor`) e prossiga — não bloqueie esperando confirmação. Registre a identidade em `<repo>/.agents/continuity-<nome>.md`.

## §1 Cross-repo pointers
- **`MODEL-SELECTION.guidelines.md`** — escolha de modelo por tipo de tarefa.
- **`AGENTS.balanced.md`** — variante default de AGENTS.md por repo.
- **`AGENTS.minimal.md`** — variante mínima para sessões curtas/repos pequenos.
- **`GDFRSBT.md`** — metodologia de desenvolvimento.

## §2 Regras globais (não-derrogáveis 🔒)
1. 🔒 **Nunca delete** arquivos. Mover para `.archive/` do repo. Apenas o usuário pode esvaziar `.archive/`.
2. 🔒 **Nunca commite segredos.** `.env` em `.gitignore`. Verificar antes de qualquer `git add`.
3. **VCS com revisões isoladas se disponível** (ex: `jj`), senão `git`. Apenas leitura sem autorização.

## §3 Convenção de variante padrão
Default do ecossistema: **`AGENTS.balanced.md`** em cada repo.
Trocar para `minimal` apenas em: repos sem código ainda, sessões exploratórias, repos que serão arquivados.
Variantes legadas ficam em `.archive/AGENTS-templates-experimental/` e não devem ser usadas.

## §4 Comportamento sob ambiguidade
Quando a regra local entra em conflito com a regra global não-marcada (sem 🔒): regra local vence.
Quando entra em conflito com 🔒: parar e perguntar ao usuário. Não tente conciliar.
````

## Por que isso não substitui `AGENTS.md` por repo

Um `AGENTS.md` de repo continua sendo a fonte de verdade para *aquele* repo — dados de projeto, stack, hard rules específicas. O meta-constituição só existiria para as **poucas** regras que fazem sentido em todo repo do mesmo mantenedor (persona, pointers cross-repo, o default de qual variante usar) — evita repetir isso em cada `AGENTS.md` individual.

## Status

Conceito, não implementado. Se algum dia adotado, o lugar natural é a raiz do diretório que contém todos os repos de um workspace (ex: `D:\vibes\AGENTS.md` para este ecossistema) — fora de qualquer repo git individual.
