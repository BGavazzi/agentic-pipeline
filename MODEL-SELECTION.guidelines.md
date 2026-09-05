# Guia de Seleção de Modelo — Claude

Como decidir entre **Opus 5**, **Sonnet 5** e **Haiku 4.5** para cada tipo de tarefa.

> **Princípio**: cada modelo tem um ponto ótimo. Usar Opus em tarefa mundana é desperdício; usar Haiku em planejamento é risco. Decida pela **natureza cognitiva da tarefa**, não pelo "vou usar o melhor que eu tiver".

> **Mudança desde a versão anterior deste guia.** Opus 5 é o único Opus — mais capaz e com `/fast` (usa Opus com saída mais rápida, sem rebaixar para modelo menor).

---

## 1. Mapa rápido por tipo de tarefa

| Tarefa | Modelo | Motivo |
|---|---|---|
| **Planejamento de feature/arquitetura** | **Opus 5** | Raciocínio profundo; `/fast` entrega o plano rápido sem perder qualidade |
| **Implementação de código (80% do dia)** | **Sonnet 5** | Workhorse — bom o suficiente, custo razoável, baixa latência |
| **Code review / segurança / refactor crítico** | **Opus 5** | Pega correlações sutis cross-arquivo; custo do falso negativo >> custo do modelo |
| **Debug de bug intermitente / race condition** | **Opus 5** | Hipóteses paralelas, leitura cuidadosa de stack traces |
| **Revisão final antes de PR/deploy** | **Opus 5** | Última linha de defesa antes de prod |
| **Geração de docs a partir do código** | **Sonnet 5** | Mecânico mas precisa de contexto — Sonnet acerta o tom |
| **Pair programming exploratório** | **Sonnet 5** | Melhor latência mantém o flow |
| **Tarefas mundanas** (listar, transcrever, qual comando, qual flag) | **Haiku 4.5** | Resposta em segundos, custo trivial |
| **Conversão/transcrição de formatos** | **Haiku 4.5** | Tarefa textual pura, sem julgamento |

**IDs exatos**: Opus 5 = `claude-opus-5` · Sonnet 5 = `claude-sonnet-5` · Haiku 4.5 = `claude-haiku-4-5-20251001`.

---

## 2. Por modelo — quando cada um brilha

### 2.1 Opus 5 — Planejamento, review e tudo que erra caro
**Use para:**
- Quebrar épico em tarefas (`.docs/tasks/nnnn-*.md`), decisões de arquitetura, ADRs/RFCs, trade-offs entre 2+ abordagens.
- Code review pré-merge, `/security-review`, auditoria de VCS/auth/billing/migrations.
- Debug que já consumiu >30min, refactor que toca >5 arquivos com lógica entrelaçada, postmortem.
- Revisão final antes de merge/deploy crítico.

**Por quê (vs Sonnet):** pega correlações sutis entre arquivos que Sonnet perde; em planejamento e review, o custo de errar (plano superficial, bug que passa) supera de longe o custo do modelo.

**`/fast`:** quando quiser o raciocínio do Opus com latência menor (planejamento iterativo, "esboce → critique → refine"). Não rebaixa o modelo — é o mesmo Opus, saída acelerada.

**Não use para:** boilerplate, rascunhos descartáveis, tarefas onde você joga fora 80% da saída.

### 2.2 Sonnet 5 — Implementação geral (o workhorse)
**Use para:** implementar feature já planejada, testes unitários, refactors mecânicos, bug com causa identificada, atualizar deps, boilerplate (rotas, models, components).

**Por quê (vs Opus):** ~80% do trabalho de código não precisa de reasoning profundo. Latência menor = mais iterações/hora = mais flow. Custo muito menor — dá pra rodar mais agentes em paralelo.

**Não use para:** decisão arquitetural nova ou review final crítica (suba pro Opus 5).

### 2.3 Haiku 4.5 — Mundano
**Use para:** "qual o comando/flag pra X?", listar/filtrar conteúdo existente, transcrição, conversão de formato, resumir log longo, rename em massa por padrão claro, commit message a partir de diff, tradução técnica direta.

**Por quê:** resposta em 1-3s vs 10-30s do Sonnet; custo trivial (use 100x sem pensar); não-determinismo baixo nessas tarefas — modelo grande não agrega.

**Não use para:** qualquer coisa que envolva julgamento sobre **se** algo deve ser feito (só sobre **como** fazer mecanicamente). Em debug, Haiku confabula causa quando não tem certeza.

---

## 3. Heurísticas de decisão

- **Regra de 30 segundos** — se resolveria em <30s consultando docs/SO → **Haiku**.
- **Regra do reasoning visível** — quer **ver o agente pensar** (alternativas, trade-offs, "isso quebra X") → **Opus**. Quer **ver entregar** (código pronto) → **Sonnet**.
- **Regra do custo do erro** — erro custa minutos de retrabalho → Sonnet ok. Erro custa horas de debug ou afeta prod → **Opus**. Erro é trivial e auto-evidente → Haiku.
- **Regra do paralelismo** — tarefas independentes em paralelo (3+ agentes) → Sonnet ou Haiku. Opus em paralelo queima budget rápido sem ganho proporcional.

---

## 4. Padrões por papel da equipe

### Fullstack
Plan → **Opus 5 (`/fast`)** · Implementação → **Sonnet 5** · Review próprio antes do review humano → **Opus 5** · Comando/flag/SDK lookup → **Haiku 4.5**.

### Frontend
Discovery de component lib / a11y → **Opus 5** · Implementação de componente → **Sonnet 5** · Review de bundle/perf → **Opus 5** · "Como faz X em Tailwind/CSS" → **Haiku 4.5**.

### Vibe coder
Default **Sonnet 5** para implementação, **Opus 5** para qualquer coisa nova ("o que é X", "como abordar Y"). **Sempre passe pelo Opus 5 antes de commit grande** — segunda opinião. Haiku pra digitar comando ou listar coisa.

### UX Designer
Brainstorm de fluxo / IA / copy → **Opus 5** · Variações de microtexto → **Haiku 4.5** (rápido, barato, varia bem) · Review de copy/tom → **Sonnet 5** · Síntese de research/entrevistas → **Opus 5**.

---

## 5. Anti-padrões comuns

- ❌ **Usar Opus pra tudo "porque é o melhor"** — queima budget, atrasa iteração.
- ❌ **Usar Sonnet pra planejar arquitetura nova** — sai plano superficial que você vai refazer.
- ❌ **Usar Haiku pra debug** — confabula causa quando incerto; te leva pra direção errada por 20min.
- ❌ **Trocar de modelo no meio da tarefa sem motivo** — perde contexto, invalida cache, retrabalho.
- ❌ **Não usar Haiku porque "parece simples demais"** — é exatamente onde Haiku ganha.

---

## 6. Custos e tokens

> **Aviso**: preços mudam. Confirme em [anthropic.com/pricing](https://www.anthropic.com/pricing) antes de orçar. Números abaixo são aproximações para decisão, não faturamento. Opus 5 fica na faixa de preço padrão Opus.

### 6.1 Tabela de preços por 1M tokens (USD, aproximado)

| Modelo | Input | Output | Cache write (5min) | Cache read | Velocidade |
|---|---:|---:|---:|---:|---|
| **Haiku 4.5** | ~$1 | ~$5 | ~$1.25 | ~$0.10 | ⚡⚡⚡ |
| **Sonnet 5** | ~$3 | ~$15 | ~$3.75 | ~$0.30 | ⚡⚡ |
| **Opus 5** (`/fast` ou normal) | ~$15 | ~$75 | ~$18.75 | ~$1.50 | ⚡⚡ |

**Razões úteis de decorar:**
- **Output custa ~5x input** em todos os modelos → seja terso na resposta esperada.
- **Opus custa ~15x Haiku** e **~5x Sonnet** → use só quando o ganho justifica.
- **Cache read custa ~10% do input** → reaproveitar contexto é praticamente grátis.

### 6.2 Input vs output tokens — por que importa

A maioria dos devs subestima output e superestima input.

| Dimensão | Input | Output |
|---|---|---|
| Custo unitário | ~1x | ~5x |
| Velocidade | Paralelo, rápido | Token a token, lento |
| Limite prático | Janela do modelo (200K–1M) | ~8K–64K por resposta |
| O que economizar | Pouco — input é barato | **Muito** — output é caro **e** lento |

**Implicações:**
- ✅ **Não tenha medo de contexto longo.** Anexar bastante código custa pouco se cabe na janela.
- ✅ **Peça respostas concisas.** *"Responda em 3 linhas"* corta ~80% do custo de output.
- ❌ **Não corte código do prompt pra "economizar"** — são tokens de input baratos; o tempo cortando vale mais.

### 6.3 Prompt caching — o multiplicador esquecido

Cache hit reduz input em ~90%. Em sessão longa com mesmo system prompt + `AGENTS.md`, do 2º turno em diante ~90% do input vira cache read.

- **Claude Code**: cache ativo automaticamente. **TTL padrão 5 min** — se a sessão pausar mais que isso, o próximo turno paga input cheio.
- **SDK**: `cache_control: { type: "ephemeral" }` em mensagens estáveis.
- **Trocar de modelo invalida o cache** → primeira mensagem do novo modelo paga input cheio.

### 6.4 Custo relativo (heurística mental)

| Modelo | Custo relativo | Quando vale |
|---|---:|---|
| Haiku 4.5 | **1x** | Tarefa que demoraria <30s manualmente |
| Sonnet 5 | **~3x** | 80% do trabalho de código |
| Opus 5 | **~15x** | Decisão ou review onde erro custa horas |

> Pergunta-chave: *"essa tarefa vale 15x o custo do Haiku?"* Se "talvez não", desça de modelo.

---

## 7. Thinking / reasoning estendido

Claude 4 raciocina antes da resposta final em tarefas complexas; esses tokens são cobrados como **output**.

> O harness gerencia o esforço de raciocínio automaticamente; `think hard` / `ultrathink` no prompt são nudges suaves (pedido de mais cuidado, não um budget garantido). No SDK/API o controle explícito continua via `thinking: { type: "enabled", budget_tokens: N }`.

**Vale mais deliberação (peça, ou deixe o Opus 5 fazer):**
- ✅ Planejamento de feature nova · debug intermitente / race · refactor cross-file >5 arquivos · security review / auth / migration · decisão arquitetural com 3+ alternativas · code review final pré-merge.

**Não precisa:**
- ❌ Lookup de comando/flag · boilerplate (CRUD, rotas, DTOs) · tradução/transcrição/conversão · aplicar patch já decidido · iteração visual de CSS.

**Custo:** tokens de thinking = output (multiplicador ~5x). Reserve deliberação pesada para Opus 5 no que realmente justifica; em Haiku quase nunca compensa.

---

## 8. Melhores práticas

### 8.1 Economia de tokens
1. **Peça concisão** quando não precisar de explicação — output é o token caro.
2. **Não cole o repo inteiro se 3 arquivos resolvem** — mas não economize cortando o que ajuda o modelo a acertar de primeira.
3. **Reaproveite a sessão** dentro do TTL de cache (5min).
4. **Não troque de modelo no meio da tarefa** sem motivo — invalida cache e quebra contexto.
5. **Use `/compact`** quando o contexto ficar grande.

### 8.2 Qualidade da saída
1. **Modelo certo de primeira** vale mais que economizar. Haiku errando 3x custa mais que Sonnet acertando 1.
2. **Plano antes de código**: peça plano (Opus 5, opcional `/fast`), valide, **depois** implemente (Sonnet).
3. **Defina critério de pronto** no prompt ("pronto quando: tests passam, lint ok, CHANGELOG atualizado").
4. **Anexe o `AGENTS.md` certo** — em Opus 5 use `AGENTS.opus48.balanced.md` (corta o que o harness já cumpre); ver `AGENTS.usage-guidelines.md`.

### 8.3 Workflow cascata (minimiza custo mantendo qualidade)
1. **Haiku 4.5** filtra/lista/extrai dados brutos.
2. **Sonnet 5** transforma e implementa.
3. **Opus 5** revisa antes de aplicar.

Bom para: triagem de bugs, geração + review de migrations, refactor em lote.

### 8.4 Paralelismo
- **Tarefas independentes** → paralelo com **Sonnet** ou **Haiku**. Opus em paralelo queima budget rápido.
- **Sub-agentes** (Agent tool) herdam o modelo do pai — explicite outro modelo se quiser baratear pesquisa.

### 8.5 Higiene de sessão
1. **Sessão por tarefa** — terminou, encerre. Sessões eternas acumulam drift.
2. **Memory para o que persiste entre sessões**, não para o trabalho atual.
3. **Continuity files** (`.agents/continuity-*.md`) carregam contexto entre sessões sem inflar tokens.

### 8.6 Quando suspeitar que o modelo não basta
- Mesmo erro 3x com Sonnet → suba para Opus 5 + peça mais deliberação.
- Resposta sempre superficial mesmo com prompt detalhado → modelo errado, não prompt errado.
- Modelo "concorda com tudo" → peça *"liste 3 razões pelas quais essa abordagem pode falhar"*.

---

## 9. Convenção do time (preencher conforme decisão)

- [ ] Modelo default no Claude Code: `___________`
- [ ] Gatilho explícito para usar Opus 5: `___________`
- [ ] Limite mensal de uso de Opus por dev: `___________`
- [ ] Tarefas que **devem** passar por Opus 5 antes de merge: `___________`
- [ ] Política de cache (sessões longas vs curtas): `___________`
