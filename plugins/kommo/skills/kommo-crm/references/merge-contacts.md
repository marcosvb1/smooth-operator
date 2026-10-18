# Merge (unir) contatos

A API v4 pública **não** tem endpoint de merge. A UI ("unir") usa endpoints internos
autenticados por **sessão (cookies)**, que dá para replicar com `fetch` no contexto da página
logada (por exemplo, com uma extensão de navegador controlada pelo Claude). O resultado é idêntico
ao clique manual quando a consolidação respeita o que o servidor já pré-marca.

Merge é destrutivo (o contato secundário some): passa pelo gate explícito, com a lista de pares e
o contato principal de cada um. Em mais de 10 merges, é BULK.

## Endpoints (POST, form-urlencoded, header `X-Requested-With: XMLHttpRequest`)

1. **`/ajax/merge/contacts/info/`** — body `id[]=A&id[]=B[&id[]=C]` → JSON
   `response.compare_values`. É **read-only** (monta o diálogo). Estrutura por campo → por
   contato → `values[]`:
   - single (NAME, MAIN_USER_ID, DATE_CREATE, cfv de texto): `{value,label,selected}`;
     `selected:true` = default (o principal).
   - multi (TAGS, cfv de telefone): `{value,checked}`; pegar todos os `checked` (união).
   - **LEADS**: `values[0].value` é um objeto `{leadId:{...}}`; juntar as **chaves** de todos os
     contatos (senão os leads se perdem).

2. **`/ajax/merge/contacts/save`** — body com o resultado consolidado → cria job assíncrono
   (HTTP 202; `response.multiactions.set.errors` deve vir `[]`). Chaves do body:
   - `id[]` (cada contato a unir)
   - `result_element[ID]` = contato principal (o `selected` do NAME)
   - `result_element[NAME]`, `[MAIN_USER_ID]`, `[DATE_CREATE]`
   - `result_element[TAGS][]` (cada tag, união)
   - `result_element[cfv][<fieldId>][]` (multi, ex.: telefone) ou `result_element[cfv][<fieldId>]`
     (single)
   - `result_element[LEADS][]` (cada leadId, união — **crítico**)

3. Polling opcional: `GET /ajax/v1/multiactions/status?request[multiactions][status][0][job_id]=<id>`
   (0 → 100%). Dá para só conferir o resultado pela API v4 depois.

## Consolidação

Não invente defaults: **leia `selected`/`checked`** do `compare_values`. O servidor já pré-marca o
principal e a união.

## Verificação (API v4)

`GET /api/v4/contacts/<principal>?with=leads` → conferir leads, tags e campos;
`GET /api/v4/contacts/<secundário>` → 204 = removido.

## Pitfall

Ferramentas de navegador podem bloquear a saída do `compare_values` ou do body como
"cookie/query string". Processe dentro do JS da página e devolva só `{status, ids}`, ou inspecione
pelo schema (chaves e tipos, sem valores).
