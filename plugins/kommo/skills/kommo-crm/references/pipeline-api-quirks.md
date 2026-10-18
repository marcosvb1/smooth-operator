# Armadilhas da API Kommo v4 — escopadas pra refactor de pipeline

Restrições empíricas de `PATCH /api/v4/leads/pipelines/{pipe}/statuses/{id}`, levantadas em refactors reais de pipeline.

## Schema do Status (8 campos)

```json
{
  "id": int,
  "name": string,
  "sort": int,
  "color": "#hex",
  "type": int,            // 0=normal, 1=system inbox, etc
  "is_editable": bool,
  "pipeline_id": int,
  "account_id": int
}
```

## Hints (descriptions)

Campo `descriptions` (plural) — array de objetos `{id, level, description}`.

```json
"descriptions": [
  { "level": "newbie" | "candidate" | "master", "description": "<até 1000 chars>" }
]
```

- Max 3 por etapa (1 por nível, sem repetir)
- `descriptions` NÃO vem no GET por default — só com `?with=descriptions`
- PATCH disponível só pra usuários admin
- `description` aceita até 1000 caracteres, inclusive emoji
- **Pegadinha:** API aceita silenciosamente campos custom (`description` singular, `hint`, `comment`, `tooltip`, `prompt`, `note`) com HTTP 200 mas ignora. Sempre `descriptions` plural.
- **Pra UPDATE:** passar o `id` da descrição existente (pegar do snapshot)
- **Pra CREATE:** sem `id`

## Palette oficial (21 cores) — única aceita pelo PATCH

Doc: <https://developers.kommo.com/reference/stage-colors>

| Grupo | Hex codes |
|---|---|
| Amarelos/laranjas | `#fffeb2` `#fffd7f` `#fff000` `#ffeab2` `#ffdc7f` `#ffce5a` |
| Vermelhos/rosas | `#ffdbdb` `#ffc8c8` `#ff8f92` |
| Azuis | `#d6eaff` `#c1e0ff` `#98cbff` |
| Verdes | `#ebffb1` `#deff81` `#87f2c0` |
| Roxos/lilás | `#f9deff` `#f3beff` `#ccc8f9` `#eb93ff` |
| Cinzas | `#f2f3f4` `#e6e8ea` |

**Cores LEGACY rejeitadas pelo PATCH** (existem em pipelines antigos mas API recusa SET):
`#ffff99`, `#ffcc66`, `#99ccff`, `#c1c1c1`. Resposta: `400 NotSupportedChoice` em `path: color`.

Cores SYSTEM fixas (não editáveis):
- `#CCFF66` — Venda ganha (id 142)
- `#D5D8DB` — Venda perdida (id 143)
- `#c1c1c1` — Incoming leads (system, mas dá pra desativar pela UI)

## System stages — read-only TOTAL via API

Stages com `is_editable: false` rejeitam **qualquer mutação** via PATCH — `name`, `descriptions`, `color`, etc. Erro: `400 NotSupportedChoice` em `path: id`, mesmo com 1 campo só. UI manual é o único caminho.

Isso inclui **renomear 142/143**. Já foi testado em várias formas de body (`{name}`, `{name,sort}`, `{name,sort,color}`, com e sem `id`) e todas devolvem 400. Um rename que "funcionou" em algum momento foi feito pela UI (engrenagem do pipeline → editar etapa). O nome de 142/143 é por pipeline. Não gaste chamada tentando. PATCH em 143 com `sort: 11000` ainda reclama "between 1 and 10000": ruído do validador, ignore.

IDs fixos em qualquer conta Kommo:
- `142` = Venda ganha (sort 10000)
- `143` = Venda perdida (sort 11000)
- O id de Incoming leads varia por pipeline, mas `type: 1` o identifica.

Pra "remover" Incoming leads: setting `is_unsorted_on: false` no pipeline (UI). API GET expõe o flag mas não é editável via PATCH garantido — verificar caso a caso.

## PATCH em batch não existe pra statuses

`PATCH /pipelines/{id}/statuses` (sem `{status_id}` final) retorna **HTTP 405**. Sempre 1 PATCH por status.

Rate limit: 7 req/s. Usar `sleep 0.18` entre PATCHs. 429 → sleep 1s + retry.

## Sort — reordenamento agressivo

**Sem `sort` explícito**, Kommo realoca o status (geralmente pro fim da fila). Sempre passar `sort` explícito.

**Sorts altos (>100) são normalizados** — enviando 200/210/220/230, o Kommo realocou em 70/80/90/100 sequenciais. Útil pra empurrar pro fim sem se preocupar com slot exato.

**Kommo NÃO faz cascade shift em PATCH sort.** Se você pede sort=20 mas 20 está ocupado, Kommo realoca SEU registro pro próximo slot livre. **Solução: PATCH em ordem DESCRESCENTE de sort** (70 → 60 → 50 → …) pra cada slot estar livre quando peço.

**System stages ocupam sort permanentemente.** Incoming leads (10), Venda ganha (10000), Venda perdida (11000) bloqueiam esses slots mesmo desativados. Etapas editáveis começam efetivamente em sort=20 mínimo se Incoming existir.

## PATCH em batch de LEADS sim existe

Endpoint `PATCH /api/v4/leads` (sem `{id}` final) aceita array de objetos:

```json
[
  {"id": <LEAD_ID_1>, "status_id": <STATUS_ID>, "pipeline_id": <PIPELINE_ID>},
  {"id": <LEAD_ID_2>, "status_id": <STATUS_ID>, "pipeline_id": <PIPELINE_ID>}
]
```

Pode incluir `name` no body pra rename simultâneo. Útil em migração + padronização de naming.

## Padrão seguro de refactor em lote

1. **Snapshot** atual via `GET /pipelines/{id}/statuses?with=descriptions` — salvar o payload original (rollback).
2. **Empurrar etapas "limbo" pra sort alto primeiro** (libera os slots baixos).
3. **PATCH na ordem alvo decrescente** (40 → 30 → 20) pra evitar swap.
4. **Sempre `name + sort + color + descriptions` explícitos** em cada PATCH.
5. **Cores só da palette de 21.**
6. **System stages: pular** (`is_editable: false` no snapshot).
7. **Snapshot final** + diff com a proposta aprovada.

## DELETE de status

```bash
DELETE /api/v4/leads/pipelines/{pipe}/statuses/{id}
# Espera HTTP 204
```

**Leads ficam órfãos** se etapa for deletada com leads ainda lá. SEMPRE migrar antes + confirmar contagem=0.

## Padrão de payload seguro pra cada PATCH

Sempre incluir `name + sort + color + descriptions` no PATCH (mesmo campos que "não quero mudar") — Kommo reseta o que não vier.

```bash
curl -X PATCH "${DOMAIN}/api/v4/leads/pipelines/${PIPE}/statuses/${SID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<nome>",
    "sort": <sort>,
    "color": "<cor_da_palette>",
    "descriptions": [{"id": <desc_id_se_update>, "level": "newbie", "description": "<hint>"}]
  }'
```

## Reversibilidade

- `name` / `sort` / `color` / `descriptions` → PATCH puro, reversível.
- Leads não perdem dado em refactor — só mudam `status_id` (que é referência, não conteúdo).
- **Exceção: DELETE de etapa** = irreversível pela API (etapa é destruída + leads ficariam órfãos). Sempre migrar leads PRIMEIRO.

## Validação após qualquer PATCH

Sempre conferir no response:
- `HTTP 200`
- `name` retornado bate com o solicitado
- `sort` retornado bate (se diferente, Kommo realocou — flagar)
- `color` retornado bate (se ficou `#fffeb2` = default reset, foi rejeitado)
- `descriptions` count bate

Se algum bate ≠, NÃO seguir pra próximo PATCH — diagnosticar primeiro.

## Armadilha de quoting jq

Em `jq -r '... "...\(expr)..." ...'`, a regra:
- **String literal jq** (`"..."`): `\"` pra aspa literal
- **Código jq** (dentro de `\(...)`): `"` direto, SEM escape

Erro recorrente: copiar `\"...\"` de uma string externa pra dentro de uma interpolação → `jq: INVALID_CHARACTER`. Se precisar de literal string dentro da interpolação, escreva `"array"` (não `\"array\"`).
