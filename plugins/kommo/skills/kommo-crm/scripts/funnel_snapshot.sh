#!/usr/bin/env bash
# funnel_snapshot.sh — Volume de leads por etapa de um pipeline do Kommo (read-only)
#
# Uso:
#   ./funnel_snapshot.sh <perfil> <pipeline_id> [--with-leads]
#
# Exemplos:
#   ./funnel_snapshot.sh cliente-a 1234567
#   ./funnel_snapshot.sh cliente-a 1234567 --with-leads
#
# Saída (em $REPORT_DIR, default ./kommo-reports):
#   kommo_<perfil>_<pipeline_id>_<ts>.json       — payload + _meta
#   kommo_<perfil>_<pipeline_id>_<ts>.csv        — 1 linha por etapa
#   kommo_<perfil>_<pipeline_id>_<ts>.md         — resumo em Markdown
#   kommo_<perfil>_<pipeline_id>_<ts>_leads.csv  (só com --with-leads) — leads ativos, contém PII
#
# Comportamento:
#   - Credenciais via kommo_env.sh (perfil do config + token em variável de ambiente).
#   - GET /pipelines/{id}/statuses (1 req) para listar as etapas.
#   - Para cada etapa (editável e de sistema), pagina
#     /leads?filter[statuses][0][pipeline_id]=...&filter[statuses][0][status_id]=...
#     filter[status_id]=ID direto é IGNORADO em silêncio; só a sintaxe aninhada funciona.
#   - Rate limit 7 req/s: sleep 0.18 entre páginas.
#   - 204 ou `_embedded.leads` vazio encerra o loop.
#
# Compatível com bash 3 (padrão do macOS). Não usa declare -A.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=kommo_env.sh
source "$SCRIPT_DIR/kommo_env.sh"

USAGE="Uso: $0 <perfil> <pipeline_id> [--with-leads]"
PROFILE="${1:?$USAGE}"
PIPE="${2:?$USAGE}"
WITH_LEADS=0
[[ "${3:-}" == "--with-leads" ]] && WITH_LEADS=1
[[ "$PIPE" =~ ^[0-9]+$ ]] || { echo "ERRO: pipeline_id deve ser numérico ($PIPE)" >&2; exit 1; }

# ---- Credenciais
kommo_load_credentials "$PROFILE" || exit $?

# ---- Diretório de saída
OUTPUT_DIR="${REPORT_DIR:-$PWD/kommo-reports}"
mkdir -p "$OUTPUT_DIR"
TS=$(date +%Y%m%d_%H%M%S)
BASE="$OUTPUT_DIR/kommo_${PROFILE}_${PIPE}_${TS}"
JSON_OUT="${BASE}.json"
CSV_OUT="${BASE}.csv"
MD_OUT="${BASE}.md"
LEADS_OUT="${BASE}_leads.csv"

SLEEP=0.18
API="${DOMAIN}/api/v4"

# ---- Pipeline meta
echo "→ GET $API/leads/pipelines/$PIPE" >&2
PIPE_DATA=$(kommo_get "$API/leads/pipelines/$PIPE")
PIPE_NAME=$(echo "$PIPE_DATA" | jq -r '.name')
echo "  pipeline: $PIPE_NAME" >&2

# ---- Statuses (sort)
echo "→ GET $API/leads/pipelines/$PIPE/statuses" >&2
STATUSES_JSON=$(kommo_get "$API/leads/pipelines/$PIPE/statuses?with=descriptions" | jq '._embedded.statuses | sort_by(.sort)')
STAGE_COUNT=$(echo "$STATUSES_JSON" | jq 'length')
echo "  $STAGE_COUNT estágios" >&2

# ---- Each status: paginate /leads com syntax correta filter[statuses][0][...]
ROWS_FILE=$(mktemp)
: > "$ROWS_FILE"
SUCCESS=0
cleanup() {
  rm -f "$ROWS_FILE"
  if [[ "$SUCCESS" -eq 0 ]]; then
    rm -f "$JSON_OUT" "$CSV_OUT" "$MD_OUT" "$LEADS_OUT"
  fi
}
trap cleanup EXIT

# Escreve header CSV de leads se --with-leads
if [[ "$WITH_LEADS" -eq 1 ]]; then
  echo "pipeline_id,pipeline_name,stage_id,stage_name,lead_id,lead_name,created_by,responsible_user_id,created_at,updated_at,source_id" > "$LEADS_OUT"
fi

for ((i=0; i<STAGE_COUNT; i++)); do
  SID=$(echo "$STATUSES_JSON" | jq -r ".[$i].id")
  SNAME=$(echo "$STATUSES_JSON" | jq -r ".[$i].name")
  SEDIT=$(echo "$STATUSES_JSON" | jq -r ".[$i].is_editable")
  SSORT=$(echo "$STATUSES_JSON" | jq -r ".[$i].sort")

  # Pagina até 204 / null / array vazio
  PAGE=1
  COUNT=0
  while true; do
    URL="$API/leads?filter[statuses][0][pipeline_id]=${PIPE}&filter[statuses][0][status_id]=${SID}&with=source_id&limit=250&page=${PAGE}"
    RESP=$(kommo_get "$URL")
    PAGE_LEADS=$(kommo_collection_json "$RESP" leads)
    N=$(echo "$PAGE_LEADS" | jq 'length')
    # Vazio → para
    if [[ -z "$RESP" || "$RESP" == "{}" || "$N" -eq 0 ]]; then
      break
    fi
    COUNT=$((COUNT + N))

    if [[ "$WITH_LEADS" -eq 1 && "$SEDIT" == "true" ]]; then
      echo "$PAGE_LEADS" | jq -r --arg pipe "$PIPE" --arg pname "$PIPE_NAME" --arg sid "$SID" --arg sname "$SNAME" \
        '.[] | [$pipe, $pname, $sid, $sname, .id, (.name | gsub("\n";" ") | gsub(",";"")), (.created_by | tostring), (.responsible_user_id | tostring), (.created_at | tostring), (.updated_at | tostring), (.source_id | tostring)] | @csv' >> "$LEADS_OUT"
    fi

    NEXT=$(echo "$RESP" | jq -r '._links.next.href // empty')
    [[ -z "$NEXT" ]] && break
    PAGE=$((PAGE + 1))
    sleep $SLEEP
  done

  echo "  ✓ $SNAME (sort=$SSORT, editable=$SEDIT) → $COUNT" >&2
  # JSON por linha, pego depois
  jq -n --argjson sid "$SID" --arg sname "$SNAME" --argjson sedit "$SEDIT" --argjson ssort "$SSORT" --argjson count "$COUNT" \
    '{"stage_id":$sid, "name":$sname, "sort":$ssort, "editable":$sedit, "leads_count":$count}' >> "$ROWS_FILE"
done

# ---- Agrega
ROWS_JSON=$(jq -s '.' "$ROWS_FILE")

# ---- Totais
TOTAL_ACTIVE=$(echo "$ROWS_JSON" | jq '[.[] | select(.editable==true)] | map(.leads_count) | add // 0')
TOTAL_TERMINAL=$(echo "$ROWS_JSON" | jq '[.[] | select(.editable!=true)] | map(.leads_count) | add // 0')

# pct_of_active (só faz sentido pros editáveis; terminais = null/"—")
ROWS_JSON=$(echo "$ROWS_JSON" | jq --argjson total "$TOTAL_ACTIVE" \
  'map(. + {"pct_of_active": (if (.editable==true and $total > 0) then ((.leads_count * 100 / $total) | floor) else null end)})')

# ---- JSON out
META=$(jq -n \
  --arg profile "$PROFILE" --arg domain "$DOMAIN" \
  --argjson pipe "$PIPE" --arg pname "$PIPE_NAME" \
  --argjson total_active "$TOTAL_ACTIVE" --argjson total_terminal "$TOTAL_TERMINAL" \
  --arg ts "$TS" \
  '{profile: $profile, domain: $domain, pipeline_id: $pipe, pipeline_name: $pname, total_active: $total_active, total_terminal: $total_terminal, snapshot_at: $ts}')

jq -n --argjson meta "$META" --argjson stages "$ROWS_JSON" \
  '{_meta: $meta, stages: $stages}' > "$JSON_OUT"

# ---- CSV
{
  echo "pipeline_id,pipeline_name,sort,stage_id,stage_name,editable,leads_count,pct_of_active"
  echo "$ROWS_JSON" | jq -r --arg pipe "$PIPE" --arg pname "$PIPE_NAME" \
    'sort_by(.sort) | .[] | [$pipe, $pname, (.sort|tostring), (.stage_id|tostring), .name, (.editable|tostring), (.leads_count|tostring), (.pct_of_active // "" | tostring)] | @csv'
} > "$CSV_OUT"

# ---- MD summary
BIGGEST=$(echo "$ROWS_JSON" | jq -r '[.[] | select(.editable==true)] | sort_by(-.leads_count) | .[0] | "\(.name) (\(.leads_count))"')

{
  echo "# Kommo Funnel Snapshot — ${PROFILE} / ${PIPE_NAME}"
  echo ""
  echo "**Snapshot:** $(date -u +%Y-%m-%dT%H:%M:%SZ)  "
  echo "**Pipeline:** \`${PIPE}\` — ${PIPE_NAME}  "
  echo "**Domain:** \`${DOMAIN}\`  "
  echo "**Perfil:** \`${PROFILE}\`  "
  echo ""
  echo "**Volumes:** ${TOTAL_ACTIVE} ativos (negócio editáveis) · ${TOTAL_TERMINAL} em system stages (Incoming + 142/143) · **$((TOTAL_ACTIVE + TOTAL_TERMINAL)) total**"
  echo ""
  echo "## Etapas (ordenadas por sort)"
  echo ""
  echo "| sort | id | etapa | editável | leads | % ativos |"
  echo "|---:|---:|---|:--:|---:|---:|"
  echo "$ROWS_JSON" | jq -r --argjson total "$TOTAL_ACTIVE" \
    'sort_by(.sort) | .[] | "| \(.sort) | \(.stage_id) | \(.name) | \(.editable) | \(.leads_count) | \(if .pct_of_active then "\(.pct_of_active)%" else "—" end) |"'
  echo ""
  echo "**Maior volume ativo:** ${BIGGEST}"
  echo ""
  echo "## Próxima ação sugerida"
  echo ""
  echo "- Para comparar com um baseline salvo, rode \`scripts/pipeline_drift.sh $PROFILE $PIPE\`."
  echo "- Snapshot JSON: \`$JSON_OUT\`  "
  echo "- CSV analítico: \`$CSV_OUT\`"
  if [[ "$WITH_LEADS" -eq 1 ]]; then
    echo "- Leads (PII): \`$LEADS_OUT\`"
  fi
} > "$MD_OUT"

# ---- Cleanup
SUCCESS=1
rm -f "$ROWS_FILE"

echo "" >&2
echo "→ Salvo:" >&2
echo "  $JSON_OUT" >&2
echo "  $CSV_OUT" >&2
echo "  $MD_OUT" >&2
[[ "$WITH_LEADS" -eq 1 ]] && echo "  $LEADS_OUT  (PII)" >&2
echo "" >&2

cat "$MD_OUT"
