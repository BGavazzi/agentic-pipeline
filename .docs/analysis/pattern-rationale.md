# Padrões identificados — de onde vem a doutrina deste repo

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor
> deste (`guidelines_IA`, tombstoned), onde era um survey cross-repo dos
> padrões observados em produção antes de serem canonizados aqui. Citações de
> quais repos específicos exibiam cada padrão foram removidas (não são
> portáveis nem necessárias — o padrão em si é o que importa); alguns itens
> (P-04 file-lock ledger, P-05 `jj`, P-09 rich commentary) descrevem
> convenções que **não foram** adotadas neste repo ainda — ficam registradas
> como candidatas, não como o que já existe.

Padrões observados no ecossistema original, com avaliação (vale canonizar? vale matar?) e formato canônico proposto. A canonização aqui significa: o padrão entra na doutrina deste repo como **regra obrigatória** ou **regra opcional**, e a justificativa fica registrada para que ninguém precise re-decidir depois.

---

## P-01 · Constituição local em `AGENTS.md` (status: **canonizado**)

**Resumo do padrão**: cada repo tem `AGENTS.md` na raiz como "máxima fonte de verdade" para agentes. Frequentemente reforçado por `CLAUDE.md`, `.cursorrules` e `.windsurfrules` que apontam de volta para ele — o que é redundante se cada um duplica conteúdo em vez de só redirecionar (ver P-02).

**Por que canonizar**: é o fundamento do ecossistema. Sem ele, o agente entra sem contexto e começa a desviar. Toda ferramenta de agente moderna lê `AGENTS.md` automaticamente. **Status neste repo: `AGENTS.md` é a fonte canônica**, ver `AGENTS.balanced.md`/`AGENTS.minimal.md`.

---

## P-02 · Pointer files (`CLAUDE.md`, `.cursorrules`, `.windsurfrules`) (status: **canonizar mas reduzir**)

**Resumo do padrão**: ferramentas de agente diferentes leem arquivos diferentes por convenção. Apontar de cada um deles para `AGENTS.md` evita drift entre ferramentas.

**Por que reduzir**: o conteúdo deveria ser **um redirecionamento de 5 linhas**, não uma duplicação parcial de regras. Repetir partes do `AGENTS.md` em cada pointer cria múltiplas fontes de verdade que se desincronizam.

**Forma canônica proposta** (idêntica em todos os pointer files):

```markdown
# STOP AND READ

You are operating within the **<project>** project.

The single source of truth for agent behavior in this repository is **`AGENTS.md`** at the root.
Read it in full before any other action. Do not rely on the abbreviated rules below if they conflict with `AGENTS.md`.

(Optional 3-5 line summary, only as a fast-glance preview, not as a replacement.)
```

---

## P-03 · Protocolo Zero (Continuity Ledger) (status: **canonizado**)

**Resumo do padrão**: antes de qualquer ação, o agente lê `.agents/continuity-<agentname>.md`, alinha com o foco descrito, e atualiza no fim da sessão. Já é `AGENTS.md` §0 neste repo.

**Por que canonizar**: é a forma mais barata em tokens de manter coerência entre sessões. Custa ~200-500 tokens por handoff e evita retrabalho que custa milhares.

**Schema interno sugerido** (padronizar o formato, hoje varia por repo):

```markdown
# Continuity Ledger — <agente> (<repo>)

## Foco Atual
Uma frase descrevendo o que o agente está fazendo agora.

## Estado dos Testes / Build
- Tests: <passing | N failing | not run>
- Build: <green | broken | n/a>

## Última sessão (data)
- Mudanças aplicadas: <bullets>
- Decisões tomadas: <bullets>
- Bloqueios: <bullets ou "nenhum">

## Próximo Passo
Uma frase descrevendo o que deve ser feito a seguir.

## Arquivos Críticos Tocados
- <path>: <razão>
```

---

## P-04 · File-Lock Ledger (status: **candidato — canonizar onde houver paralelismo real**, não adotado ainda)

**Resumo do padrão**: `.agents/file-locks.md` registra `| arquivo | agente | timestamp | tarefa |`. Antes de editar, agente verifica e adiciona; ao terminar, remove.

**Avaliação honesta**: útil quando há 2+ agentes simultâneos. Cerimônia desnecessária quando há um agente por vez. Recomendação: **canonizar como opcional**, ativado por flag no `AGENTS.md` (`multi_agent: true`). Caso contrário, **não obrigar**.

**Alternativa mais barata para single-agent**: confiar no VCS. Um VCS com revisões isoladas nativamente (ex: Jujutsu/`jj`) faz isso de graça — o lock-ledger é cinto-suspensório.

---

## P-05 · VCS com revisões isoladas como mutação primária (status: **candidato**, não adotado neste repo — usa `git` puro)

**Resumo do padrão**: preferir um VCS que trata conflitos como first-class state e permite múltiplos agentes em revisões isoladas (ex: Jujutsu/`jj`, "usar se disponível, senão git"), sobre `git` puro que serializa mutações via `.git/index`.

**Por que é candidato**: elimina race em `.git/index`, e permite múltiplos agentes trabalhando em paralelo sem lock-ledger manual (ver P-04). A regra hard-coded de não fazer push/commit sem autorização complementa bem.

**Status real**: nenhum script deste repo (`builder`, `dispatcher`, etc.) assume `jj` — todos assumem `git`. Registrado aqui como direção possível, não como algo a instalar.

---

## P-06 · Lei de Fechamento de Tarefa / Closure Law (status: **canonizado — é o coração do sistema**)

**Resumo**: tarefa só fecha quando **todos** os artefatos de doc estão atualizados — já é `AGENTS.md` §3 + `scripts/validate_closure.py` neste repo.

| Artefato | Sempre? | Quando aplicar |
|---|---|---|
| `CHANGELOG.md` | ✅ Sempre | Toda mudança |
| `function-catalog.md` | ✅ Sempre | Mudança de assinatura/signature |
| `SDD_KIT.md` | Condicional | Nova decisão arquitetural → flag `Dxx` |
| `README.md` | Condicional | Mudança visível ao usuário |
| `.agents/continuity-*.md` | ✅ Sempre | Estado de handover |
| Testes passando | ✅ Sempre | Sem exceção |
| `ROUTE_BEHAVIOR_MAP.md` | Condicional | Rota/handler alterado |

**Por que é o coração**: é a única regra que força sincronização entre código, specs e docs. **Sem ela, a documentação envelhece em horas.**

---

## P-07 · Convenção de numeração de tarefas `nnnn` (status: **canonizado**)

**Resumo do padrão**: formato `NNNN-tipo-slug.md`, `NNNN` = 4 dígitos cronológicos. Já é `AGENTS.md` §4.1 neste repo, validado por `scripts/validate_task.py`.

**Por que canonizar**: dá ordering total estável. Permite que o agente saiba sem ler o conteúdo se uma tarefa é nova ou antiga.

**Pegadinha conhecida** (do original): colisões de número acontecem quando dois branches criam a mesma task ID em paralelo sem coordenar. Sugestão: validador que rejeita colisões antes do merge.

---

## P-08 · Decisões Arquiteturais como Flags `Dxx` (SDD) (status: **candidato**, referenciado mas não implementado neste repo)

**Resumo**: cada decisão arquitetural recebe um ID curto (`D11`, `D22`), uma linha de rationale, e o(s) arquivo(s) onde foi implementada. O **código referencia a flag** em comentário (`# D07: retry com backoff exponencial`).

**Por que canonizar**: é o que torna um `SDD_KIT.md` *vivo*. Sem o backreference no código, o SDD vira tijolo morto.

**Sugestão**: regra de que toda mudança em arquivo listado em uma decisão deve manter o comentário `# Dxx:` se ele já existir, ou adicionar se for nova decisão. Um CI hook simples (`grep -r "# D[0-9]\+:" src/`) confirma que todas as flags ativas do SDD ainda existem no código.

---

## P-09 · Rich Commentary inline (`# CONTRACT:`, `# SYNC:`, `# Dxx:`, `# [agente | data]`) (status: **candidato**, não adotado neste repo)

**Resumo**: comentários com função semântica explícita:

| Tag | Função |
|---|---|
| `# CONTRACT:` | Contrato de interface — o que o caller pode esperar |
| `# Dxx:` | Referência a decisão arquitetural |
| `# SYNC:` | "Mexer aqui implica mexer em X" — interdependência cross-arquivo |
| `# [agente \| data] descrição` | Auditoria — quem/quando/por quê |
| `# TODO(<agente>): ...` | Pendência rastreável com responsável |

**Por que canonizar**: em ambiente multi-agente, código é a interface entre agentes. Esses tags são parseable (`grep -r "# CONTRACT:"`) e geram artefatos automatizáveis (function-catalog).

---

## P-10 · `.archive/` em vez de `rm` (status: **canonizado**)

**Resumo**: nunca deletar; mover para `.archive/` mantendo estrutura de diretórios. Já é `AGENTS.md` §2 hard rule neste repo.

**Sugestão de canonização** (ainda não implementada): `.archive/` deve ser **ignorado por padrão** no `.gitignore`, mas com um `.archive/INDEX.md` versionado que lista o que foi arquivado e por quê. Assim ninguém perde o registro do que existiu, sem inflar o histórico.

---

## P-11 · GDFRSBT como doutrina de desenvolvimento (status: **canonizado como referência**)

**Avaliação**: o framework é bom, mas **referenciar é melhor que repetir**. Já é assim neste repo: `GDFRSBT.md` vive num lugar só na raiz, e `AGENTS.md`/`README.md` apenas referenciam em vez de reexplicar a tabela de 8 estágios inline.

**Anti-padrão a evitar**: reexplicar a tabela GDFRSBT inline em cada `AGENTS.md` de repo satélite — duplica ~30 linhas por repo à toa. Reduzir para uma única linha de pointer economiza tokens em cada sessão.

---

## P-12 · Variantes de `AGENTS.md` por tamanho (status: **canonizado**)

**Avaliação honesta**: medir o trade-off entre variantes é trabalho que vale a pena fazer explicitamente e documentar (ver `AGENTS.assessment.md`), não deixar implícito.

**Recomendação concreta, já aplicada neste repo**:
- **2 variantes de tamanho**: `AGENTS.balanced.md` (default) e `AGENTS.minimal.md` (bolso).
- O eixo relevante é **tamanho**, não tier de modelo: o `balanced` cabe em qualquer modelo moderno; a diferença está no estilo de prompt do usuário, não na constituição do projeto.
- Variantes por-modelo antigas vão para `.archive/` quando o modelo que as motivou é sucedido — ver `AGENTS.assessment.md` para o histórico dessa consolidação.
- Manter `MODEL-SELECTION.guidelines.md` separado — esse eixo (qual modelo pra qual tarefa) é genuinamente ortogonal ao tamanho do `AGENTS.md`.

**Justificativa**: o ganho de tokens entre `balanced` (~90 linhas) e variantes maiores é marginal — irrelevante comparado ao custo de o time não saber qual usar.

---

## Síntese: seções que compõem um `AGENTS.md` canônico

Sequência canônica das seções (já a estrutura de `AGENTS.balanced.md`/`AGENTS.minimal.md` neste repo):

1. Cabeçalho (identidade + versão + status)
2. § 0 — Protocolo Zero (P-03)
3. § 1 — Identidade & escopo + stack
4. § 2 — Hard rules (nunca deletar + segredos + `.archive/`)
5. § 3 — Lei de Fechamento (P-06)
6. § 4 — Tarefas (P-07 + checklist Lei de Fechamento)
7. § 5 — Estilo
8. (Candidatos ainda não adotados: VCS rules/P-05, anti-colisão/P-04, rich commentary/P-09, catálogo de agentes auto-gerado)
9. Footer — pointers para `MODEL-SELECTION.guidelines.md`, `GDFRSBT.md`, `SDD_KIT.md` (quando existir)
