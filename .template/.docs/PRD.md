---
title: PRD — <project_name>
status: draft
owner: <maintainer>
created: <YYYY-MM-DD>
diamante: 1
---

# PRD — <project_name>

> Documento vivo. Atualizado pelo PRDfier (skill `grill-me`) ou pelo owner antes de cada milestone.

## 1. O problema

<Uma frase: que dor existe que justifica explorar este protótipo?>

## 2. Hipótese

<Se construirmos X, esperamos observar Y porque Z. Métrica observável.>

## 3. Quem usa

<Persona única — Diamante 1 não tenta atender múltiplas personas.>

## 4. Happy path

<3-7 passos do fluxo principal. Cada passo é uma frase.>

1.
2.
3.

## 5. Out of scope (Diamante 1)

- Auth canônica → mock local OK
- Multi-tenant → single-tenant OK
- RBAC granular → root user OK
- Performance/observabilidade plenas → smoke test OK
- Migrations reversíveis → SQLite OK
- I18n → 1 idioma OK

## 6. Critério de "vale levar pro gate humano"

- [ ] README com demo de 1 parágrafo
- [ ] `docker compose up` (ou equivalente) roda local
- [ ] Screenshots/GIF do happy path
- [ ] Tests do happy path passando
- [ ] Link de preview / domínio temporário
- [ ] Esta seção do PRD respondida em ≤ 1 página

## 7. Open questions (alimentar grill-me)

- ?
- ?

## 8. Decisões tomadas

| Quando | Decisão | Por quê |
|---|---|---|
| <data> | <decisão> | <1-line rationale> |

---

**Pós-Diamante 1**: este doc não promove pra Diamante 2 sem ser reescrito. O PRD de Diamante 2 vai pro repo canônico, alinhado com a documentação arquitetural desse repo.
