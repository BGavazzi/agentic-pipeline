# Convenção — defaults de engenharia (org-wide)

Decisões de arquitetura e stack que valem como **default** em todos os repos da org. Não são leis absolutas (👇 têm exceções justificáveis), mas o ônus de divergir é de quem diverge.

> Promovidas de memória pessoal para a constituição porque descrevem\ como\ esta\ org\ constrói\ software, não a preferência de uma pessoa.

---

## 1. Regras de negócio moram no backend que é dono do dado

Validação, enforcement de invariantes, integração com 3rd-party (chaves/segredos) e auto-derivação **vão no backend que é dono do dado** — nunca no frontend. O front é **UX**: surfacing de erro do backend, affordance, disabling otimista. Nunca enforcement.

- Regra de validação ("X obrigatório pra publicar", "Y ∈ Z"): use-case no backend + constraint no DB onde couber. Front mostra o 4xx/422.
- Integração 3rd-party com segredo (image-gen, OpenAI, pagamento): endpoint no backend. Front faz POST e lê a resposta.
- Auto-derivação ("derivar X de Y na escrita"): backend re-deriva autoritativamente. Front pode pré-preencher pra UX.
- Invariante cross-record: transação no backend.

**Why:** se a regra vive só no front, qualquer outro caller (scraper, webhook, microserviço futuro, `curl` manual) a contorna. Vivido com `news_items.source_id` (ADR-002). Se um ticket de front diz "enforce X" / "prevent Y", reescrever como ticket de backend + um follow-up fino de UI.

---

## 2. Sem encanamento técnico exposto na UI

Não expor plumbing de backend (selectors de FK deriváveis do contexto) como escolha de formulário em telas de editor. **Preferir auto-derivação silenciosa.**

Quando um fix exige popular um FK relacional num form, primeiro perguntar se o FK pode ser **derivado** de outro campo que o usuário já se importa (host da URL, nome da categoria, slug). Se sim, derivar num watch/effect e esconder o FK. Só cair pra um picker quando a derivação for genuinamente ambígua e o usuário **tiver** que desambiguar. Documentar a lógica de derivação num ADR — inferência silenciosa não-rastreável vira fantasma.

**Why:** o editor pensa em "a URL do artigo original", não na tabela-taxonomia curada. Um picker adiciona um clique que o modelo mental do usuário não justifica.

---

## 3. Imagem gerada por IA: nunca fotorrealista

Imagem gerada por IA (Imagen ou qualquer provider) pra produto\ public-facing (portal de notícias, etc.) **nunca pode ser fotorrealista** — sempre ilustração / estilo não-foto.

- A ferramenta de imagem compartilhada **não expõe modo `"photo"`** — não passar `style: "photo"`.
- Parear com label visível "gerada por IA".

**Why:** imagem fotorrealista de evento/pessoa real = desinformação + risco de likeness; ilustração sinaliza claramente que é editorial/IA, não foto do evento. Aplica ao cluster-synthesis, geração de capa e tools similares.

---

## 4. Componente de UI ⇄ Storybook (obrigatório, frontend)

Em qualquer repo de frontend com Storybook, **componente e story são um pacote só**:

- **Nenhum componente novo sem story.** Criar um componente de UI (átomo, molécula, qualquer reusável em `Components/`) **obriga** entregar, no mesmo PR, o que o Storybook precisa: o `*.stories.jsx` com as variantes representativas (estados/cores/tamanhos relevantes) renderizando com o tema real (decorator `ChakraProvider` + theme tokens). PR de componente sem story = incompleto, não mergeia.
- **Se já existe no Storybook, use e respeite.** Antes de escrever um componente, **procurar no Storybook/catálogo** se já há um canônico pra aquela intenção. Se houver, **reutilizar** (estender via props/composição) — **proibido clonar** um `XCustom`/`XV2`/cópia-por-domínio que faça o mesmo. Divergir do canônico exige justificativa explícita no PR (e idealmente vira uma variante do canônico, não um novo componente).
- **Tokens, não hardcode.** Componente em story usa tokens do tema (cor/spacing/tipografia) — zero hex hardcoded. É o que torna a story fiel ao Figma e o whitelabel possível.
- **Pixel-perfect verificável.** A story é o artefato contra o qual o design/QA confere fidelidade ao Figma (e onde o `visual-tester` da fábrica roda diff perceptual). Sem story, "bate com o Figma" é inverificável.

**Why:** o <front-repo> acumulou ~21 implementações de Button, 17 de Input, 8 de Avatar — cada tela montada sobre átomos não-consolidados, então a mesma intenção aparece visualmente diferente em telas diferentes. Story-por-componente + "reusar o canônico" é o que impede a próxima geração de clones e dá ao designer uma fonte única de verdade. 2026-06-09.
