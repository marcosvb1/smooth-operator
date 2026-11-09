#!/usr/bin/env bash
# dump_contacts.sh — Paginação completa de contatos do Kommo, com custom fields
#
# Uso:
#   ./dump_contacts.sh <perfil> [output_path]
#
# Exemplo:
#   ./dump_contacts.sh cliente-a contatos.jsonl
#
# Comportamento:
#   - Credenciais via kommo_env.sh (perfil do config + token em variável de ambiente).
#   - Saída em JSONL, 1 contato por linha: id, name, created_at, updated_at, email,
#     phone e `custom_fields` ({"<nome do campo>": "<valor>"}; campos multivalor
#     viram lista). Filtre por custom field depois, com jq: a API ignora
#     filter[custom_fields_values] em /contacts.
#   - O arquivo contém PII. Default em /tmp; não versione nem compartilhe.
#
# Ordem de grandeza: ~10 min para 85 mil contatos.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../../scripts/kommo_env.sh
source "$SCRIPT_DIR/../../../scripts/kommo_env.sh"

PROFILE="${1:?Uso: $0 <perfil> [output_path]}"
OUTPUT="${2:-/tmp/kommo_${PROFILE}_contacts_$(date +%Y%m%d_%H%M%S).jsonl}"

kommo_load_credentials "$PROFILE" || exit $?

echo "==> Perfil:  ${PROFILE}"
echo "==> Domain:  ${DOMAIN}"
echo "==> Output:  ${OUTPUT}"
echo ""

TMP_OUTPUT=$(mktemp)
cleanup() { rm -f "$TMP_OUTPUT"; }
trap cleanup EXIT

PAGE=0
kommo_paginate "${DOMAIN}/api/v4/contacts?limit=250" contacts | while IFS= read -r CONTACTS; do
  printf '%s\n' "$CONTACTS" | jq -c '.[] | {
    id: .id,
    name: .name,
    created_at: .created_at,
    updated_at: .updated_at,
    email: ([.custom_fields_values[]? | select(.field_code == "EMAIL") | .values[0].value] | first),
    phone: ([.custom_fields_values[]? | select(.field_code == "PHONE") | .values[0].value] | first),
    custom_fields: (
      [.custom_fields_values[]?
        | select(.field_code != "EMAIL" and .field_code != "PHONE")
        | {key: (.field_name // (.field_id | tostring)),
           value: ([.values[]?.value] | if length == 1 then .[0] else . end)}]
      | from_entries)
  }' >> "$TMP_OUTPUT"
  PAGE=$((PAGE + 1))
  printf "\rPage %d | %d contatos acumulados" "$PAGE" "$(wc -l < "$TMP_OUTPUT" | tr -d ' ')"
done
TOTAL=$(wc -l < "$TMP_OUTPUT" | tr -d ' ')

echo ""
mv "$TMP_OUTPUT" "$OUTPUT"
trap - EXIT
echo "==> Total: ${TOTAL} contatos"
echo "==> Salvo em: ${OUTPUT}"
echo "==> Tamanho:  $(du -h "$OUTPUT" | cut -f1)"
