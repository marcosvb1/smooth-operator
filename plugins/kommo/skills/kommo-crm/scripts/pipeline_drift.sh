#!/usr/bin/env bash
# pipeline_drift.sh — Compara as etapas reais (API) de um pipeline com um baseline em Markdown
#
# Uso:
#   ./pipeline_drift.sh <perfil> <pipeline_id> [baseline.md]
#
# Baseline default: ${KOMMO_BASELINE_DIR:-./kommo-baselines}/<perfil>_<pipeline_id>.md
# Formato do baseline: references/baseline.template.md (linha **Pipeline:** `nome`
# e uma tabela `| sort | id | nome |`; vale a última tabela do arquivo).
#
# Saída: Markdown no stdout. Exit code:
#   0 = sem drift
#   1 = drift encontrado (não é erro, só sinaliza)
#   2 = pré-requisito ausente (credencial, baseline) ou falha técnica no GET
#
# Compatível com bash 3 (padrão do macOS). Não usa declare -A.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=kommo_env.sh
source "$SCRIPT_DIR/kommo_env.sh"

USAGE="Uso: $0 <perfil> <pipeline_id> [baseline.md]"
PROFILE="${1:-}"
PIPE="${2:-}"
[[ -n "$PROFILE" && -n "$PIPE" ]] || { echo "$USAGE" >&2; exit 2; }
MEM_FILE="${3:-${KOMMO_BASELINE_DIR:-$PWD/kommo-baselines}/${PROFILE}_${PIPE}.md}"

if [[ ! -f "$MEM_FILE" ]]; then
  echo "⚠️  Baseline não encontrado: \`$MEM_FILE\`"
  echo "   Sem baseline para comparar. Rode \`funnel_snapshot.sh\` e crie o baseline a partir de references/baseline.template.md."
  exit 2
fi

# ---- Credenciais
kommo_load_credentials "$PROFILE" || exit 2

# ---- 1. Estado da API
if ! API_DATA=$(kommo_get "${DOMAIN}/api/v4/leads/pipelines/$PIPE"); then
  exit 2
fi
API_NAME=$(echo "$API_DATA" | jq -r '.name')
# Stages com `id|name|sort|editable`
API_TMP=$(mktemp)
if ! kommo_get "${DOMAIN}/api/v4/leads/pipelines/$PIPE/statuses" \
  | jq -r '._embedded.statuses | sort_by(.sort) | .[] | "\(.id)|\(.name)|\(.sort)|\(.is_editable)"' > "$API_TMP"; then
  rm -f "$API_TMP"
  exit 2
fi
API_COUNT=$(grep -c . "$API_TMP" || true)

# ---- 2. Estado do baseline: extrair a última tabela `sort | id | nome`
# Nome do pipeline: pega primeiro texto entre backticks após "Pipeline:" (aceita "hoje nomeado `X` (era `Y`)")
MEM_NAME=$(awk '
  /^\*\*Pipeline:\*\*/ {
    # Pega o texto entre o primeiro par craseado
    line=$0
    while (match(line, /`[^`]+`/)) {
      print substr(line, RSTART+1, RLENGTH-2)
      exit
    }
  }
' "$MEM_FILE")

MEM_TMP=$(mktemp)
awk -f "$SCRIPT_DIR/extract_pipeline_baseline.awk" "$MEM_FILE" > "$MEM_TMP"
MEM_COUNT=$(grep -c "|" "$MEM_TMP" || true)

# ---- 3. Drift
DRIFT=0
REPORT="## Kommo drift check — ${PROFILE} / pipeline ${PIPE}\n\n"
REPORT+="**API:** \`${API_NAME}\` — ${API_COUNT} estágios  \n"
REPORT+="**Baseline:** \`${MEM_NAME:-?}\` — ${MEM_COUNT} estágios (\`${MEM_FILE}\`)  \n\n"

# 3.1 Nome do pipeline
if [[ -z "${MEM_NAME:-}" ]]; then
  REPORT+="### ⚠️ Nome do pipeline não parseado do baseline (regex pode estar defasado)\n\n"
  DRIFT=1
elif [[ "${API_NAME}" != "${MEM_NAME}" ]]; then
  REPORT+="### 📛 Nome do pipeline mudou\n"
  REPORT+="- baseline: \`${MEM_NAME}\`\n- API:      \`${API_NAME}\`\n\n"
  DRIFT=1
fi

# 3.2 Adições/renomeações (itera API stages)
# Normaliza nome: stripa " (SYSTEM)" suffix e whitespace; lowercase via tr (bash 3 safe)
normalize_name() {
  echo "$1" | sed -E 's/[[:space:]]*\(SYSTEM\)[[:space:]]*$//' | sed -E 's/^[[:space:]]+|[[:space:]]+$//' | tr '[:upper:]' '[:lower:]'
}

ADDED=""
RENAMED=""
while IFS='|' read -r sid sname ssort sedit; do
  [[ -z "$sid" ]] && continue
  MEM_LINE=$(grep "^${sid}|" "$MEM_TMP" || true)
  if [[ -z "$MEM_LINE" ]]; then
    ADDED+="- \`${sid}\` → \`${sname}\` (sort ${ssort})\n"
    DRIFT=1
  else
    MEM_SNAME_RAW=$(echo "$MEM_LINE" | cut -d'|' -f2)
    NORM_API=$(normalize_name "$sname")
    NORM_MEM=$(normalize_name "$MEM_SNAME_RAW")
    if [[ "$NORM_API" != "$NORM_MEM" ]]; then
      RENAMED+="- \`${sid}\`: baseline=\"${MEM_SNAME_RAW}\" → API=\"${sname}\"\n"
      DRIFT=1
    fi
  fi
done < "$API_TMP"

# 3.3 Remoções (itera as etapas do baseline)
REMOVED=""
while IFS='|' read -r sid sname ssort; do
  [[ -z "$sid" ]] && continue
  if ! grep -q "^${sid}|" "$API_TMP"; then
    REMOVED+="- \`${sid}\` → \`${sname}\` (não está mais na API)\n"
    DRIFT=1
  fi
done < "$MEM_TMP"

[[ -n "$ADDED"   ]] && REPORT+="### ➕ Estágios adicionados na API (ausentes do baseline)\n${ADDED}\n"
[[ -n "$REMOVED" ]] && REPORT+="### ➖ Estágios removidos da API (órfãos no baseline)\n${REMOVED}\n"
[[ -n "$RENAMED" ]] && REPORT+="### ✏️ Estágios renomeados\n${RENAMED}\n"

# 3.4 Contagem
if [[ "$API_COUNT" -ne "$MEM_COUNT" ]]; then
  REPORT+="### 📊 Contagem divergente\n"
  REPORT+="- API tem **${API_COUNT}** estágios, baseline diz **${MEM_COUNT}**\n\n"
  DRIFT=1
fi

if [[ $DRIFT -eq 0 ]]; then
  REPORT+="### ✅ Sincronizado"
  REPORT+=" — ${API_COUNT} estágios em ambos, nomes coincidem.\n\n"
fi

REPORT+="---\n"
if [[ $DRIFT -eq 1 ]]; then
  REPORT+="**Ação sugerida:** editar \`${MEM_FILE}\` adicionando seção \`## Mudanças desde a snapshot\`. Drift de rename/add via UI não exige o workflow de pipeline design.\n"
fi

echo -e "$REPORT"

# Cleanup
rm -f "$API_TMP" "$MEM_TMP"
exit $DRIFT
