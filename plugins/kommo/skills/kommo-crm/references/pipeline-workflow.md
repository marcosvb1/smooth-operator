# Workflow detalhado — refactor de pipeline Kommo

Os 6 passos canônicos. Cada um com comando exato e validação esperada.

## Setup inicial

Carregar o helper compartilhado da skill:

```bash
SCRIPT_DIR="${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/scripts"
source "$SCRIPT_DIR/kommo_env.sh"
kommo_load_credentials <perfil>   # perfil do kommo.local.json
API="${DOMAIN}/api/v4"
PIPE=<pipeline_id>
```

Se o pedido for ambíguo entre contas ou pipelines, perguntar antes (não inferir).

## Passo 1 — Snapshot inicial

Sempre rodar antes de qualquer mutação. Salva o ponto pra rollback.

```bash
# Estrutura atual + hints
kommo_get "$API/leads/pipelines/${PIPE}/statuses?with=descriptions" > /tmp/pipe_snapshot.json

# Pipeline settings (pra ver is_unsorted_on, is_main, etc)
kommo_get "$API/leads/pipelines/${PIPE}" > /tmp/pipe_meta.json

# Render
jq -r '._embedded.statuses[] |
  "  sort=\(.sort | tostring | (. + "      ")[0:5])  id=\(.id)  \(.color)  \"\(.name)\"\(if .is_editable == false then "  [SYSTEM]" else "" end)"' \
  /tmp/pipe_snapshot.json
```

Em seguida, contar leads por etapa (pagination até esgotar — `_total_items` é null em `/leads`):

```bash
count_leads() {
  local SID=$1; local PAGE=1; local TOTAL=0
  while true; do
    URL="$API/leads?filter%5Bstatuses%5D%5B0%5D%5Bpipeline_id%5D=${PIPE}&filter%5Bstatuses%5D%5B0%5D%5Bstatus_id%5D=${SID}&limit=250&page=${PAGE}"
    RESP=$(kommo_get "$URL")
    C=$(echo "$RESP" | jq -r '._embedded.leads | length // 0')
    if [[ "$C" == "0" || "$C" == "null" ]]; then break; fi
    TOTAL=$((TOTAL + C))
    if [[ -z "$(echo "$RESP" | jq -r '._links.next.href // empty')" ]]; then break; fi
    PAGE=$((PAGE + 1)); sleep 0.18
  done
  echo "$TOTAL"
}

for SID in $(jq -r '._embedded.statuses[].id' /tmp/pipe_snapshot.json); do
  NAME=$(jq -r --argjson s "$SID" '._embedded.statuses[] | select(.id==$s) | .name' /tmp/pipe_snapshot.json)
  N=$(count_leads "$SID")
  printf "  %-30s %s leads\n" "$NAME" "$N"
  sleep 0.18
done
```

## Passo 2 — Diagnóstico

Procurar e listar pro usuário cada problema que detectar:

| Tipo de problema | Como detectar |
|---|---|
| Naming inconsistente | Mistura Title Case + MAIÚSCULA + lowercase, plurais misturados |
| Etapas duplicadas | Nomes semanticamente próximos (`Reunião inicial` + `COMPARECEU NA REUNIÃO`) ou cuja função se sobrepõe |
| Ordem ilógica | Sort não respeita fluxo (ex: "Visita sem fechamento" vem antes de "Compareceu na reunião") |
| Etapa que deveria ser CF | Estado paralelo à decisão (avaliação, documentação, reagendamento) |
| Etapas órfãs / mortas | 0 leads OU criadas mas sem fluxo passando |
| Cores não-semânticas | Cor não reflete estado (ex: terminal frio com cor quente) |
| Hints faltando ou inconsistentes | `descs=0` em etapas operacionais |
| Sort com gaps grandes | Pode confundir; preferir sequencial 10/20/30 |

Apresentar como tabela explícita pro usuário. Não corrigir antes de mostrar.

## Passo 3 — Proposta de redesenho

Apresentar pro usuário:
- Tabela `etapa antiga → etapa nova` com sort, color, hint, e o que muda
- O que vira CF em vez de etapa (se aplicável)
- O que vai pra "limbo" e migrar depois (pra etapas órfãs)
- Aguardar OK explícito (gate WRITE inegociável)

Se o usuário pedir variações ("e se a gente fizesse X?"), iterar no rascunho. **NÃO aplicar até OK final claro.**

## Passo 4 — Aplicação estrutural

Regras inegociáveis nessa hora (cf. `pipeline-api-quirks.md`):

1. **PATCH em ordem DECRESCENTE de sort** (70 → 60 → 50 → …).
   Por quê: o Kommo não faz cascade shift. Se você pede sort=20 e 20 está ocupado, Kommo realoca SEU registro pro próximo slot livre (não desloca o ocupante). Indo decrescente, cada slot está livre quando chega a vez.

2. **Sempre passar `name + sort + color + descriptions` em cada PATCH.**
   Por quê: omitir `color` faz Kommo resetar pra default amarelo pálido. Omitir `sort` dispara reorder agressivo.

3. **Pular system stages** (`is_editable: false`).
   Por quê: API retorna 400 `NotSupportedChoice` em `path: id` pra qualquer mutação em system stage.

4. **Cores só da palette oficial (21)** — cf. `pipeline-api-quirks.md`. Cores legacy de pipelines antigos rejeitam SET via PATCH.

5. **`descriptions` array de objetos** `{id, level, description}`. Se UPDATE de descrição existente, passar o `id` (pegar do snapshot `?with=descriptions`). Se CREATE, sem id.

6. **1 PATCH por etapa** — não existe batch PATCH em statuses (retorna 405). Sleep 0.18 entre PATCHs (rate limit 7 req/s).

Template do PATCH:

```bash
HINT="<hint>"
PAYLOAD="$(jq -nc \
    --arg n "<nome>" \
    --argjson s <sort> \
    --arg c "<cor>" \
    --argjson did <desc_id_ou_null> \
    --arg h "$HINT" \
    'if $did == null then
       {name:$n, sort:$s, color:$c, descriptions:[{level:"newbie", description:$h}]}
     else
       {name:$n, sort:$s, color:$c, descriptions:[{id:$did, level:"newbie", description:$h}]}
     end')"
RESPONSE=$(kommo_request PATCH "$API/leads/pipelines/${PIPE}/statuses/${SID}" "$PAYLOAD")
echo "$RESPONSE" | jq -e --arg n "<nome>" --arg c "<cor>" --argjson s <sort> \
  '.name == $n and .color == $c and .sort == $s' >/dev/null
READBACK=$(kommo_get "$API/leads/pipelines/${PIPE}/statuses/${SID}?with=descriptions")
echo "$READBACK" | jq -e --arg n "<nome>" --arg c "<cor>" --arg h "$HINT" --argjson s <sort> \
  '.name == $n and .color == $c and .sort == $s and any(.descriptions[]?; .description == $h)' >/dev/null
```

Após cada PATCH, validar HTTP 200 + checar `sort`/`color` do response (Kommo pode realocar — flagar).

## Passo 5 — Migração de leads

Pra cada etapa órfã (que vai sumir), os leads dela precisam de novo destino. 3 padrões:

### Padrão A: bloco único pra etapa nova

Quando todos os leads da etapa órfã têm semântica clara pra ir pra mesma etapa nova.

```bash
# Paginar toda a etapa origem para JSONL antes de escrever
LEADS_TMP=$(mktemp)
PAGE=1
while true; do
  URL="${DOMAIN}/api/v4/leads?filter%5Bstatuses%5D%5B0%5D%5Bpipeline_id%5D=${PIPE}&filter%5Bstatuses%5D%5B0%5D%5Bstatus_id%5D=${FROM}&limit=250&page=${PAGE}"
  RESP=$(kommo_get "$URL")
  N=$(echo "$RESP" | jq '._embedded.leads // [] | length')
  [[ "$N" -eq 0 ]] && break
  echo "$RESP" | jq -c '._embedded.leads[]' >> "$LEADS_TMP"
  [[ -z "$(echo "$RESP" | jq -r '._links.next.href // empty')" ]] && break
  PAGE=$((PAGE + 1)); sleep 0.18
done

# PATCH em lotes de até 250, com readback da resposta antes do próximo lote
TOTAL=$(wc -l < "$LEADS_TMP" | tr -d ' ')
OFFSET=0
while [[ "$OFFSET" -lt "$TOTAL" ]]; do
  BATCH=$(jq -sc --argjson to "$TO" --argjson pipe "$PIPE" --argjson offset "$OFFSET" \
    '[.[$offset:($offset + 250)][] | {id, status_id: $to, pipeline_id: $pipe}]' "$LEADS_TMP")
  RESPONSE=$(kommo_request PATCH "$API/leads" "$BATCH")
  EXPECTED_IDS=$(echo "$BATCH" | jq 'map(.id) | sort')
  echo "$RESPONSE" | jq -e --argjson expected "$EXPECTED_IDS" \
    '([._embedded.leads[].id] | sort) == $expected' >/dev/null

  FILTER=$(echo "$BATCH" | jq -r '.[].id | "filter[id][]=\(.)"' | paste -sd '&' -)
  READBACK=$(kommo_get "$API/leads?${FILTER}&limit=250")
  echo "$READBACK" | jq -e --argjson expected "$EXPECTED_IDS" --argjson to "$TO" --argjson pipe "$PIPE" \
    '([._embedded.leads[].id] | sort) == $expected and all(._embedded.leads[]; .status_id == $to and .pipeline_id == $pipe)' >/dev/null
  OFFSET=$((OFFSET + 250)); sleep 0.18
done
```

### Padrão B: split em categorias

Quando a etapa órfã tem leads com perfis diferentes (ex: panfletagem vs nomes reais vs placeholders). Categorizar e mandar em batches separados.

### Padrão C: caso a caso

Quando o volume é pequeno (<5 leads) ou o destino depende de inspeção individual (notas, mensagens recentes, contatos vinculados). PATCH unitário por lead (`/api/v4/leads/{id}`).

### Validação obrigatória

Após migrar, **SEMPRE confirmar contagem=0 na origem** antes de avançar pro DELETE:

```bash
count_leads "$FROM"  # deve retornar 0
```

## Passo 6 — Delete + validação final

Só executar DELETE com contagem=0 confirmada. Senão lead vira órfão (perde etapa).

```bash
kommo_request DELETE "$API/leads/pipelines/${PIPE}/statuses/${FROM}" >/dev/null
# Espera HTTP 204
```

Snapshot final + render visual:

```bash
kommo_get "$API/leads/pipelines/${PIPE}/statuses?with=descriptions" \
  | jq -r '._embedded.statuses[] |
    "  sort=\(.sort | tostring | (. + "      ")[0:5])  \(.color)  \"\(.name)\"  descs=\((.descriptions // []) | length)\(if .is_editable == false then "  [SYSTEM]" else "" end)"'
```

Comparar com a proposta aprovada no Passo 3. Reportar deltas (se Kommo realocou algum sort fora do alvo, etc).

## Após o refactor — sempre

1. **Atualizar o baseline** — criar/atualizar `./kommo-baselines/<perfil>_<pipeline_id>.md` (modelo em `baseline.template.md`; é o arquivo que o `pipeline_drift.sh` lê) com:
   - Estrutura final (tabela id/nome/sort/cor/hint)
   - Volumes baseline (contagem por etapa na data do refactor)
   - Modelo operacional (manual / automatizado, com / sem tasks)
   - Convenção de naming dos leads
   - Pendências abertas (CFs não criados, automações pendentes, bugs flagados)

2. **Flagar pendências pro usuário** — bugs de import, hints faltantes em system stages (Incoming leads via UI), CFs propostos mas não criados, etc.

## Anti-patterns

- ❌ PATCH em ordem ascendente de sort (vai bagunçar)
- ❌ Omitir `color` no PATCH (Kommo reseta pra amarelo pálido)
- ❌ Tentar renomear system stages (rejeita com 400)
- ❌ Usar cor de pipeline antigo que não está na palette atual (rejeita com 400)
- ❌ Deletar etapa antes de migrar leads (gera órfãos)
- ❌ Esquecer de atualizar o baseline após o refactor (perde o rastro pra próxima conversa)
- ❌ Aplicar sem mostrar o payload pro usuário primeiro (gate WRITE)
