# Kommo API — Pitfalls e falhas silenciosas

A API do Kommo aceita filtros desconhecidos sem retornar erro — só ignora e devolve resultados não-filtrados (parecem certos, mas são lixo). Antes de afirmar "X tem N leads/contatos", validar com endpoint canônico.

## Falhas silenciosas conhecidas

### 1. `filter[contact_id]` em `/leads` — IGNORADO
O Kommo aceita o parâmetro mas devolve leads paginados sem nenhum vínculo com o contato. É fácil ler o resultado como "leads do contato X" e errar.

❌ Não usa:
```
GET /leads?filter[contact_id][]=X
```

✅ Usa:
```
GET /contacts/X?with=leads
```
Retorna `_embedded.leads` com IDs vinculados ao contato. Pra detalhes completos, fazer `GET /leads/{id}` por cima.

---

### 2. `filter[email]` em `/leads` — IGNORADO
Email vive no contato, não no lead.

❌ Não usa:
```
GET /leads?filter[email]=fulano@x.com
```

✅ Usa:
```
GET /contacts?query=fulano@x.com
```

---

### 3. `filter[custom_fields_values][...]` em `/contacts` — IGNORADO
`filter[custom_fields_values]` pode devolver 400; `filter[cf][id]` devolve 200 e ignora o filtro (vem tudo). Pra filtrar contatos por custom field:

✅ **Opção A** — Paginação full (`scripts/dump_contacts.sh`) + filtro client-side com jq:
```bash
jq 'select(.custom_fields["<Nome do campo>"] == "<valor>")' contatos.jsonl
```

✅ **Opção B** — Full-text query (rápido pra valores populares):
```
GET /contacts?query=<valor>
```
O full-text bate em todos os campos textuais, então há falsos positivos; confirme no resultado.

---

### 4. `with=tags` esperando filtro
`with=` é embed (carrega o array), não filtro. Pra filtrar por tag, usar `filter[tags]`/`query=` ou client-side.

---

## Whitelist de filtros que FUNCIONAM em `/leads`

Apenas esses são aceitos — qualquer outro é ignorado silenciosamente:

- `filter[id][]` — por ID
- `filter[name]` — substring
- `filter[price]` ou `filter[price][from/to]`
- `filter[statuses][N][pipeline_id]` + `filter[statuses][N][status_id]`
- `filter[pipeline_id][]`
- `filter[created_at][from/to]`, `filter[updated_at][from/to]`, `filter[closed_at][from/to]` (epoch)
- `filter[responsible_user_id][]`
- `filter[custom_fields_values][FIELD_ID]` (atenção: funciona em `/leads` mas NÃO em `/contacts`)
- `query=` — full-text (documentado; `filter[query]` dá o mesmo resultado, testado em 12/10/2026)

## Regra geral

Se um filtro retorna número que parece "alto demais" ou "estranho demais" pra um contato/email específico, suspeitar — refazer via endpoint da entidade-base (`/contacts/{id}` pra contato, `/leads/{id}` pra lead) com o `with=` correto.

## Outros pitfalls operacionais

- **Rate limit 7 req/s** — em loops, sleep 0.18s entre requests. 429 = sleep 1s e retry.
- **Limite 40 fields/POST** — pra criar muitos custom fields, dividir em batches de 40.
- **DELETE de custom field apaga dados** — irreversível. Sempre confirmar com o operador humano antes.
- **DELETE de funil/etapa** — confirmar antes; afeta leads associados.
- **`filter[source_id]` em `/leads` é ignorado** (devolve a lista inteira), e `source_id` só vem no payload com `with=source_id`. Pra descobrir de que canal é um `source_id`, tabular `source_id` × `pipeline_id` numa amostra (`GET /leads?limit=250&with=source_id`): as pipes em que os leads caem identificam o canal.
- **`_total_items` não é total.** Em `/leads` vem `null`; em `/talks` só espelha a página. Contagem = paginar até acabar.
- **`curl` sem `-g`** com `filter[x][]` falha em silêncio (veja `endpoints.md`).
- **Telefone de WhatsApp no Brasil:** guardar e buscar as duas variantes, com e sem o 9º dígito. Testar só com um DDD dá falso verde.
- **Node da comunidade no n8n × HTTP Request:** resposta vazia (204) é sucesso no node e erro no HTTP Request, e o `filter[pipelines]` do node é ignorado pelo Kommo. Confira o resultado pela API.
- **Token:** fica em variável de ambiente (`KOMMO_ACCESS_TOKEN_<PERFIL>`), nunca em arquivo. Pra rotação, gerar novo token na integração do Kommo e trocar a variável.
