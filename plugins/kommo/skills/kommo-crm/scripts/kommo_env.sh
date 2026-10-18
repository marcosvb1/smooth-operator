#!/usr/bin/env bash

# Resolvedor de credenciais compartilhado pelos scripts do Kommo.
#
# Config (sem tokens), procurado nesta ordem:
#   1. $KOMMO_CONFIG
#   2. ./.claude/kommo.local.json
#   3. ~/.claude/kommo.local.json
# Formato: {"default_profile": "cliente-a", "profiles": {"cliente-a": {"domain": "<sub>.kommo.com"}}}
#
# Domínio: KOMMO_DOMAIN_<PERFIL> > profiles.<perfil>.domain > KOMMO_DOMAIN
# Token:   KOMMO_ACCESS_TOKEN_<PERFIL> > KOMMO_ACCESS_TOKEN (nunca do arquivo)
# <PERFIL> = nome do perfil em maiúsculas, com '-' trocado por '_'.
#
# Exporta DOMAIN, TOKEN, KOMMO_PROFILE e KOMMO_CONFIG_FILE sem imprimir segredo.

kommo_find_config() {
  if [[ -n "${KOMMO_CONFIG:-}" ]]; then
    [[ -f "$KOMMO_CONFIG" ]] && { printf '%s' "$KOMMO_CONFIG"; return 0; }
    return 1
  fi
  local cand
  for cand in "$PWD/.claude/kommo.local.json" "$HOME/.claude/kommo.local.json"; do
    [[ -f "$cand" ]] && { printf '%s' "$cand"; return 0; }
  done
  return 1
}

kommo_env_key() {
  printf '%s' "$1" | tr '[:lower:]' '[:upper:]' | tr -- '-' '_'
}

kommo_load_credentials() {
  local profile="${1:-}"
  local cfg="" key domain_var token_var n

  cfg=$(kommo_find_config) || cfg=""

  if [[ -z "$profile" && -n "$cfg" ]]; then
    profile=$(jq -r '.default_profile // empty' "$cfg")
    if [[ -z "$profile" ]]; then
      n=$(jq -r '(.profiles // {}) | length' "$cfg")
      if [[ "$n" == "1" ]]; then
        profile=$(jq -r '.profiles | keys[0]' "$cfg")
      elif [[ "$n" -gt 1 ]]; then
        printf 'ERRO: vários perfis em %s e nenhum default_profile; informe o perfil.\n' "$cfg" >&2
        return 2
      fi
    fi
  fi

  DOMAIN=""
  TOKEN=""
  if [[ -n "$profile" ]]; then
    key=$(kommo_env_key "$profile")
    domain_var="KOMMO_DOMAIN_${key}"
    token_var="KOMMO_ACCESS_TOKEN_${key}"
    DOMAIN="${!domain_var:-}"
    TOKEN="${!token_var:-}"
    if [[ -z "$DOMAIN" && -n "$cfg" ]]; then
      DOMAIN=$(jq -r --arg p "$profile" '.profiles[$p].domain // empty' "$cfg")
    fi
  fi
  [[ -n "$DOMAIN" ]] || DOMAIN="${KOMMO_DOMAIN:-}"
  [[ -n "$TOKEN" ]] || TOKEN="${KOMMO_ACCESS_TOKEN:-}"

  if [[ -z "$DOMAIN" ]]; then
    if [[ -n "${KOMMO_CONFIG:-}" && -z "$cfg" ]]; then
      printf 'ERRO: KOMMO_CONFIG aponta para arquivo inexistente: %s\n' "$KOMMO_CONFIG" >&2
    fi
    printf "ERRO: domínio do Kommo não encontrado para o perfil '%s'. Rode /kommo:setup ou defina KOMMO_DOMAIN_<PERFIL>.\n" "${profile:-?}" >&2
    return 2
  fi
  if [[ -z "$TOKEN" ]]; then
    printf "ERRO: token ausente. Defina KOMMO_ACCESS_TOKEN_%s (ou KOMMO_ACCESS_TOKEN).\n" "$(kommo_env_key "${profile:-PERFIL}")" >&2
    return 2
  fi

  [[ "$DOMAIN" =~ ^https?:// ]] || DOMAIN="https://${DOMAIN}"
  # O Kommo exige HTTPS; http:// só aparece nos testes locais (127.0.0.1).
  DOMAIN="${DOMAIN%/}"
  KOMMO_PROFILE="${profile:-default}"
  KOMMO_CONFIG_FILE="$cfg"

  export DOMAIN TOKEN KOMMO_PROFILE KOMMO_CONFIG_FILE
}

# GET com validação de HTTP e um retry em 429. O corpo só sai depois de um 2xx.
kommo_get() {
  local url="${1:?URL obrigatória}"
  local attempt=1 status body

  body=$(mktemp)
  while [[ "$attempt" -le 2 ]]; do
    status=$(curl -g -sS -o "$body" -w '%{http_code}' \
      -K <(printf 'header = "Authorization: Bearer %s"\n' "$TOKEN") \
      -H "Content-Type: application/json" \
      "$url") || {
        rm -f "$body"
        printf 'ERRO: falha de rede em GET %s\n' "$url" >&2
        return 1
      }

    if [[ "$status" -ge 200 && "$status" -lt 300 ]]; then
      cat "$body"
      rm -f "$body"
      return 0
    fi

    if [[ "$status" == "429" && "$attempt" -eq 1 ]]; then
      sleep 1
      attempt=2
      continue
    fi

    rm -f "$body"
    printf 'ERRO: GET %s retornou HTTP %s\n' "$url" "$status" >&2
    return 1
  done
}

# Escrita validada. Nunca faz retry, porque repetir uma escrita pode duplicar
# efeitos; quem chama confere o corpo e depois faz o readback com GET.
kommo_request() {
  local method="${1:?método HTTP obrigatório}"
  local url="${2:?URL obrigatória}"
  local data="${3:-}"
  local status body
  local -a extra=()

  [[ -n "$data" ]] && extra=(--data "$data")
  body=$(mktemp)
  status=$(curl -g -sS -o "$body" -w '%{http_code}' -X "$method" \
    -K <(printf 'header = "Authorization: Bearer %s"\n' "$TOKEN") \
    -H "Content-Type: application/json" \
    ${extra[@]+"${extra[@]}"} \
    "$url") || {
      rm -f "$body"
      printf 'ERRO: falha de rede em %s %s\n' "$method" "$url" >&2
      return 1
    }

  if [[ "$status" -ge 200 && "$status" -lt 300 ]]; then
    cat "$body"
    rm -f "$body"
    return 0
  fi

  rm -f "$body"
  printf 'ERRO: %s %s retornou HTTP %s\n' "$method" "$url" "$status" >&2
  return 1
}

# O Kommo usa HTTP 204 (corpo vazio) para indicar o fim de algumas coleções.
kommo_collection_json() {
  local body="${1:-}"
  local collection="${2:?nome da coleção obrigatório}"
  if [[ -z "$body" ]]; then
    echo '[]'
  else
    echo "$body" | jq -c ".\"_embedded\".\"${collection}\" // []"
  fi
}

kommo_collection_count() {
  kommo_collection_json "${1:-}" "${2:?nome da coleção obrigatório}" | jq 'length'
}
