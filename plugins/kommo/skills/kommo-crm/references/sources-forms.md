# Fontes de lead (sources) e ingestão de formulários

Para criar fontes de lead registradas e atribuir leads vindos de formulário, n8n ou outra
automação a uma fonte específica. A parte de widget e Worker está na skill
`kommo-widget-builder`.

## 0. GET de sources também é escopado por integração

`GET /api/v4/sources` devolve só as fontes **da integração que chama**. `GET /sources/{id}` de uma
fonte de chat (WhatsApp, Instagram) devolve **204** mesmo com token da própria conta: essas fontes
pertencem às integrações internas de canal do Kommo. Para nomear o `source_id` de uma conversa,
use evidência indireta (tabular `source_id` × `pipeline_id` com `GET /leads?with=source_id`,
sucessão temporal, conhecimento da operação) e mantenha um de-para próprio.

## 1. `POST /api/v4/sources` exige widget

Token de integração privada comum → `400 "Integration needs widget to perform this operation"`.
O widget é só a "chave": depois que a integração tem um widget **instalado**, o token dela cria
sources direto pela API (HTTP 200), sem código no widget para isso. O widget mínimo válido e o
passo a passo estão na skill `kommo-widget-builder`. A location `lead_sources` deixa o widget ser
adicionado como fonte (callback `onAddAsSource(pipeline_id)`).

Body: `[{"name": "...", "external_id": "<slug>", "pipeline_id": <PIPELINE_ID>}]`.
`DELETE /api/v4/sources` com body `[{"id": <ID>}]` funciona (204). Ambos são WRITE.

## 2. Atribuir lead a uma fonte registrada

- ✅ **Confiável: `POST /api/v4/leads/complex`** (ou `/api/v4/leads`) com
  `_embedded.source = {"external_id": "<slug>", "type": "widget"}`. `type` só aceita `"widget"`.
  O lead nasce com `source_id` = a fonte daquele `external_id`.
- ⚠️ **`external_id` é o SLUG da fonte** (ex.: `"site-organico"`), **não o `id` numérico**. Cada
  source tem os dois; pegue o `external_id` em `GET /api/v4/sources`. Passar o `id` falha em
  silêncio: o lead cai na fonte implícita da integração (rótulo = nome da integração).
- ❓ **`unsorted/forms` + `source_uid`: não use para atribuição.** Em teste, tanto com o slug
  quanto com o id numérico, o lead caiu noutra fonte registrada da mesma integração, não na fonte
  alvo. `leads/complex` atribui como esperado.
- 1 integração comum = 1 fonte (o nome da integração); uma integração-widget gerencia várias
  fontes com um token só.

## 3. Não dá para apagar lead pela API

`DELETE /api/v4/leads` e `/contacts` → 405. Para testes, use `unsorted/forms`, que é reversível:
`DELETE /api/v4/leads/unsorted/{uid}/decline?user_id=<ID>` apaga o lead e o contato provisórios.
`POST /leads` direto cria um lead que só sai pela UI.

## 4. Token dedicado

Vale ter uma integração-widget dedicada à ingestão (ex.: "Ingestão de formulários"), com perfil próprio no
`kommo.local.json` e token em `KOMMO_ACCESS_TOKEN_<PERFIL>`. Assim o escopo e a revogação ficam
isolados do token de operação.

## 5. Gerenciar sources a partir de uma UI no Kommo

A sessão do admin (client-side) recebe `400 "Only integrations can access this endpoint"` em
`/api/v4/sources`. Solução: um proxy server-side (Cloudflare Worker) que guarda o token como
secret e só repassa sources + pipelines. O n8n não precisa do Worker: é server-side e fala direto
com o token. Receita completa em `kommo-widget-builder`.

## 6. Long-lived token × OAuth2

- Os dois **coexistem** na mesma integração. Gerar long-lived não quebra o grant OAuth2.
- **Quebra o OAuth2**: "Regenerate secret key" (invalida o client_secret e o refresh para) ou
  desinstalar o widget.
- **Revoga o long-lived**: desinstalar o widget.
- Token OAuth2 da integração-widget também cria sources. OAuth2 com refresh é mais robusto: não
  morre em reinstalação. Se o n8n der 401 depois de mexer no widget, reconecte a credencial
  OAuth2 (refaz o consentimento).
- A aba "Chaves e escopos" some se a URL de redirecionamento estiver vazia: preencha qualquer URL
  válida e salve.

## Receita n8n (leads/complex)

```http
POST https://<subdominio>.kommo.com/api/v4/leads/complex
Authorization: Bearer <token>
Content-Type: application/json
```

```json
[{
  "name": "Lead do formulário X",
  "pipeline_id": <PIPELINE_ID>,
  "_embedded": {
    "source": { "external_id": "<slug-da-fonte>", "type": "widget" },
    "contacts": [{
      "name": "{{name}}",
      "custom_fields_values": [
        { "field_code": "PHONE", "values": [{ "value": "{{phone}}", "enum_code": "WORK" }] },
        { "field_code": "EMAIL", "values": [{ "value": "{{email}}", "enum_code": "WORK" }] }
      ]
    }]
  }
}]
```

No n8n, use HTTP Request com credencial Header Auth (`Authorization: Bearer <token>`), nunca o
token no body ou na URL.
