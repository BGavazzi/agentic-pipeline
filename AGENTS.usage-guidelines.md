# Guia de Uso — Variantes do `AGENTS.md`

Como cada papel da equipe escolhe e aplica as variantes do `AGENTS.md`.

> **Princípio**: o `AGENTS.md` que vai ao agente precisa ser do **tamanho certo** — explícito o suficiente pra não dar drift, enxuto o suficiente pra não desperdiçar contexto. Com **Opus 5** a escolha deixou de ser por-modelo (os dois Opus viraram um, e o Sonnet não precisa mais de uma variante própria mais verbosa). A escolha agora é só **tamanho**.

---

## 0. As variantes (pós-Opus 5)

| Arquivo | O que é | Quando usar |
|---|---|---|
| **`AGENTS.balanced.md`** | Template completo / meta-constituição. Toda a doutrina. | Default. Onboarding, repos novos, qualquer dúvida. |
| **`AGENTS.opus48.balanced.md`** | `balanced` sem o que o harness do Claude Code já cumpre nativamente (commit/push, memory-vs-estado, terseness). | Dentro do Claude Code, pra economizar contexto sem perder regra acionável. |
| **`AGENTS.minimal.md`** | Enxuta — só hard rules + ponteiros, cross-ref pro `balanced`. | Repos pequenos, sessões curtas, contexto apertado. |

> As antigas variantes por-modelo (`opus47.*`, `sonnet46.*`) foram pra `.archive/agents-variants-pre-opus48/`. O porquê está em [`AGENTS.assessment.md`](AGENTS.assessment.md).

---

## 1. Mapa rápido por papel

| Papel | Variante padrão | Subir para `balanced` completa | Descer para `minimal` |
|---|---|---|---|
| **Fullstack** | `opus48.balanced` (no Claude Code) | Refactor multi-módulo, mudança em VCS, deploy | Sessão exploratória, protótipo local |
| **Vibe coder** | `balanced` completa | — (já é a mais segura) | Só quando outro dev revisa o resultado |
| **Frontend** | `opus48.balanced` | Mudanças que tocam build, deploy ou env | Iteração visual rápida em componente isolado |
| **UX Designer** | `minimal` ou nenhum | Quando IA vai gerar arquivos commitáveis (copy, tokens, fixtures) | Brainstorm, wireframe, pesquisa — IA não toca repo |

---

## 2. Regras por papel

### 2.1 Fullstack
- **Default**: `opus48.balanced` dentro do Claude Code; `balanced` completa fora dele ou em onboarding.
- **Não pular**: §0 (Continuity) e §3 (Lei de Fechamento) — as duas que mais quebram quando ignoradas.
- **Pode pular cognitivamente**: §6 (Catálogo de agentes) — é dado, não regra.

### 2.2 Vibe coder
- **Default**: `balanced` completa. A explicitude é o seu cinto de segurança.
- **Antes de aceitar mudança grande**, peça em PT-BR: *"liste as regras do AGENTS.md que essa mudança toca e como você cumpriu cada uma"*. Se o agente não souber responder, não cumpriu.
- **Sinais de alerta**: agente sugere `rm`/`del`/"vou apagar X" → §2 (nunca deletar; mover pra `.archive/`) violada. Agente tenta editar `.env` no repo → §2 (segredos) violada. *(Commit/push sem você pedir o harness já bloqueia — se aparecer, há algo errado no contexto.)*

### 2.3 Frontend
- **Default**: `opus48.balanced`.
- **Atenção**: o GDFRSBT (§1) cobre componentes e copy também — não é só backend.
- **Iteração visual** (CSS/layout puro): pode usar `minimal` — risco de violar regra é baixo.
- **Build/deploy/env**: sobe pra `balanced` completa. Blast radius alto.
- **A11y/i18n**: documentar em `.docs/tasks/` mesmo que pareça pequeno.

### 2.4 UX Designer
- **Caso comum**: você não precisa de `AGENTS.md`. Brainstorm, wireframe, pesquisa — IA não toca o repo.
- **Quando precisa**: IA vai gerar arquivos que **vão pro repo** (tokens, copy em JSON, fixtures, conteúdo estático).
  - Use `minimal`.
  - Peça: *"todo arquivo que você gerar vai em local apropriado conforme §4 do AGENTS.md, com tarefa registrada"*.

---

## 3. Como anexar o `AGENTS.md` certo

### 3.1 Claude Code (CLI/IDE)
O harness lê `AGENTS.md` automaticamente do root do projeto. Para usar uma variante:
- **Opção A (temporária)**: copie a variante por cima de `<repo>/AGENTS.md` antes da sessão.
- **Opção B (permanente)**: escolha uma variante como canônica do projeto e descarte as outras.
- **Opção C (por sessão)**: cole o conteúdo da variante na primeira mensagem como contexto.

### 3.2 Outros agentes (Cursor, Cline, etc.)
- Aponte a config do agente para o caminho da variante escolhida, não para um `AGENTS.md` genérico.

### 3.3 ChatGPT/Gemini/web
- Cole o conteúdo no system prompt ou primeira mensagem. `minimal` cabe confortavelmente em janelas pequenas.

---

## 4. Sinais de que escolheu a variante errada

- ❌ Agente esquece §0 (continuity) duas vezes na mesma sessão → suba de `minimal` → `balanced`.
- ❌ Agente fica refraseando regras na resposta em vez de agir → variante grande demais; desce.
- ❌ Você lendo este arquivo mais de uma vez na semana → fixe um default no time e pare de re-decidir.

---

## 5. Convenção do time (preencher conforme decisão)

- [ ] Default fullstack: `___________`
- [ ] Default frontend: `___________`
- [ ] Default vibe coder: `___________`
- [ ] Default UX (quando aplicável): `___________`
- [ ] Variante única no repo (se decidir consolidar): `___________`
