# GDFRSBT — Metodologia de Desenvolvimento Orientado a Especificações

> **Primeira Passagem** — Documento vivo. Gerado com base na leitura dos `AGENTS.md` dos projetos `<whatsapp-audio-bot-repo>` e `<your-bot-repo>`.
> Próximas passagens aprofundam cada estágio com exemplos, templates e workflows operacionais.

---

## 0. O Que É o GDFRSBT

O **GDFRSBT** é uma metodologia de desenvolvimento de software que combina oito práticas complementares numa única cadeia sequencial e coerente. Cada prática tem seu estágio, foco, e artefato de saída bem definidos. Juntas, elas formam um sistema que vai do "por que construir isso" até "como provar que funciona", eliminando os pontos cegos que causam retrabalho, colisões entre agentes e entropia de longo prazo.

A sigla desdobra assim:

| Sigla | Prática | Em Português |
|:------|:--------|:-------------|
| **G** | Goal Driven Development | Desenvolvimento Orientado a Objetivos |
| **D** | Domain Driven Design (Estratégico) | Design Orientado ao Domínio (Macro) |
| **F** | Feature Driven Development | Desenvolvimento Orientado a Features |
| **R** | Readme Driven Development | Desenvolvimento Orientado ao README |
| **S** | Spec Driven Development | Desenvolvimento Orientado a Especificações |
| **B** | Behavior Driven Development | Desenvolvimento Orientado a Comportamento |
| **T** | Test Driven Development | Desenvolvimento Orientado a Testes |

> **Nota:** O segundo "D" (DDD Tático) opera em paralelo com o BDD e TDD — ele é o refinamento do domínio em nível micro (Entidades, Agregados, Value Objects) depois que o comportamento esperado já foi definido.

---

## 1. Os Oito Estágios em Detalhe

### Estágio 1 — GDD: Goal Driven Development
**Escopo:** Macro / Negócio  
**Pergunta central:** *Por que estamos construindo isso?*  
**Artefato de saída:** Metas claras e Métricas de Sucesso (OKRs, KPIs, critérios de aceitação de produto)

Antes de qualquer linha de código ou spec, o time define o objetivo de negócio com precisão suficiente para que qualquer agente, humano ou IA, possa tomar decisões coerentes sem precisar perguntar. Um objetivo vago gera features vaga.

**No projeto <whatsapp-audio-bot-repo>, o GDD aparece como:**
- "Zero-Friction Voice-to-API Assistant for Blue Events Management"
- Métricas implícitas: zero duplicatas na API, human-in-the-loop via emoji, 100% de cobertura de testes

---

### Estágio 2 — DDD Estratégico: Domain Driven Design (Macro)
**Escopo:** Arquitetura  
**Pergunta central:** *Como o domínio se divide?*  
**Artefato de saída:** Bounded Contexts, Context Maps, Subdominios

O domínio é mapeado em fronteiras bem delimitadas antes de qualquer decisão técnica. Cada módulo tem responsabilidade única e interfaces definidas. No contexto multi-agente, isso é crítico: agentes precisam saber exatamente *de quem* é a responsabilidade de cada parte do sistema.

**No projeto <whatsapp-audio-bot-repo>, o DDD Estratégico aparece como:**  
O Mapa de Modularidade na seção 1.4 do AGENTS.md:

| Módulo | Arquivo(s) | Responsabilidade |
|:-------|:-----------|:-----------------|
| Webhook Router | `evolution_webhook.py` | Ponto de entrada, roteamento por tipo de mensagem |
| AI Agent | `agno_service.py` | STT + Gemini LLM + Ferramentas |
| API\ Client | `api_client\.py` | Adaptador CRUD completo |
| Resolution | `resolution_service.py` | Nome → UUID, dedup, cache |
| ... | ... | ... |

---

### Estágio 3 — FDD: Feature Driven Development
**Escopo:** Gestão de Entrega  
**Pergunta central:** *O que vamos construir, em que ordem?*  
**Artefato de saída:** Lista priorizada e decomposta de Features

Features são decompostas em unidades entregáveis. O sistema de numeração `nnnn-tipo-subtipo-nomes.md` é a implementação concreta do FDD: define prioridade (primeiros 3 dígitos = ordem cronológica), paralelismo (último dígito: `0` = bloqueador, `1-9` = paralelo), tipo e subtipo.

**No projeto <whatsapp-audio-bot-repo>, o FDD aparece como:**  
O sistema de tarefas em `.docs/tasks/` com convenção:
```
.docs/tasks/
  0010-feat-...   ← bloqueador (sequencial)
  0021-feat-...   ← paralelo com 0022 e 0023
  0022-feat-...
  0023-fix-...
  completed/      ← tarefas concluídas
```

---

### Estágio 4 — RDD: Readme Driven Development
**Escopo:** UX / DX (Developer Experience)  
**Pergunta central:** *Como o produto é experimentado por quem o usa?*  
**Artefato de saída:** `README.md` que orienta a experiência de uso

O README é redigido *antes* da implementação completa, como um contrato de experiência. Ele define como o sistema se apresenta ao mundo externo — humanos e agentes. Qualquer feature implementada que não couber no README é sinal de escopo desnecessário.

**Obrigação de atualização (Lei de Fechamento):**  
O README deve ser atualizado ao fechar toda tarefa que introduza funcionalidade visível ao usuário ou mude comportamento do sistema.

---

### Estágio 5 — SDD: Spec Driven Development ← *Foco desta documentação*
**Escopo:** Integração / Contratos  
**Pergunta central:** *Qual é o contrato entre componentes?*  
**Artefato de saída:** Specs legíveis por máquina (OpenAPI, JSON Schema, Pydantic Models, SDD_KIT.md)

Ver Seção 2 para detalhamento completo.

---

### Estágio 6 — BDD: Behavior Driven Development
**Escopo:** Regras de Negócio  
**Pergunta central:** *O que o sistema deve fazer em cada situação?*  
**Artefato de saída:** Cenários estruturados (Given / When / Then)

Define o comportamento esperado de cada feature em linguagem próxima ao negócio. No contexto do projeto, isso aparece nos critérios de aceite das tarefas (os `[ ]` checkboxes) e nas condições de saída.

**Exemplo real da tarefa `0120-fix-missing-approval-router-methods.md`:**
```
- [ ] _send_ambiguity_list(self, jid, operations, partial_task) implementado e funcional
- [ ] _build_ceo_summary(self, operations, results) implementado e funcional
- [ ] Nenhum AttributeError em paths de ambiguidade e CEO mode
- [ ] pytest tests/ -v --tb=short passa 100%
```

---

### Estágio 7 — DDD Tático: Domain Driven Design (Micro)
**Escopo:** Lógica de Negócio  
**Pergunta central:** *Como o domínio é modelado em código?*  
**Artefato de saída:** Entidades, Agregados, Value Objects (Pydantic Models no projeto)

A lei do projeto é explícita: **"API payloads DEVEM usar modelos Pydantic estritos (`api_models\.py`). Nunca use dicionários crus para requisições de API."** Este é o DDD Tático na prática: o domínio é expressado em tipos, não em estruturas genéricas.

---

### Estágio 8 — TDD: Test Driven Development
**Escopo:** Código / Unidade  
**Pergunta central:** *Como provar que funciona?*  
**Artefato de saída:** Testes unitários (falhos → implementação → refatoração)

A lei: *"Qualquer mudança de código DEVE ser verificada contra os 160+ testes unitários: `pytest tests/ -v --tb=short`. Não afirme que uma tarefa está completa se os testes estiverem falhando."*

---

## 2. SDD em Profundidade — Spec Driven Development

### 2.1 O Que É uma "Spec" Neste Sistema

Uma **spec** é qualquer artefato que define um contrato entre partes do sistema de forma precisa o suficiente para ser verificado automaticamente ou por um agente sem ambiguidade. No GDFRSBT, specs existem em três camadas:

**Camada 1 — Decisões Arquiteturais (`SDD_KIT.md`)**  
Cada decisão de design que afeta comportamento global recebe uma flag `Dxx`:
```markdown
| D11 | Duplicate Detection | Resolution service busca backend API antes de qualquer create_* |
| D17 | Idempotency + Sequential | Redis lock por usuário. msg_ids duplicados rejeitados. |
| D25 | UUID Safety Gate | Dispatcher rejeita payload com IDs não-UUID (exceto $! placeholders) |
```

**Camada 2 — Contratos de Módulo (código + comentários)**  
Todo ponto de interface público tem um `# CONTRACT:` explícito:
```python
# CONTRACT: Returns None on 404 (entity not found), raises APIClientError
# on 5xx. Callers MUST handle None gracefully (see dispatcher.py:L145).
```

**Camada 3 — Contratos de Tarefa (arquivos de tarefa)**  
Cada tarefa define seu contrato na forma de Condições de Saída (exit criteria):
```markdown
## Condições de Saída
- [ ] _send_ambiguity_list implementado e funcional
- [ ] pytest passa 100%
```

### 2.2 O `SDD_KIT.md` — O Coração do SDD

O `SDD_KIT.md` é o documento central de Spec Driven Development num projeto. Ele tem estrutura fixa:

```
1. Executive Summary     ← O que o sistema faz, em uma página
2. Core Design Decisions ← Tabela de flags Dxx com decisão, rationale e arquivos
3. Architecture Overview ← Pipeline flow + Services Map + Tools
4. (Extensões por projeto)
```

**Regra de adição de flags:**
- Toda nova decisão arquitetural gera uma nova flag `Dxx`
- Toda mudança em decisão existente atualiza a entrada correspondente
- Flags marcadas como `(Planned)` são specs futuras ainda não implementadas — esse é o mecanismo de "design first"
- O código deve referenciar as flags nos comentários: `# D07: retry 3x com backoff...`

**Ciclo de vida de uma flag:**
```
Ideia → Proposal (planning/) → Flag Dxx (Planned) no SDD_KIT → 
Tarefa nnnn criada → Implementação → Flag atualizada (status: implementada) → 
Tarefa fechada
```

### 2.3 Anatomy de uma Tarefa SDD-Compliant

Uma tarefa bem formada no sistema GDFRSBT contém obrigatoriamente:

```markdown
---
status: open
priority: [P0/P1/P2/high/medium/low]
type: [feat/fix/refactor/docs/chore/audit]
---

# nnnn — [Tipo]: [Título Descritivo]

## Contexto
[Por que esta tarefa existe. Qual problema ela resolve. Referências ao ROUTE_BEHAVIOR_MAP, 
SDD_KIT, ou outras tarefas relacionadas.]

## Problema
[Descrição técnica precisa do que está errado ou ausente.]

## O Que Fazer
- [ ] Subtarefa 1 (acionável, verificável)
- [ ] Subtarefa 2
- [ ] Subtarefa N

## Arquivos Afetados
- `src/services/foo.py` (principal)
- `tests/test_foo.py` (testes)

## Condições de Saída
- [ ] Comportamento X implementado
- [ ] pytest tests/ -v --tb=short passa 100%

## Documentação Obrigatória (Lei de Fechamento)
- [ ] `.docs/function-catalog.md` atualizado
- [ ] `docs/SDD_KIT.md` atualizado (se nova decisão arquitetural → flag Dxx)
- [ ] `README.md` atualizado (se aplicável)
- [ ] `.agents/continuity-*.md` atualizado
- [ ] Testes escritos e passando
- [ ] `.docs/ROUTE_BEHAVIOR_MAP.md` atualizado (se rota/action/modelo alterado)
```

### 2.4 Convenção de Nomes de Tarefas

```
nnnn-tipo-subtipo-nomes.md
│    │    │        └─ Palavras descritivas com hífens
│    │    └──────── Subtipo (opcional, ex: report, memory, core)
│    └───────────── Tipo: feat, fix, refactor, docs, chore, audit, proposal
└────────────────── 4 dígitos:
                    - Primeiros 3: ordem cronológica de planejamento
                    - Último: 0 = bloqueador, 1-9 = paralelo
```

**Exemplos:**
```
0010-feat-...         ← 1º bloco, bloqueador
0021-feat-...         ← 2º bloco, tarefa paralela 1
0022-fix-core-...     ← 2º bloco, tarefa paralela 2 (com subtipo "core")
0113-feat-image-processing-pipeline.md
0126-refactor-uniform-dedup-strategy.md
```

### 2.5 O Ciclo Completo de uma Spec

```
┌─────────────────────────────────────────────────────────────────┐
│                     CICLO SDD COMPLETO                          │
│                                                                 │
│  1. DESCOBERTA                                                  │
│     Problema ou feature identificada                            │
│     → Criado em .docs/tasks/planning/ (sem código ainda)       │
│                                                                 │
│  2. ESPECIFICAÇÃO                                               │
│     Planning → Tarefa formal com:                              │
│     • Condições de Saída claras                                │
│     • Arquivos Afetados listados                               │
│     • Flag Dxx no SDD_KIT.md (se mudança arquitetural)         │
│     → Arquivo em .docs/tasks/nnnn-tipo-subtipo-nomes.md        │
│                                                                 │
│  3. IMPLEMENTAÇÃO                                               │
│     Agente pega tarefa de menor número disponível              │
│     Registra lock em .agents/file-locks.md                     │
│     Implementa com Rich Commentary (docstrings, # SYNC:, etc.) │
│     Testa: pytest tests/ -v --tb=short                         │
│                                                                 │
│  4. FECHAMENTO (Task Closure Gate)                              │
│     Toda documentação da Lei de Fechamento atualizada           │
│     Flag Dxx atualizada no SDD_KIT.md                          │
│     Tarefa marcada [x] e movida para completed/                │
│     CHANGELOG.md atualizado                                    │
│     continuity-agente.md atualizado                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Protocolos Operacionais que Sustentam o SDD

### 3.1 Anti-Colisão Multi-Agente

O SDD só funciona em ambiente multi-agente se houver controle de concorrência. O sistema usa:

1. **File Lock Ledger** (`.agents/file-locks.md`): antes de editar qualquer arquivo, o agente registra o lock. Se o arquivo já está lockado, não edita — deixa comentário e passa para outra subtarefa.

2. **Freshness Check**: se o arquivo foi lido há mais de 2 minutos ou aparece no `jj diff`, o agente relê antes de editar.

3. **Domínio por Tarefa**: cada tarefa lista os arquivos que tocará em "Arquivos Afetados". Agentes verificam sobreposição antes de começar.

4. **Jujutsu (jj)**: o VCS primário, que elimina erros de lock do `.git/index` e permite que múltiplos agentes trabalhem em revisões isoladas simultâneas.

### 3.2 Rich Commentary — A Especificação Dentro do Código

Em ambiente multi-agente, o código é a interface de comunicação entre agentes. Comentários têm função de spec inline:

```python
# CONTRACT: Returns None on 404, raises APIClientError on 5xx.
# D11: Duplicate check via backend API search before any create_* operation.
# SYNC: If you change fields here, also update api_models\.py
# [claude-opus | 2026-03-24] Added retry logic — Tarefa: 0022-fix-core.md
```

**Tipos de comentário:**
| Tag | Propósito |
|:----|:----------|
| `# CONTRACT:` | Contrato de interface pública — o que o chamador pode esperar |
| `# D##:` | Referência a uma decisão arquitetural do SDD_KIT.md |
| `# SYNC:` | Aviso de interdependência — mudança aqui implica mudança ali |
| `# [agente \| data]` | Auditoria — quem mudou, quando, e por quê |
| `# TODO(agente):` | Pendência rastreável com responsável |

### 3.3 Changelog como Spec de Mudança

O `CHANGELOG.md` é a spec histórica do sistema. Formato imutável:

```markdown
## [AAAA-MM-DD] - Título Breve
### Added / Changed / Fixed / Removed
- Detalhes precisos da mudança
**Author**: [Nome ou ID do Agente]
```

Regras: sempre adicionar no topo, nunca deletar entradas existentes, nunca modificar entradas passadas (exceto typos).

### 3.4 Continuity Ledger — Memória do Agente

Cada agente mantém `.agents/continuity-<nome>.md` com:
- O que foi feito nesta sessão (por tópico)
- Estado dos testes
- O que o próximo agente precisa saber
- Arquivos críticos tocados

Isso é a spec de handover: garante que qualquer agente que assumir o trabalho tenha contexto suficiente para continuar sem retrabalho.

---

## 4. Estrutura de Diretórios do Sistema GDFRSBT

```
projeto/
│
├── AGENTS.md                    ← Constituição do projeto (lida por TODOS os agentes)
├── README.md                    ← RDD: experiência do usuário final
├── CHANGELOG.md                 ← Spec histórica de mudanças (imutável)
│
├── .docs/
│   ├── tasks/
│   │   ├── 000-template.md      ← Template padrão de tarefa
│   │   ├── nnnn-tipo-nome.md    ← Tarefas abertas (FDD + BDD + SDD)
│   │   ├── planning/            ← Ideias e propostas (pré-tarefa)
│   │   └── completed/           ← Tarefas concluídas
│   ├── tasklist.json            ← Index de status (não editado por agentes)
│   ├── architecture/
│   │   └── SDD_KIT.md           ← Spec central: decisões Dxx (SDD)
│   ├── function-catalog.md      ← Catalog de funções (atualizado no fechamento)
│   ├── ROUTE_BEHAVIOR_MAP.md    ← Mapa de comportamento de rotas
│   └── CHANGELOG.md             ← Histórico técnico
│
├── .agents/
│   ├── file-locks.md            ← Anti-colisão: locks de arquivos
│   ├── continuity-<agente>.md   ← Memória de handover por agente
│   ├── memories/                ← Descobertas arquiteturais compartilhadas
│   └── thoughts/<agente>/       ← Offload de contexto durante tarefas longas
│
├── docs/                        ← Documentação pública (usuário final)
│   └── SDD_KIT.md               ← (pode ser symlink para .docs/architecture/)
│
└── .archive/                    ← Código depreciado (nunca deletar)
```

---

## 5. Governança de Modelos e Agentes

### 5.1 Hierarquia de Modelos

| Uso | Modelo Preferido |
|:----|:----------------|
| Raciocínio complexo / codificação | `claude-opus-4-8` / `gemini-3.1-pro` |
| Execução rápida / workhorse | `claude-sonnet-4-6` / `gemini-3-flash` |
| Testes repetidos baratos | `claude-haiku-4-5` / `gemini-3.1-flash-lite` / `gpt-5.1-mini` |

### 5.2 Identidade de Agente

Todo agente deve assumir uma identidade ao trabalhar num repositório:
- Baseada na ferramenta (ex: `claude-code`, `gemini-cli`, `cursor`)
- Registrada em `.agents/continuity-<nome>.md`
- Usada em comentários de auditoria no código

---

## 6. Leis Imutáveis (Resumo)

| # | Lei | Violação Proibida |
|:--|:----|:-----------------|
| L1 | Nunca deletar arquivos | Usar `.archive/` sempre |
| L2 | Sempre atualizar CHANGELOG | Toda modificação tem entrada |
| L3 | Task Closure Gate | Sem fechar tarefa sem docs completas |
| L4 | File Lock antes de editar | Anti-colisão obrigatório |
| L5 | Testes devem passar | Nunca declarar tarefa completa com testes quebrando |
| L6 | SDD_KIT para toda decisão | Nenhum padrão novo sem flag Dxx |
| L7 | Pydantic para modelos de API | Nunca dicionários crus em payloads |

---

## 7. Próximas Passagens Previstas

Esta é a **Passagem 1** — mapa do modelo. As passagens seguintes vão aprofundar:

| Passagem | Foco |
|:---------|:-----|
| **P2** | Template de tarefa completo com exemplos reais anotados |
| **P3** | SDD_KIT.md em profundidade — como criar e evoluir flags Dxx |
| **P4** | Workflow multi-agente — file locks, jj, continuity na prática |
| **P5** | Rich Commentary — guia de comentários com exemplos do projeto |
| **P6** | Integração com ClickUp — como o `<your-bot-repo>` automatiza o ciclo GDFRSBT |

---

*Documento gerado por: claude-opus-4-8 | Data: 2026-04-29 | Fonte: `AGENTS.md` (<whatsapp-audio-bot-repo> + <your-bot-repo>)*
