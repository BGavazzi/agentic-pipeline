# Convenção — Notificar o humano quando o agente para (Stop hook)

> Status: ativa. Generaliza o padrão "me avise toda vez que parar de trabalhar".

## Princípio

Em runs longos/autônomos, o humano não fica olhando o terminal. Quando o agente **para**
(fim de turno, idle, fim de tarefa), ele deve **empurrar um aviso** pro canal assíncrono do
humano (WhatsApp/Slack/etc.), pra que a pessoa saiba que pode re-engajar — sem precisar
adivinhar a cadência.

Isto é um **comportamento automático disparado por evento** → **tem que ser um hook** no
`settings.json`. Memória/preferência NÃO dispara ação automática; só o harness executa hooks.
Evento certo: **`Stop`** (roda quando o Claude para, incluindo clear/resume/compact).

Relacionado: respostas em canal público pedem follow-up no mesmo canal; ver também a regra de
"convergência não é fechamento" (continuar até sinal explícito de parada).

## Forma (genérica)

`.claude/settings.json` (escopo projeto ou user):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "shell": "bash",
            "command": "<comando-de-notificação> || true",
            "timeout": 30,
            "statusMessage": "Avisando o humano…"
          }
        ]
      }
    ]
  }
}
```

Regras:
- **Nunca bloquear o stop.** Terminar sempre em sucesso (`|| true`, e silenciar stderr no script).
- **`shell: "bash"`** no Windows pra não cair no PowerShell (assume Git Bash presente).
- **Mensagem CONTEXTUAL, não estática.** O Stop dispara a CADA fim de turno — uma string fixa
  ("Claude parou") vira spam inútil. O agente escreve uma nota curta do que fez no turno num
  arquivo (ex.: `~/.claude/claude-stop-note.txt`) e o script envia o conteúdo dela.
- **Dedup por conteúdo.** O script guarda a última mensagem enviada; se a nota não mudou, NÃO
  reenvia → turnos sem novidade não pingam. Sem isso o usuário recebe ~1 msg/turno (a cada poucos
  minutos num run longo) e reclama — aprendizado real do run `teste_refactor_whitelabel`.
- **Script, não one-liner gigante.** Encapsular num script (`~/.claude/zap_notify.sh`) e referenciar.
- O comando NÃO deve vazar segredo: delega o envio a um componente que já tem as credenciais
  (ex.: container do bot), em vez de ler API keys no hook.

## Implementação local (WhatsApp via bot de zap)

Dependências (específicas do canal WhatsApp — por isso NÃO vai no `settings.json` compartilhado
de repo, só no settings local/user de quem tem o ambiente):
- Container do bot WhatsApp rodando (Docker), com Evolution configurado (`EVOLUTION_API_URL`,
  `EVOLUTION_INSTANCE`, `EVOLUTION_API_KEY` no env do container — ver `<your-bot-repo>`).
- Script `~/.claude/zap_notify.sh` que faz `docker exec <bot-container> python3 …` postando em
  `POST {EVOLUTION_API_URL}/message/sendText/{INSTANCE}` com header `apikey` e body `{number,text}`.
  As creds ficam dentro do container — o hook nunca as lê.
- Destino: JID do humano (ex.: `<phone-number>`). Ver directory de JIDs no `<your-bot-repo>`.

Comando do hook (exemplo):
```
bash "~/.claude/zap_notify.sh" || true
```
O `zap_notify.sh` lê `~/.claude/claude-stop-note.txt` (nota contextual que o agente atualiza
ao fim de cada turno), aplica dedup contra `~/.claude/.claude-stop-note.last`, e só então envia.

## Companheira: pollar respostas

Quando o agente MANDA algo no zap e fica aguardando, deve **pollar respostas a cada ~10 min**
(em run autônomo, via ScheduleWakeup ~600s) até o humano responder ou o assunto fechar. Isso é
comportamento do agente (não um hook), mas anda junto desta convenção.

## Como adotar em outro repo/perfil

1. Garantir o canal de envio (ex.: container do bot + `~/.claude/zap_notify.sh`).
2. Adicionar o bloco `hooks.Stop` no `settings.json` de **escopo apropriado**:
   - **user** (`~/.claude/settings.json`) se quiser em todos os projetos da máquina;
   - **local** (`.claude/settings.local.json`, gitignored) pra um projeto sem afetar o time;
   - **NÃO** no `.claude/settings.json` versionado de repo compartilhado (quebraria pra quem
     não tem o canal/credenciais).
3. Abrir `/hooks` uma vez (ou reiniciar) se o watcher não tinha settings no start da sessão.
