---
name: kommo-salesbot-builder
description: >-
  This skill should be used when the user asks to validate, adapt/port,
  convert or import a Kommo Salesbot, or to compile one from a ready-made
  template — e.g. "adaptar esse bot pra outra conta", "portar salesbot entre
  contas", "gerar o JSON import-ready do salesbot", "validar meu salesbot do
  kommo", "montar salesbot de follow-up a partir de um template", "por que meu
  salesbot não importa", "salesbot renderiza bloco vazio", "widget_request não
  dispara", "port a Kommo salesbot", "validate Kommo bot export". It is the
  account-agnostic technical engine: takes an existing export, or a templates/
  skeleton with its slots filled, plus the target account, resolves IDs live,
  emits import-ready JSON (UI export format) and VALIDATES it before delivery.
  It does NOT design new flow topologies nor write copy. NOT for
  running/stopping a bot on leads (kommo-crm) nor for building widgets
  (kommo-widget-builder).
---

# Kommo Salesbot Builder — motor de export

Converte um **export existente** ou um **template de `templates/` com os slots preenchidos** em
JSON de Salesbot do Kommo **import-ready** para uma conta-alvo, e **valida antes de entregar**. É
agnóstico de conta. Os caminhos abaixo são relativos a
`${CLAUDE_PLUGIN_ROOT}/skills/kommo-salesbot-builder/`.

## Fora de escopo (de propósito)

Esta skill **não escreve copy nem cria topologias novas de fluxo**. A estrutura vem de um bot que
já existe (export) ou de um dos esqueletos de `templates/`; copy e IDs vêm do usuário. Gerar bots
com topologia nova a partir de um fluxo descrito é a fase 2 (adiada) em `references/ir.md`. O
motor garante uma coisa só: **export ou template preenchido + conta → JSON que importa sem erro**.

Disparar ou parar um bot em leads (`/bots/{id}/run`, `/stop`) é operação de CRM: skill
`kommo-crm`. Montar o widget `salesbot_designer` que faz o `widget_request` disparar é da skill
`kommo-widget-builder` (`${CLAUDE_PLUGIN_ROOT}/skills/kommo-widget-builder/references/widget-anatomy.md`);
o contrato de runtime fica aqui, em `references/api-and-runtime.md`.

## Não existe API de criar bot

O Kommo não tem CRUD de bot: só lista/metadata, `run` e `stop` (detalhes em
`references/api-and-runtime.md`). Criar/importar é pela UI: Configurações → Ferramentas de
comunicação → Salesbots → "Criar ou importar". O entregável é um `.json` no formato de export; a
verificação é offline (validador + round-trip) **+ 1 import manual** para confirmar o aceite.

## Duas entradas (ambas sem copy)

1. **Adaptar / portar** — export de qualquer conta + perfil-alvo → re-resolve IDs ao vivo →
   export válido para a conta nova. Workflow: `resolve_ids` → `parse_to_ir` → **remapear os IDs do
   IR à mão** para os resolvidos → `ir_to_export` → validate. Não há script de remap: o IR preserva os
   IDs estrangeiros verbatim, e a rede de segurança é o `validate.py --inventory`, que acusa ID
   fora do inventário. O `chat_source` é o caso mais sensível (veja abaixo).
2. **Compilar de template** — esqueleto de `templates/` com os slots preenchidos (copy + IDs
   resolvidos) + perfil-alvo → compila → valida. Para um fluxo que nenhum template cobre, partir
   do export de um bot parecido (modo 1) e ajustar folhas, não a topologia.

A saída **sempre** passa pelo `validate.py` antes de ser entregue.

## Como "sem erros" é garantido

1. `scripts/validate.py` aceita bots known-good e rejeita malformados (`tests/test_validate.py`).
2. `scripts/roundtrip.py` prova que o modelo do formato é fiel (parse → regenera → diff semântico).
3. 1 import manual confirma o aceite na conta real.

Nunca entregue um bot que não passou no `validate.py`.

## Formato (resumo; detalhe em `references/format.md`)

Wrapper: `{"type_functionality": N, "model": {"text": "<JSON string>", "name": "...", "positions": "<JSON string>", "type": N}}`.

- `text` e `positions` são **JSON stringificado** (escape duplo): gerar sempre por código.
- **Duas representações que precisam casar**: `text` (por step-id, `goto:{step,type}`) e
  `positions` (grafo visual, `goto:{block:id}` e `links`). Essa consistência é a fonte nº 1 de erro.
- Handlers reais divergem da doc dev: `send_message` (não `show`), `waits`, `conditions`
  (plural), `distribution`, `trigger`, `wait_answer`, `send_internal`, `goto`, `start`/`_stop`.
  `change_status` leva `pipeline_id` + `value` (status_id).
- **IDs de conta** em todo lugar. Nunca reusar IDs de outro bot ou conta.

## Conta, credenciais e IDs

Mesma convenção do plugin (veja a skill `kommo-crm`): perfil no config `kommo.local.json`
(`$KOMMO_CONFIG`, `./.claude/` ou `~/.claude/`), token só em `KOMMO_ACCESS_TOKEN_<PERFIL>` ou
`KOMMO_ACCESS_TOKEN`. O perfil-alvo é **explícito**: se o usuário não disse para qual conta, pergunte.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kommo-salesbot-builder/scripts/resolve_ids.py" <perfil> \
  --out /tmp/inv.<perfil>.json --scan-bots <pasta-de-exports-da-conta-alvo>
```

- Resolvível pela API v4 (só leitura, autônomo): **pipelines, statuses, users, custom fields
  (+ enums)**.
- **Não** resolvível: **`chat_sources`**. Para bot com `send_message` numa conta nova, pegue o id
  de um bot que já funciona naquele canal da conta-alvo (export pela UI) e confirme com o dono. O
  `--scan-bots` lista os ids vistos, mas não garante que são da conta-alvo. Depois de confirmar,
  acrescente o id à lista `chat_sources.confirmed` do inventário (ex.: `"confirmed": [12345]`); o
  validador avisa (`INV_CHATSRC`) sobre todo canal fora dessa lista.
- Etapas de sistema 142/143 (ganho/perdido) existem em todo pipeline e não podem ser renomeadas
  pela API.
- Antes de mapear `distribution` ou `change_responsible_user`, resolva `user_id` → nome no
  inventário e confirme com o usuário.

## Workflow

1. Receber o export (modo adaptar) ou a escolha de template + copy (modo compilar), e o
   perfil-alvo. Se faltar algum, peça: o motor não inventa fluxo nem conta.
2. Resolver IDs ao vivo → inventário (`resolve_ids.py`).
3. Modo adaptar: `salesbot_model.parse_to_ir` no export e remapear os IDs do IR para os
   resolvidos + `chat_source` **confirmado**; depois `salesbot_model.ir_to_export`.
   Modo compilar: preencher os slots do template (`templates/README.md`) com a copy e os IDs
   resolvidos e rodar
   `python3 scripts/compile.py templates/<nome>.json --values vals.json --inventory /tmp/inv.<perfil>.json --out bot.json`.
4. **Validar (gate obrigatório)**: `python3 scripts/validate.py bot.json --inventory /tmp/inv.<perfil>.json`.
   Falhou: corrigir e revalidar.
5. Entregar o `bot.json` com a instrução de import. Na primeira vez numa conta/canal, fazer o
   import junto com o usuário para confirmar o aceite e o `chat_source`.

Instrução de import para o usuário:

> Configurações → Ferramentas de comunicação → aba Salesbots → "Criar ou importar um novo robô" →
> importar → colar/subir o JSON. Abrir o construtor visual para conferir o fluxo. Salvar.

## Gates de segurança

Esta skill **não escreve no CRM** (só lê para resolver IDs). O risco é entregar um bot que,
importado, age sobre leads reais. Por isso:

- Validação é gate inegociável antes da entrega.
- `change_status`, `distribution` e `change_responsible_user` mexem em produção quando o bot roda.
  Liste o efeito ("vai mover leads para a etapa X", "vai distribuir entre os usuários A e B") e
  confirme com o usuário antes de entregar.
- Bot com `widget_request` exige widget com `salesbot_designer` e um webhook que **sempre** chama o
  `continue`; sem isso o lead trava (veja `references/api-and-runtime.md`).

## Pitfalls rápidos

- `text`/`positions` stringificados quebram no escape se feitos à mão. Sempre compilar.
- step-ids e block-ids são arbitrários e não sequenciais; não assuma 0, 1, 2...
- `finish`/`_stop` às vezes só em `positions`, às vezes também em `text`. O validador aceita os dois.
- Limite de 64KB no JSON do bot; botão ≤ 80 caracteres em alguns mensageiros; ≤ 13 botões.
- `chat_source` de outra conta = mensagem que não entrega.
- Template de WhatsApp escolhido no bot precisa ser HSM aprovado **daquele** número; o seletor não
  avisa (veja `references/api-and-runtime.md`).

## Mapa de arquivos

| Arquivo | Função |
|---|---|
| `references/format.md` | Formato de export completo, handlers, invariantes e divergências da doc |
| `references/ir.md` | Schema do IR (forma editável do export) e a fase 2 adiada |
| `references/api-and-runtime.md` | API de bots, `chat_source`, templates de WhatsApp, `widget_request` |
| `scripts/resolve_ids.py` | Inventário de IDs ao vivo por perfil (+ scan de `chat_sources` em exports) |
| `scripts/validate.py` | Valida um export contra os invariantes + inventário |
| `scripts/roundtrip.py` | export → IR → export com diff semântico |
| `scripts/roundtrip_templates.py` | Prova que cada template regenera o bot-fonte |
| `scripts/compile.py` | Template + valores → JSON de export validado |
| `scripts/salesbot_model.py` | Parse/serialize do formato (IR) |
| `templates/` | Esqueletos de IR sem copy + README |
| `tests/run_all.sh` | Roda todas as provas offline (corpus sintético ou `$SALESBOT_CORPUS`) |
| `viz/salesbot-viewer.html` | Visualizador read-only de um export, abre no navegador sem dependências |

## Corpus de prova

As provas rodam contra um corpus de exports. Sem `$SALESBOT_CORPUS` (ou argumento), o
`tests/run_all.sh` monta um corpus sintético com os templates compilados e o
`viz/sample-bot.export.json`. Exports reais de várias contas dão uma prova mais forte; guarde-os
fora do repositório, porque carregam IDs e copy de contas reais.
