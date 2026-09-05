# Gaps da fábrica agêntica para testar FE+BE (picture-perfect + funcional) sem AI pitfalls

> **Nota de proveniência (migração 2026-09).** Migrado do repo predecessor deste
> (`guidelines_IA`, tombstoned). Documento histórico: os 4 gaps duros descritos
> abaixo (regressão visual, FE-real, loop Figma→render, verificador
> independente) **já foram fechados** neste repo — são exatamente o porquê de
> `visual-tester`, `tester --fe-real`, `figma-frontend-context
> --extract_tokens`, e `ultrareview` existirem hoje. Mantido como registro do
> raciocínio que levou a construí-los, não como backlog aberto.

> Spec de fechamento de gaps. Auditado 2026-06-08.

A fábrica é sólida para backend funcional tier-protótipo. Colapsa em 3 dos 4 eixos pedidos: **FE funcional real, visual/picture-perfect, e verificação independente (adversarial)**.

## Já existia (baseline, em 2026-06-08)
- Pipeline 9-stages `grounding→builder→tester→librarian→notifier` + dispatcher + quota gate determinístico.
- Anti-rubber-stamp de *fechamento*: `scripts/validate_closure.py` pega "0/7 [x], tudo [N/A]"; `tester` §9/§11 proíbe skip-as-pass e mockar a unidade sob teste.
- Caminho Figma→brief→código: `figma-frontend-context` → `codebase-grounding` → `implement-figma-task`.
- `meta-test` testa os próprios skills (subagentes + `expected.yaml`).

## BLOQUEADORES da iniciativa Figma→Storybook (à época — hoje resolvidos por `visual-tester`)

**GAP-1 — Zero capacidade de regressão visual. (BLOQUEADOR DURO)**
Busca por `playwright|storybook|chromatic|percy|loki|screenshot|baseline|toMatchSnapshot` só retornava hits de *backlog*. `codebase-grounding` só *detectava* `has_storybook` — nunca renderizava/diffava. Sem baseline, sem diff pixel/perceptual. Fidelidade ao Figma era a barra de aceite e a fábrica não produzia nem comparava artefato visual.
*Fix mínimo (proposto então, construído hoje como `visual-tester`):* skill que: `storybook build` → screenshot por story via Playwright compartilhado (CDP-attach) → diff contra baseline versionado. Começa capturando baseline de um run abençoado por humano.

**GAP-2 — Tester recusava dirigir browser; "teste" de FE = `npm run build`+lint. (BLOQUEADOR DURO funcional)**
Verde = compilou, não = funciona, muito menos = parece certo.
*Fix mínimo (hoje: `tester --fe-real`):* fiar o Playwright compartilhado (CDP-attach p/ páginas logadas) num passo FE real: subir dev server, dirigir o fluxo, assertar DOM/interação.

**GAP-3 — Sem loop Figma→render; design source of truth era descartado. (BLOQUEADOR DURO "bate com Figma")**
`figma-frontend-context` dizia 2× que **NÃO** extraía tokens (cor/spacing/tipo) — só "o quê", não "como estilizar". Nada re-buscava o frame p/ comparar.
*Fix mínimo (hoje: `figma-frontend-context --extract_tokens`):* estender a skill p/ também exportar o PNG do frame + extrair tokens; passo de verificação que screenshota o componente buildado e roda diff perceptual (SSIM/pixelmatch) com threshold numérico + imagem-diff anexada (a imagem-diff é a evidência anti-alucinação).

## BLOQUEADOR do mandato anti-pitfall (transversal, à época)

**GAP-4 — Sem verificador independente/adversarial; tester era in-band e auto-atestava. (BLOQUEADOR "PASS sem rodar")**
`validate_closure.py` pegava rubber-stamp de *doc*; `tester` proibia em *política* — mas nada **provava execução**. Dispatcher confiava na string STATUS do próprio tester. Sem exit code capturado, sem JUnit/stdout salvo, sem 2º agente re-rodando. O stage "Reviewer" estava documentado na strategy mas **não tinha SKILL.md**.
*Fix mínimo (hoje: `ultrareview`):* (a) `tester` emite artefato checável por máquina — exit code + relatório em `.docs/test-reports/` — e o dispatcher gateia no **arquivo**, não na prosa. (b) agente independente que re-roda a suíte e inspeciona o diff por asserts vazios (`expect(true)`, `it()` sem assert, snapshot-only). Adversarial = invocação de agente diferente de quem escreveu.

## Gap parcial (by-design p/ protótipo, ainda válido hoje)
**GAP-5 — Sem harness DB/migration/e2e completo em modo `prototype`.** Modo `production` (docker compose + DB seedado + contract + e2e) segue não-runnable em V1. By-design p/ Diamante II (protótipo, dado descartável); vira bloqueador quando a fábrica precisar certificar backend de verdade.

## Quota (sem gap, com ressalva — ainda relevante)
`quota_gate.py` é sólido. **Ressalva:** conta *tasks*, não volume de teste. Um sweep visual (build Storybook + N screenshots + N diffs/componente) pesa muito mais que `tsc`+`curl`. Re-tunar limites ou adicionar custo-por-task em tokens quando o volume de tasks visuais crescer — senão uma task visual pesada come a noite.

## Prioridade (histórico — ordem em que foram fechados)
1. GAP-2 + GAP-1 + GAP-3 (juntos = a iniciativa; nenhum existia; todos bloqueavam).
2. GAP-4 (mandato anti-pitfall).
3. GAP-5 (deferido por design; bloqueia só ao certificar backend).
4. Re-tune de quota (follow-up pequeno, ainda em aberto).
