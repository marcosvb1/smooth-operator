# Salesbot: API, canais e runtime

O que a API do Kommo oferece (e não oferece) para bots, como achar o `chat_source` certo, as
armadilhas de template de WhatsApp e o contrato do `widget_request`.

## API de bots: leitura e execução, sem CRUD

- `GET /api/v4/bots` — lista. Coleção em **`_embedded.items`** (não `.bots`), com paginação real
  (`_page`/`_page_count`). Filtros: `filter[type_functionality][]` (`regular`/`greeting`/
  `marketing`/`nps`), `filter[id][]`, `with=favorite`. Objeto enxuto: `id`, `name`,
  `type_functionality`, `is_visual_editor`, `settings.active` (sem `created_at`/`updated_at`).
  `marketing` = bot do módulo Clientes/recorrência, não do pipeline de leads.
- `GET /api/v4/bots/{id}` — só metadata, **não** devolve o fluxo. Ler a lógica de um bot = exportar
  pela UI.
- `POST /api/v4/bots/{id}/run` — dispara 1 bot; body `entity_id` + `entity_type` (`leads`,
  `contacts` ou `customers`; `customers` exige o modo Clientes ativo).
- `POST /api/v4/bots/run` — lote de até 100 `{bot_id, entity_id, entity_type}`, resposta 202.
- `POST /api/v4/bots/{id}/stop` — para o bot rodando na entidade (só `leads`).
- **Criar, editar e apagar bot é só pela UI** (Configurações → Ferramentas de comunicação →
  Salesbots → "Criar ou importar"). Por isso o entregável é um `.json` de export e o import é
  manual.

Disparar bot em leads reais é WRITE no CRM: passa pelos gates da skill `kommo-crm`.

## `chat_source`: o calcanhar de Aquiles do `send_message`

O `chat_sources[].id` é o id de canal de mensageria (amojo) e **não é resolvível pela API**:
`/api/v4/sources` devolve 204 ou só as fontes da integração que chama.

Como obter o id certo:

1. Exportar pela UI um bot que já envia mensagem por aquele canal na conta-alvo (ou criar um bot
   de 1 passo e exportar) e ler o id; `resolve_ids.py --scan-bots <pasta>` lista os ids vistos.
2. Para saber de qual número/canal é um `source_id` de lead: `GET /api/v4/leads?limit=250&with=source_id`
   e tabular `source_id` × `pipeline_id`. O canal não tem nome pela API, mas as pipes em que os
   leads dele caem mostram de quem ele é. `filter[source_id]` é ignorado; `source_id` só vem com
   `with=source_id`.
3. Confirmar com o dono da conta. O nome da conta na UI pode não bater com o subdomínio, o que
   confunde "de qual conta é esse export".

## Template de WhatsApp no `send_message`

- **`params.type` do `send_message` é o tipo de ENTREGA (`"external"`)**, não de conteúdo. O
  dialeto `type: "text"/"buttons"/"buttons_url"` + `value` da doc dev só vale num Custom step
  (Code). Num `send_message` compilado, importa sem erro e **renderiza bloco vazio**.
- **O seletor de template do Salesbot não distingue modelo de WhatsApp (HSM) de modelo de chat
  "geral"**, nem mostra canal ou status de aprovação. Escolher um que não é HSM aprovado
  **daquele** número não dá erro na montagem: o Kommo envia como texto comum, e o WhatsApp recusa
  fora da janela de 24h. No card, o sintoma é um genérico "falha na mensagem".
- **Template em análise não aparece na lista.** Bot montado antes da aprovação nasce apontando
  para o modelo errado e continua assim depois. Ao subir canal novo, "trocar o template do bot"
  é passo obrigatório pós-aprovação.
- **`text` e `positions` não carregam o mesmo conteúdo**: bloco com `template_id` deixa `text`/
  `buttons` só no espelho de `positions`. Concluir sobre conteúdo lendo um blob só dá veredito
  errado.

## `widget_request` → webhook externo → `continue`

Docs: <https://developers.kommo.com/docs/private-chatbot-integration> e
<https://developers.kommo.com/reference/salesbot-widget-block-execution-confirmation>.

**Precisa de widget.** Import bem-sucedido não é execução: o Custom step aceita o JSON colado, o
bot importa e fica ativo, e o POST simplesmente não sai. Pré-requisitos:

1. widget com `locations: ["salesbot_designer"]` no manifest;
2. o objeto `salesbot_designer` que desenha o modal;
3. `onSalesbotDesignerSave` no `script.js` (é ele que gera o bloco);
4. a **secret key** da integração, que assina o JWT do POST;
5. token de **administrador** para o `continue`.

Como montar esse widget (manifest `salesbot_designer` + `onSalesbotDesignerSave`): skill
`kommo-widget-builder`, seção `salesbot_designer` em
`${CLAUDE_PLUGIN_ROOT}/skills/kommo-widget-builder/references/widget-anatomy.md`.

**Ida** — o Custom step com `widget_request` (`params.url` + `params.data`, array de strings/
placeholders) faz um POST na URL com:

```json
{ "token": "<JWT>", "data": [...], "return_url": "https://<sub>.kommo.com/api/v4/salesbot/<bot_id>/continue/<continue_id>" }
```

- **ACK obrigatório: HTTP 200 em até 2s.** No n8n, o Webhook no modo default ("respond
  immediately") já cumpre.
- O JWT é assinado com a secret key da integração e valida a origem. Campos: `account_id`,
  `subdomain`, `entity_type`, `entity_id`, `client_uid`.

**Volta** — POST no `return_url`, como administrador da conta:

```json
{ "data": { "status": "ok" },
  "execute_handlers": [ { "handler": "goto", "params": { "type": "question", "step": 3 } } ] }
```

- **O bot fica parado até esse POST chegar.** Não há timeout: sem `continue`, o lead trava no
  Custom step, e bot vivo na entidade impede o próximo bot de rodar nela. Todo ramo de erro do
  lado externo tem que chamar o `continue` mesmo assim.
- O que vai em `data` fica legível nos blocos seguintes por `{{json.<chave>}}`. Para dado que
  precisa sobreviver ao bot, gravar em custom field de contato e ler por `{{contact.cf.<id>}}`.
- Limites do `execute_handlers`: máx. 10 handlers, `show` com `value` ≤ 80 caracteres, máx. 25
  botões.
- **`return_url` é entrada não confiável.** Quem recebe o webhook vai fazer um POST autenticado
  nela; se vier forjada, o Bearer da conta vaza. Valide o prefixo
  (`https://<subdominio-da-conta>.kommo.com/api/v4/`) antes de usar.

Modos de falha:

- **(A) sem widget**: nenhum Widget step no modal, o bloco colado aparece como "Etapa adaptada
  (código)", zero execução no webhook, lead travado.
- **(B) widget instalado, mas bloco colado à mão** (sem passar pelo `onSalesbotDesignerSave`):
  importa limpo, renderiza bloco vazio, sem campo editável.
- **(C) POST sai e o `continue` não volta**: o webhook registra execução com `token` e
  `return_url`, e o lead fica parado.

**Saída barata quando o objetivo é só ter dado fresco na hora do envio:** não usar
`widget_request`. Pôr um webhook no Pipeline Digital com atraso, disparando antes do bot; o dado
é regravado em custom field de contato e o bot lê por `{{contact.cf.<id>}}`.
