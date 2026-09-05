# AGENTS.md — Por que colapsamos a matriz de variantes (pass Opus 4.8)

> **TL;DR**: existiam 6 variantes do `AGENTS.md` (Opus 4.7 × Sonnet 4.6, em minimal/balanced/full/verbose) porque os dois Opus tinham pontos ótimos diferentes e o Sonnet precisava de mais explicitude. **Opus 4.8 apaga essa razão.** Há um único Opus (mais capaz **e** com `/fast`), e o harness do Claude Code passou a cumprir nativamente várias regras que as variantes repetiam. Restaram **duas** variantes por **tamanho** (não por modelo): `AGENTS.balanced.md` (completa) e `AGENTS.minimal.md` (enxuta), mais a `AGENTS.opus48.balanced.md` (balanced sem o que o harness já cobre). As 6 antigas foram para `.archive/agents-variants-pre-opus48/`.

Este arquivo era a análise empírica que justificava a matriz por-modelo. A análise está obsoleta; fica aqui só o registro do **porquê** e o que sobrou de acionável.

> **Nota de proveniência (migração 2026-09).** Registro histórico da
> consolidação pré-Opus 4.8 → Opus 4.8, migrado como está de `guidelines_IA`.
> Desde então o Opus 4.8 também foi sucedido — o valor deste arquivo não é
> "o Opus 4.8 é o Opus atual", é o **padrão de raciocínio** (menos variantes
> por-modelo, mais harness-native) que se repete a cada geração.

---

## O que mudou

| Antes (pré-4.8) | Agora (Opus 4.8) |
|---|---|
| **Dois Opus**: 4.6 "para planejar" (tinha `/fast`) × 4.7 "para review" (mais capaz, sem fast) | **Um Opus**: 4.8 é o mais capaz **e** tem `/fast`. A dicotomia some. |
| **Sonnet 4.6** precisava de enumeração explícita + marcadores de severidade → variante própria mais verbosa | Continua sendo o workhorse, mas não justifica um `AGENTS.md` próprio. |
| Regras repetidas em cada variante: "nunca commit/push sem autorização", "respostas tersas", "verificar estado antes de ação irreversível", "não comentar o óbvio" | **Cumpridas nativamente pelo harness** — repeti-las só gasta contexto. Ver cabeçalho de [`AGENTS.opus48.balanced.md`](AGENTS.opus48.balanced.md). |
| 6 arquivos (`opus47.*`, `sonnet46.*`) | 2 por tamanho (`balanced`, `minimal`) + `opus48.balanced`. As 6 → `.archive/`. |

## O que continua verdadeiro (independe do modelo)

O insight original sobre **o que cortar de um `AGENTS.md`** sobrevive — só deixou de ser por-modelo:

- **Manter** (não-derivável): dados do projeto (versões, IDs, paths), regras invertidas (`nunca deletar → .archive/`, `jj` sobre `git`), e protocolos com ordem/side-effects (Protocolo Zero, Lei de Fechamento).
- **Cortar** (cerimônia ou harness-native): cabeçalhos "ALERTA DO SISTEMA", parentéticos decorativos, e qualquer regra que o harness já cumpre (commit/push, terseness, verificação antes de ação irreversível, não comentar o óbvio).

## Origem deste registro

Pass de redundância contra Opus 4.8 sobre o repo inteiro (191 arquivos, um subagente por arquivo). Dois tipos de redundância encontrados: **(A)** instruções já cumpridas nativamente pelo harness; **(B)** framing de modelo superado pelo fim dos dois-Opus. Detalhe do método e dos cortes no `CHANGELOG.md`.
