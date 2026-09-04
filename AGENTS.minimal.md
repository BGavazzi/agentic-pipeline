# AGENTS.md — <project_name>

Variante mínima. Para versão completa, ver `AGENTS.balanced.md` da [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA). Herda regras hard 🔒 desse template.

**Versão**: <vX.Y.Z>  ·  **Tipo**: <one-line>

## §0 Protocolo Zero
Ler `.agents/continuity-<agente>.md`, alinhar foco, atualizar ao final.

## §1 Hard rules (locais — herdadas globais ficam no balanced)
- <ex: Pydantic obrigatório para payloads de API> — substituir conforme stack.
- Mudança arquitetural exige flag `Dxx` em `<sdd_kit_path>` antes do código.

## §2 Lei de Fechamento (resumida)
Antes de fechar tarefa: `CHANGELOG.md` + `<function_catalog>` + `.agents/continuity-*.md` + testes passando.
Se aplicável: `<sdd_kit_path>`, `README.md`, `<route_map>`.

## §3 Tarefas
`<task_dir>/nnnn-tipo-subtipo-nomes.md`. Numeração: `nnnn` = `[3 dígitos cronológicos][1 dígito paralelismo]`.
Tarefas concluídas em `<task_dir>/completed/`.

## §4 VCS
`jj` se disponível, senão `git`.

## §5 Rich Commentary
`# CONTRACT:` em interfaces públicas · `# Dxx:` ao referir decisão · `# SYNC:` em interdependências · `# [agente | data]` em mudanças.

---
**Pointers**: `AGENTS.balanced.md` (meta) · `MODEL-SELECTION.guidelines.md` · `GDFRSBT.md` — todos em [your-org/guidelines_IA](https://github.com/your-org/guidelines_IA).
