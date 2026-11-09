#!/usr/bin/env bash
# resolve_ids.sh — Inventário de IDs ao vivo de uma conta Kommo (para compile/validate).
#
# O export de Salesbot embute IDs numéricos da conta (pipeline_id, status_id, campo +
# enum, usuário responsável, chat_sources). Eles mudam de conta para conta e nunca
# podem ser copiados de outro bot; este script os resolve na conta-alvo.
#
# Pela API v4 pública saem pipelines, etapas, usuários e campos (+ enums). Os
# chat_sources (ids de canal do amojo) não: /api/v4/sources devolve 204 ou só as
# fontes da própria integração. Com --scan-bots, lista os chat_sources vistos em
# exports existentes para alguém confirmar quais são desta conta.
#
# Credenciais: plugins/kommo/scripts/kommo_env.sh (perfil do config, token no ambiente).
#
# Uso:
#   resolve_ids.sh [perfil] [--out inv.json] [--scan-bots pasta_de_exports]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../scripts/kommo_env.sh
source "$SCRIPT_DIR/../../../scripts/kommo_env.sh"

PROFILE="" OUT="" SCAN=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT="${2:?--out precisa de um caminho}"; shift 2 ;;
    --scan-bots) SCAN="${2:?--scan-bots precisa de uma pasta}"; shift 2 ;;
    -*) echo "Uso: $0 [perfil] [--out inv.json] [--scan-bots pasta]" >&2; exit 2 ;;
    *) PROFILE="$1"; shift ;;
  esac
done

kommo_load_credentials "$PROFILE" || exit $?
API="$DOMAIN/api/v4"

ACCOUNT=$(kommo_get "$API/account")
echo "Resolvendo inventário de $KOMMO_PROFILE ($(jq -r '"\(.name), id \(.id)"' <<<"$ACCOUNT"))..." >&2

PIPELINES=$(kommo_get "$API/leads/pipelines" | jq '[._embedded.pipelines[]
  | {id, name, statuses: [._embedded.statuses[] | {id, name}]}]')
USERS=$(kommo_paginate "$API/users?limit=250" users | jq -s '[.[][] | {id, name, email}]')
fields() {
  kommo_paginate "$API/$1/custom_fields?limit=250" custom_fields \
    | jq -s '[.[][] | {id, name, type, enums: [(.enums // [])[] | {id, value}]}]'
}
LEAD_CF=$(fields leads)
CONTACT_CF=$(fields contacts)

NOTE="chat_sources (ids de canal usados em send_message) não são enumeráveis por /api/v4/sources. Copie o id de um bot que já funciona no mesmo canal DESTA conta, ou confirme com o dono da conta. --scan-bots lista os ids vistos em exports."
# confirmed: ids de canal que alguém conferiu nesta conta; é a única lista que o validate.py aceita.
CHAT=$(jq -n --arg note "$NOTE" '{confirmed: [], note: $note}')
ERR_FILE=$(mktemp)
if SOURCES=$(kommo_get "$API/sources" 2>"$ERR_FILE"); then
  CHAT=$(jq --argjson s "${SOURCES:-null}" \
    '. + {integration_sources: [($s // {})._embedded.sources[]? | {id, name, pipeline_id}]}' <<<"$CHAT")
else
  CHAT=$(jq --arg e "$(cat "$ERR_FILE")" '. + {integration_sources_error: $e}' <<<"$CHAT")
fi
rm -f "$ERR_FILE"
if [[ -n "$SCAN" ]]; then
  SEEN=$(jq -n '[inputs | (input_filename | split("/") | last) as $f
      | (try (.model.text | fromjson) catch {}) | .. | objects
      | .chat_sources? // empty | .[]? | .id? // empty | {id: ., f: $f}]
    | group_by(.id) | map({id: .[0].id, seen_in: (map(.f) | unique)})' "$SCAN"/*.json)
  CHAT=$(jq --argjson seen "$SEEN" '. + {from_existing_bots: $seen}' <<<"$CHAT")
fi

INVENTORY=$(jq -n \
  --arg profile "$KOMMO_PROFILE" --arg domain "$DOMAIN" \
  --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson account "$ACCOUNT" --argjson pipelines "$PIPELINES" --argjson users "$USERS" \
  --argjson lead_cf "$LEAD_CF" --argjson contact_cf "$CONTACT_CF" --argjson chat "$CHAT" \
  '{profile: $profile, account_id: $account.id, account_name: $account.name, domain: $domain,
    resolved_at: $at, pipelines: $pipelines, users: $users,
    lead_custom_fields: $lead_cf, contact_custom_fields: $contact_cf, chat_sources: $chat}')

jq -r '"  pipelines=\(.pipelines | length) statuses=\([.pipelines[].statuses[]] | length) users=\(.users | length) lead_cf=\(.lead_custom_fields | length) contact_cf=\(.contact_custom_fields | length) chat_sources_confirmed=\(.chat_sources.confirmed | length)"' <<<"$INVENTORY" >&2
if [[ -n "$OUT" ]]; then
  printf '%s\n' "$INVENTORY" > "$OUT"
  echo "  gravado em $OUT" >&2
else
  printf '%s\n' "$INVENTORY"
fi
