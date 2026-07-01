# Convenção — timestamp em milissegundos para migrations (org-wide)

Regra de nomenclatura de migrations válida em **todos** os repos da org que usam versionamento de schema (TypeORM, Knex, Sequelize, Flyway, ou qualquer runner caseiro).

---

## 1. 🔒 Migration nova usa timestamp em ms, nunca incremento sequencial

Ao gerar ou criar uma migration, o prefixo do nome deve ser o **Unix timestamp em milissegundos** no momento da criação — nunca `001`, `002`, nem o número-seguinte do último arquivo existente.

**Forma correta:**

```
1749998400000_add_speaker_status_enum.ts
1750001200000_create_activity_instructors.ts
```

**Forma proibida:**

```
001_add_speaker_status_enum.ts          ← número sequencial
0042_create_activity_instructors.ts     ← incremento manual do último
```

Obter o timestamp de criação:

```bash
node -e "console.log(Date.now())"
# ou
date +%s%3N          # Linux/macOS/Git Bash
```

Frameworks com gerador nativo (TypeORM `migration:generate`, Knex `migrate:make` com opção `--timestamp`) já produzem o timestamp — não sobrescrever manualmente com sequencial.

---

## 2. Por que não basta o segundo (sem ms)?

Timestamps em segundos (`1749998400`) colidem quando dois deploys ou dois devs geram migrations no mesmo segundo — raro mas real em CI + local simultâneos. Milissegundos reduzem a colisão a zero na prática e são o formato já usado pelos geradores de TypeORM/Knex por padrão.

---

## 3. Resolução de conflito entre branches

Se dois branches adicionarem migrations com timestamps próximos, **não renumere** — o timestamp já é a ordem de aplicação. Basta garantir que o runner aplica por ordem crescente de nome (comportamento padrão de todos os runners listados). Não há merge conflict real: os arquivos têm nomes distintos e o runner aplica ambos em sequência.

Se o runner do projeto usa tabela de controle (`migrations` / `schema_migrations`), confirmar que a chave primária é o nome completo do arquivo (ou o timestamp extraído), nunca um auto-increment local.

---

## 4. Exceções aceitas (com justificativa)

| Situação | Aceito | Condição |
|---|---|---|
| Migration de seed / fixture local (sem deploy) | sequencial OK | Arquivo fora do diretório `migrations/` canônico |
| Runner legado que só aceita inteiro curto | sequencial OK | Comentário no PR explicando o constraint do runner |
| Migração gerada por CLI de terceiro (Prisma `migrate dev`) | formato do CLI | Não alterar o nome gerado |

Toda exceção deve ter uma linha de justificativa no PR ou no cabeçalho do arquivo.

**Why:** a raiz do problema é parallelismo de branches — dois devs trabalhando em features diferentes criam `0043_foo.ts` e `0043_bar.ts` no mesmo repo, causando conflito de número e ambiguidade de ordem. Timestamp em ms é único por construção, independe de comunicação entre branches, e é o padrão já adotado pelos geradores canônicos. Custo zero de adoção, colisão zero em prática.
