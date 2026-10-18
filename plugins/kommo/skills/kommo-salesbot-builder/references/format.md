# Formato de export do Salesbot do Kommo — referência

Derivado por engenharia reversa de 24 bots reais (known-good, de várias contas) + doc dev oficial,
e conferido em imports reais. O corpus original não é distribuído; os pontos abaixo foram
**provados** pelo `validate.py` (passou nos 24, rejeitou malformados) e pelo `roundtrip.py`
(parse→regenera→diff = identidade nos 24). `tests/run_all.sh` repete as provas num corpus sintético. Onde o formato real diverge da doc
dev, a doc real (export) prevalece — é ela que o import da UI consome.

## 1. Wrapper

```json
{ "type_functionality": 0,
  "model": { "text": "<JSON STRING>", "name": "Nome do bot",
             "positions": "<JSON STRING>", "type": 2 } }
```

- `model.text` e `model.positions` são **JSON codificado como STRING** (escape duplo). Gerar
  sempre por código (`salesbot_model.ir_to_export`) — montar à mão quebra no escape.
- `type_functionality`: 0 no corpus. `model.type`: 2 no corpus.
- Limite: o JSON do bot **não pode exceder 64KB** (doc dev). `validate.py` checa `model.text`.

## 2. `model.text` — a lógica

Objeto keyed por **step-id** (string de inteiro, **arbitrário e não-sequencial** — ex.:
`"0","1","2","42","44","45"`; gaps são normais porque a UI reaproveita/descarta ids), mais um
booleano top-level `"conversation"`. Pode haver outras chaves top-level (ex.: `"error"` =
handler de erro de entrega — ver doc dev).

Cada step:
```json
"42": {
  "question": [ {"handler": "...", "params": {...}}, ... ],
  "block_uuid": "620f5286-6b75-4ca3-b391-bcb2a7139ebc"
}
```
- Arrays possíveis: `question` (ações ao enviar), `answer` (ao receber resposta), `finish` (ao
  concluir). Cada elemento é `{handler, params}`.
- `block_uuid`: UUID que **liga o step ao bloco correspondente em `positions`** (mesma uuid).

## 3. `model.positions` — o grafo visual

Array de blocos. Tipos observados:
- **start**: `id 0`, `step -1`, `type "start"`, action `_start`, `goto.block` → 1º bloco real.
- **static/trigger**: `id null` (ou `-1`), `step -1`, `type "static"`, `code "trigger"`, sem
  actions. Bloco decorativo do gatilho.
- **question**: bloco lógico real. `id` (inteiro arbitrário), `step` (= chave no `text`),
  `type "question"`, `name` (rótulo UI: "Enviar mensagem"/"Pausar"/…), `actions[]` que
  **espelham os handlers do step** (menos o `goto`, que vira `goto.block`), `block_uuid`.
- **finish**: `type "finish"`, action `_stop`. **Terminal.**

Campos por bloco: `id`, `step`, `type`, `name?`, `goto?` (`{"block": <id>}`), `actions[]`,
`block_uuid?`, `links?` (quase sempre `null`/`[]`), e **cosméticos** `x,y,z,width,height`.

> **Cosmético vs. semântico (provado):** `x,y,z,width,height` são **só layout** — `roundtrip.py`
> regenera com auto-layout e o diff semântico continua idêntico nos 24. Tudo o mais é semântico.

## 4. Os dois endereçamentos (fonte nº1 de erro)

| | `text` | `positions` |
|---|---|---|
| chaveado por | **step-id** | posição no array; bloco tem **`id`** próprio |
| salto | handler `goto` `{ "step": N, "type": "question\|answer\|finish" }` | `goto.block` = `<id>` de outro bloco |

`step-id` e `block-id` são **independentes** (o step 0 pode ser block id 1 ou 3; o finish step
1 pode ser block id 7 ou 4). Consistência exigida:
1. Todo step-id do `text` aparece como `.step` de algum bloco em `positions`.
2. `block_uuid` casa entre `text[step]` e o bloco de `positions` com aquele `step`.
3. Todo `goto` no `text` aponta pra um step que existe (chave do `text` **ou** `.step` de um
   bloco — **finish/terminais podem existir só em `positions`**).
4. Todo `goto.block` em `positions` referencia um `id` de bloco existente.

> **Variação por complexidade/versão:** em bots simples, os blocos `start`/`finish`/`trigger`
> existem **só em `positions`** (o `text` só os referencia via goto). Em bots complexos,
> `start`/`_stop`/`trigger` também aparecem como handlers **no `text`**. O validador tolera ambos.

## 4b. Branch encoding em `positions` — via `links` (NÃO só `goto.block`)

Saltos **lineares** usam `goto.block` no bloco. Mas **ramificações** (waits/conditions/distribution)
NÃO usam `goto.block` — explodem em **actions com `links:[{block:B}]`**. Erro nº1 de quem só
olha `goto.block`. (`validate.py` valida `goto.block` **e** todo `action.links[].block`.)

- **waits → `wait` (singular!) em positions.** Um handler `waits` no `text` com N condições vira
  **N actions `wait`** (sort 0..N-1), cada uma só com o `event` em `params.params`; o destino sai
  pra `links:[{block:B}]` (B = id do bloco cujo `.step` == `action.step` da condição). `logic` some.
  O bloco waits **não tem `goto.block`**.
- **conditions.** Cada handler `conditions` vira uma action cujo `params.params.result` é **forçado
  a `[]`** (o goto do `result` sai) e o alvo casado vai pra `links:[{block:B}]`. O `goto` bare final
  (fallback/no-match) do `text` vira o **`goto.block`** do bloco.
- **distribution.** Cada variante vira uma action com `links:[{block:B}]`; `variants` fica `[]` na
  action; `seed_id` (UUID) sobe pro topo do bloco.
- **wait_answer** (text) NÃO existe como action em positions — o destino vira `goto.block` do bloco
  (indistinguível de um goto simples estruturalmente; só o `text` carrega a semântica wait_answer).
- **on_error** do `send_message` é `null` no `text` e **omitido** em positions.

## 5. Catálogo de handlers (real, do corpus)

Totais no corpus: `goto`(468), `action`(244), `conditions`(91), `send_message`(77),
`waits`(55), `trigger`(36), `send_internal`(24), `distribution`(14), `_stop`(7),
`wait_answer`(5), `start`(1). Ações: `change_responsible_user`(113), `set_custom_fields`(72),
`change_status`(54), `change_conversation_status`(3), `set_tag`(2).

### send_message  (≈ "Enviar mensagem"; doc dev chama de `show`/`send_external_message`)
```json
{"handler":"send_message","params":{
  "text":"...", "type":"external", "tag":"", "on_error":null,
  "recipient":{"type":"all_contacts","way_of_communication":"over_all"},
  "chat_sources":[{"id":11111}],
  "is_in_starting_block":true, "create_chat_if_not_exists":true }}
```
- `chat_sources[].id` = **canal de mensageria (específico de conta)**. `recipient.type`:
  `all_contacts`/`main_contact`/`filtered_contacts`.
- 🔴 **`params.type` é o tipo de ENTREGA e vale `"external"`** nos 24 do corpus e em todos os exports
  conferidos em contas reais. **Não confundir com a doc dev**, onde o handler `show` usa `params.type`
  como tipo de CONTEÚDO (`text`/`buttons`/`buttons_url`) + `params.value`. Esse dialeto só vale
  colado num **Custom step (Code)**; num `send_message` compilado ele importa "limpo" e
  **renderiza um bloco VAZIO no construtor**, sem erro em lugar nenhum (medido 02/09/2026).
  `validate.py` agora avisa (`SEND_TYPE`, `SEND_VALUE`).

### Botões — forma real (ground truth de exports reais, 09/2026)

Botão de resposta rápida ("inline"). Ele aparece em **três lugares que têm que casar**:

```jsonc
// 1. positions[].actions[].params.params  — o desenho do botão
"buttons": [{"text": "Confirmar telefone", "type": "inline"}]

// 2. text[step].answer  — o ramo que o clique dispara
"answer": [{"handler": "buttons", "params": [
  {"value": "Confirmar telefone",
   "params": [{"handler": "goto", "params": {"step": 7, "type": "question"}}]}]}]

// 3. positions[].actions[].links  — o alvo, casado por REGEX do rótulo
"links": [{"data": {"regex": "/Confirmar telefone/iu"}, "block": 20}]
```

O rótulo é a chave de junção nos três — mudar o texto do botão sem mudar o regex quebra o ramo
em silêncio. `type: "inline"` **não carrega URL**: é resposta rápida, o clique devolve o texto.
Para entregar link, o padrão que funciona é o link **inline no corpo da mensagem**
(`{{contact.cf.ID}}` dentro do `text`), já usado em bots de produção.
`buttons_url` continua **sem ground truth** — não existe no corpus nem em nenhum export.

### 🔴 `text` e `positions` não carregam o mesmo conteúdo

Num bloco inicial com `template_id`, o **`text` traz só `template_id`** (sem `text`, sem
`buttons`) e o **conteúdo real mora no espelho em `positions`**. São 13 sends assim em 4 bots
known-good do corpus. Consequência prática: **qualquer conclusão sobre conteúdo tirada de um
blob só está errada.** Foi exatamente assim que se concluiu, em 02/09/2026, que "o botão não
está no salesbot" — olhando só o `text` de um bot cujo botão estava em `positions`.

### waits  (≈ "Pausar"; timer/resposta)
```json
{"handler":"waits","params":{"logic":"or","conditions":[
  {"event":{"delay":7200,"action":"ended","source":"timer"},"action":{"step":42,"type":"question"}},
  {"event":{"action":"received","source":"message"},"action":{"step":43,"type":"finish"}}
]}}
```
- Cada condição = um `event` (timer com `delay` em segundos / `message received`) → um `action`
  (salto `{step,type}`). É aqui que a pausa ramifica.

### wait_answer
```json
{"handler":"wait_answer","params":{"type":"question","step":2}}
```

### conditions  (doc dev: `condition` singular — real é plural)
```json
{"handler":"conditions","params":{"logic":"and",
  "conditions":[{"term1":"{{message_text}}","term2":"Olá","operation":"contains","value_type":"custom_value"}],
  "result":[{"handler":"goto","params":{"step":6,"type":"question"}}]}}
```
- `value_type` (`custom_value`/`value`) é campo real não documentado. `result[]` = ramo se verdadeiro.

### action — `name` + `params` aninhados
- **change_status**: `{"name":"change_status","params":{"value":<status_id>,"pipeline_id":<pipeline_id>}}`
  — **`pipeline_id` é obrigatório no real** (doc dev só mostra `value`).
- **set_custom_fields**: `{"name":"set_custom_fields","params":{"type":"lead"|1|2,"value":"...","custom_field":"{{lead.cf.<FIELD_ID>}}"|"custom_fields_id":123,"value_type":"value"}}`
  — cf referenciada por `custom_fields_id` (int) **ou** placeholder `{{lead.cf.ID}}` / `{{lead.cf.ID.ENUM}}`.
- **change_responsible_user**: `{"name":"change_responsible_user","params":{"value":<user_id>,"type":1|2}}`.
- **change_conversation_status**, **set_tag**/`unset_tag` (`{type:1|2,value}`), **add_note**,
  **set_budget**, **subscribe**/`unsubscribe` (`{type:user|group,value:<id>}`), **link**, etc. (ver doc dev).

### distribution  (round-robin; **não documentado** na doc dev)
Distribui ações ciclicamente entre N opções (round robin de leads/responsáveis). Usado nos bots
de distribuição junto com `change_responsible_user`.

### trigger  (ações do Pipeline Digital embutidas)
```json
{"handler":"trigger","params":{"element_type":"lead","trigger":{
  "action":"create_task","handler_code":"amocrm","delay":0,
  "settings":{"task_text":"Atender lead","task_type":"1","responsible_user":"current",...},
  "execution_condition":{"id":45,"name":"execute_trigger"}}}}
```

### send_internal
```json
{"handler":"send_internal","params":{"entity_id":"{{lead.id}}","entity_type":2,"message":"...","user_id":123}}
```

### start  ("Iniciar Salesbot" — encadeia outro bot)
```json
{"handler":"start","params":{"bot":<BOT_ID>}}
```  — `bot` = id de bot (específico de conta).

### goto / _start / _stop
`goto` salta (`{step,type}`). `_start`/`_stop` são as actions dos blocos start/finish.

## 6. Placeholders (no `text`, handler `show`/`send_message`)
`{{contact.name}}`, `{{contact.first_name}}`, `{{lead.id}}`, `{{lead.name}}`, `{{lead.price}}`,
`{{message_text}}`, `{{message_text.email}}`, `{{message_text.phone}}`, `{{origin}}`,
`{{lead.cf.ID}}` / `{{lead.cf.ID.ENUM}}` / `{{contact.cf.ID}}`, `{{lead.responsible.id/name/email}}`,
`{{current_date}}`, `{{rand}}`, `{{regexp./.../}}`, `{{last_validation_result}}`.
Campos de sistema (NÃO checados contra o registro de CF): `{{lead.source_id}}`,
`{{lead.responsible_user_id}}`, `{{talk.type}}`.

**conditions** — operações vistas no corpus: `=`, `!=`, `contains` (conjunto completo desconhecido — §10).
**waits** — além de `timer`/`message`, existe a variante **working-time**: `event.source:"working-time"`,
`action:"start"`, com `settings:{time_from, time_to, week_days}` (carregado também na action `wait` de positions).
**change_conversation_status** — `{"name":"change_conversation_status","params":{"status_action":"close"}}` (não confundir com set_tag).

## 7. IDs específicos de conta (resolver/confirmar — nunca copiar do corpus)

| Kind | Onde | Resolução |
|---|---|---|
| chat_source | `send_message.chat_sources[].id` | **NÃO via API** (`/sources`=204). Lift de bot existente + confirmar |
| pipeline_id | `change_status.params.pipeline_id` | `resolve_ids.py` (leads/pipelines) |
| status_id | `change_status.params.value` | idem (statuses embutidos) |
| custom field | `set_custom_fields.custom_fields_id` / `{{lead.cf.ID}}` | `resolve_ids.py` (leads/contacts custom_fields) |
| enum | `{{lead.cf.ID.ENUM}}` / value de select | idem (enums do cf) |
| user | `change_responsible_user.value`, `subscribe`, `send_internal.user_id` | `resolve_ids.py` (users) |
| bot | `start.params.bot` | exportar/listar bots na conta |

Os 24 exemplos são de **contas estrangeiras** — todos os ids acima são inválidos fora delas.

## 8. Divergências doc dev × real (export)

| Doc dev | Real (export/import) |
|---|---|
| `show` | `send_message` (com `recipient`, `chat_sources`, `create_chat_if_not_exists`) |
| `condition` (singular) | `conditions` (plural) + `value_type` |
| `change_status` só `value` | `value` + `pipeline_id` |
| "Pausa"/timer genérico | handler `waits` com `conditions[].event.{delay,action,source}` |
| (ausente) | `distribution` (round-robin), `trigger` (amocrm), `start.bot` |
| finish implícito | bloco `finish` (positions) / handler `_stop` (text complexo) |

## 9. Invariantes que o `validate.py` aplica

**Estruturais (sempre)** — ERROR: wrapper/model tipados; `text`/`positions` parseiam; steps com
block array; **sync text↔positions** (todo step do text vira bloco; `block_uuid` casa quando ambos
têm); **todo alvo de branch do text resolve** — `goto`, `waits.conditions[].action.step`,
`distribution.variants[].step`, `wait_answer.step`, e `conditions.result[]` (gotos aninhados);
**`goto.block` E todo `action.links[].block` resolvem**; **exatamente 1 bloco start**; ids de bloco
únicos; **`change_status` exige `pipeline_id`**; **`chat_sources[].id` é int** (não string); conflito
`chat_sources`+`send_to_all_chat_sources`; 64KB; limites de botão.
WARN: `GOTO_TYPE_MATCH` (tipo declarado ≠ tipo do bloco alvo); `GOTO_BLOCK_MISSING` (goto type
`answer` pra step sem answer block); `SEND_NO_CHANNEL` (send_message não-inicial sem canal nem
broadcast); `POS_ORPHAN` (bloco question em positions sem step no text); `BLOCK_UUID_DUP`;
`HANDLER_UNK` (handler fora do catálogo conhecido — pode ser válido não-visto).

**Inventário (`--inventory`)** — ERROR: `pipeline_id` existe; **`status_id` pertence ao
`pipeline_id`** (cross-membership; obs.: 142/143 são status de sistema "ganho/perdido" presentes em
TODA pipeline); `custom_fields_id` existe; `change_responsible_user.value`, `send_internal.user_id`,
`trigger.settings.responsible_user` são usuários da conta; `set_custom_fields` valor digit-string em
CF select é enum válido daquele CF; `{{*.cf.ID(.ENUM)}}` resolve; `start.bot` ∈ `inventory.bots`
(se a lista existir). WARN: `chat_source` só limpo se em `chat_sources.confirmed`.

## 10. Perguntas em aberto — resolver no 1º import real

> ✅ **Confirmado no import real (2026-09-02):** `send_message` **com
> `chat_sources` específico** importa e entrega — era o último item aberto de 2026-05-29.
> Confirmado junto: `widget_request` como Custom step importa e renderiza como "Etapa adaptada
> (código)"; ids/uuids sintéticos (`uuid5`) e auto-layout são aceitos; `on_error` apontando pra
> um bloco de ação (tag) importa; bloco `static/trigger` é dispensável.
> ❌ **Refutado no mesmo import:** `send_message` com `params.type` de conteúdo
> (`buttons_url` + `value`) — importa sem erro e renderiza bloco vazio. Ver §5.

> ✅ **Confirmado no import real (2026-05-29):** `set-lead-name` e `post-sale-nurture` (gerados pelo
> `compile.py` → `ir_to_export` com **auto-layout sintético**) importaram **limpos** numa conta real. Logo:
> ids/coords sintéticos SÃO aceitos; `conversation:false` no `text` é aceito; `send_message` **sem**
> `chat_sources` (canal do gatilho) importa OK; multi-step com slot-filling importa OK. O `block_uuid`
> dos templates veio do bot-fonte (não testado omitir). O `send_message` **com** `chat_sources`
> específico foi confirmado depois (bloco acima).

A fase 1 adapta templates (topologia preservada de bots known-good), então estes pontos não
bloqueiam o uso atual. Pontos abaixo ainda não confirmados no import (relevantes pra fase 2):

- **IDs/coords sintéticos**: o importer aceita ids de bloco/action arbitrários e `x/y/z/width/height`
  zerados (auto-layout)? Sentinelas obrigatórios: start id=0, `_start` id=-3, static id=-1.
- **block_uuid**: pode ser omitido/null (servidor regenera) ou é obrigatório em algum caso?
- **synonyms:[]** na action do send_message inicial: obrigatório ou opcional? (só Atendimento mostra).
- **static/trigger block**: realmente opcional pra todos os tipos de gatilho? (2/24 omitem; ambos routers de condição).
- **distribution**: o importer exige mínimo 2 variantes (regra do editor) ou aceita N exatos sem padding?
- **ids/sort duplicados** (presentes no ground truth) sobrevivem ao re-import ou o importer reordena?
- **`conversation` boolean**: obrigatório no `text`? (sempre `false` no corpus).
- **vocabulário**: `value_type` (só `value`/`custom_value` vistos), `operation` de conditions
  (`=`/`contains`/`!=`), `trigger.settings.within-deadline` (`custom`/`0`) — conjuntos completos desconhecidos.
