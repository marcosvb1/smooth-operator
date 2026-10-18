# Conversas: Talks API, Chats API add-on e Events API

Para ler conversas de chat (WhatsApp, Instagram etc.) e o histórico de atividade. Os três se
completam: `/talks` dá o **estado** da conversa (quem, onde, aberta ou fechada), `/events` dá o
**quando** (criada, respondida, SLA estourado, mensagem recebida/enviada) e o add-on de Chats dá o
**texto** das mensagens.

## `GET /api/v4/talks` — lista de conversas

- **Params**: `page`, `limit` (máx. 250), `filter[talk_id][]`, `filter[contact_id][]`,
  `filter[entity_id][]` + `filter[entity_type]=lead`, `filter[only_in_work]`.
- **Objeto talk**: `talk_id`, `created_at`/`updated_at` (unix), `rate` (nota NPS do bot),
  `contact_id`, `chat_id` (uuid do canal), `entity_id` + `entity_type`, `status`, `is_in_work`,
  `is_read`, `origin`, `source_id`, `account_id`. `_embedded` traz `contacts[]`, `leads[]` e
  `customers[]` (módulo Clientes/recorrência).
- **`status`**: `in_work` / `closed` / `nps_scheduled` / `nps_in_progress` / `with_error`.
- Ordena por `talk_id` desc. Um `chat_id` pode ter N talks: cada reabertura é um talk novo.

Fatos não óbvios:

- **Aqui os filtros são honrados.** `filter[contact_id][]` e `filter[entity_id]` +
  `entity_type=lead` funcionam, ao contrário de `filter[contact_id]` em `/leads`.
- **`_total_items` mente**: só espelha a contagem da página. E `_page`/`_links.next` podem vir
  `null` mesmo com página cheia. Varredura completa = paginar às cegas (`page+1` até vir vazio).
- **`origin` = tipo de canal** (`waba`, `instagram_business`, `telegram`...).
- **`/talks` não traz texto de mensagem.** `with=messages`/`with=chat` são ignorados, e o corpo da
  mensagem também não fica em notes. Texto = webhooks em tempo real ou o add-on abaixo.

## Chats API add-on — texto das mensagens

Mesmo `talk_id` e mesmo Bearer/OAuth2 da API v4 (não é o esquema separado da Chats API clássica,
por `scope_id`).

- **`GET /api/v4/talks/{talk_id}/messages`** — escopo "External chat history". Retorna `text`,
  `type` (incoming/outgoing), `message_type` (text/contact/file/video/picture/voice/audio/sticker/
  location), `author{id,type:internal|external|bot,name,user_id}`, `recipient`, `origin`,
  `delivery_status`, `attachment{type,link,file_name}` e timestamps. Paginado, aceita
  `filter[created_at][from/to]`. **Grátis.**
- **Ordem**: pagina do mais recente para o mais antigo. Para pegar a 1ª mensagem do talk, use
  `filter[created_at][from/to]` com janela colada no `created_at` do talk, não `page=1`.
- **`POST /api/v4/talks/{talk_id}/send_message`** — escopo "Sending to external chats". Body só
  `{text}`. Resposta 202 assíncrona `{id}`. **Consome cota paga.** 422 se o talk já está fechado.
  É WRITE: passa pelo gate.
- **Escopos**: habilitar em "Chaves e escopos" da integração, categoria "Chats". Quem já autorizou
  via OAuth2 precisa re-autorizar para pegar os escopos novos. Um 403 "Invalid scope" é escopo
  faltando na integração, não falta do recurso no plano.
- **Plano**: só Pro/Enterprise. Leitura (GET) e recebimento (webhook) são grátis; envio consome
  cota (Pro inclui um volume mensal sem acúmulo; há pacotes extras). Confira os valores atuais
  na doc do Kommo.
- **Escopo por token**: tokens de integrações diferentes na mesma conta podem enxergar coisas
  diferentes (uma integração-widget pode só servir para `/talks/{id}/messages`). Se um endpoint
  devolve vazio com um token e dados com outro, é escopo, não ausência de dado.
- **Atribuição de anúncio CTWA pelo conteúdo**: a 1ª mensagem recebida com texto idêntico entre
  vários contatos costuma ser o texto pré-preenchido do anúncio; mensagem renderizada como "This
  message type can't be displayed" costuma ser o cartão de referral do anúncio.

## Webhooks de mensagem

- `add_message`: mensagem recebida (contato → Kommo), com `message_type`.
- `add_outgoing_message`: mensagem enviada por usuário do Kommo **ou Salesbot**. Payload
  `{"outgoing_message":{"add":[{id, message_type, type:"outgoing", origin}]}}`.

## `GET /api/v4/events` — histórico de atividade

Doc oficial: <https://developers.kommo.com/reference/events-types>. `GET /api/v4/events/types`
lista os tipos da conta (inclui um `custom_field_<id>_value_changed` por campo). Os de conversa:

| key | type | descrição |
|---|---|---|
| `talk_created` | 119 | Conversa iniciada |
| `talk_closed` | 120 | Conversa encerrada |
| `conversation_answered` | 135 | Conversa respondida |
| `talk_missed_event` | 122 | Tempo de resposta excedido (SLA estourado, nativo) |
| `incoming_chat_message` | 89 | Mensagem recebida |
| `outgoing_chat_message` | 90 | Mensagem enviada |

### Formato

Eventos de talk são **ponteiros nus**: `entity_id` = `talk_id`, `entity_type: "talk"`,
`value_after`/`value_before` vazios e `_embedded.entity` = `[]`. O join com `/talks` é obrigatório.
`created_by` = `0` para eventos de sistema e traz o user id em `conversation_answered` (é a
atribuição de quem respondeu).

```json
{ "id": "01k...", "type": "talk_created", "entity_id": 48421, "entity_type": "talk",
  "created_by": 0, "created_at": 1784669208,
  "value_after": [], "value_before": [], "_embedded": {"entity": []} }
```

Eventos de mensagem **carregam o talk_id**, e é isso que destrava a análise:

```json
"value_after": [{"message": {"id": "<uuid>", "origin": "waba", "talk_id": 48421}}]
```

Aqui `entity_type` é `lead` ou `customer`, não `talk`.

### Gotchas de filtro

- **`filter[created_at][to]` sozinho devolve 0 sempre.** `[from]` sozinho funciona; `[from]` +
  `[to]` juntos funcionam. Sempre parear, senão parece que não há retenção.
- **Colchetes no shell**: no zsh, `filter[type][]=x` sem aspas vira glob e a query sai vazia.
  URL-encode (`filter%5Btype%5D%5B%5D=`) ou `urlencode(..., doseq=True)` no Python.
- **Paginar às cegas**: `limit` máx. 250, `page+1` até vir vazio. Eventos vêm do mais novo para o
  mais antigo.
- **Retenção** é limitada (da ordem de um ano e pouco numa conta medida). Meça com janelas
  `from`+`to` antes de prometer histórico.

### `talk_id` é sequencial por conta

Duas contas diferentes têm faixas de `talk_id` que colidem. Qualquer tabela multi-conta chaveada
em talk_id precisa de chave composta `(account_id, talk_id)`.

### Join `talk_id` → contato/lead

`GET /api/v4/talks?filter[talk_id][]=...` resolve em lote (até 250 por request).

- **Ancore em `contact_id`, não em lead**: uma parte dos talks aponta para `customer` (cliente
  recorrente); chavear só por lead perde esses em silêncio.
- **Um contato gera N talks.** "Conversas criadas" ≠ "pessoas que falaram"; a segunda métrica exige
  dedupe por `contact_id`.

### Direção: entrada × saída

1. Puxar `incoming_chat_message` + `outgoing_chat_message` da janela.
2. Extrair `value_after[0].message.talk_id`.
3. Pegar a mensagem **mais antiga** de cada talk_id.
4. `incoming` = o cliente falou primeiro (ENTRADA); `outgoing` = a empresa falou primeiro (SAÍDA).

**Sem separar direção, a métrica mente.** Picos de `talk_created` costumam ser disparo em massa,
não demanda. E SLA calculado sobre o total vira lixo: conversa de disparo entra no denominador e
não é para ser respondida. Filtre para ENTRADA antes de medir SLA de primeira resposta.

Contas em que um único usuário "operacional" responde quase tudo não permitem ranking por
vendedor: confira a distribuição de `created_by` antes de prometer essa análise.
