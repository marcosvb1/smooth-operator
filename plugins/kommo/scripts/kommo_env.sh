#!/usr/bin/env bash

# Credenciais e HTTP do plugin kommo: usado pelos scripts das skills, pelo
# /kommo:setup e (via DOMAIN/TOKEN exportados) pelo devserver do widget.
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
# Exporta DOMAIN, TOKEN e KOMMO_PROFILE sem imprimir segredo.

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

  export DOMAIN TOKEN KOMMO_PROFILE
}

# Uma chamada HTTP. Imprime o corpo só em 2xx. Sai com 1 em falha de rede ou
# HTTP de erro, e com 3 em 429 (para o kommo_get decidir se repete).
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
  [[ "$status" == "429" ]] && return 3
  return 1
}

# Leitura: repete uma vez, depois de 1s, se a API devolver 429. Escritas vão
# direto no kommo_request e nunca repetem, porque repetir pode duplicar efeitos.
kommo_get() {
  local url="${1:?URL obrigatória}" rc=0
  kommo_request GET "$url" || rc=$?
  [[ "$rc" -eq 3 ]] || return "$rc"
  sleep 1
  kommo_request GET "$url"
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

# Limite da API: 7 req/s. Quem faz laço de requisições espera isto entre elas.
KOMMO_RATE_SLEEP=0.18

# Pagina uma coleção: imprime cada página como um array JSON (uma linha por página).
# Para no corpo vazio (HTTP 204), na página sem itens ou quando não há _links.next.
# Uso: kommo_paginate "$DOMAIN/api/v4/contacts?limit=250" contacts
kommo_paginate() {
  local url="${1:?URL obrigatória}"
  local collection="${2:?nome da coleção obrigatório}"
  local sep="?" page=1 resp items
  [[ "$url" == *\?* ]] && sep="&"
  while true; do
    resp=$(kommo_get "${url}${sep}page=${page}") || return 1
    items=$(kommo_collection_json "$resp" "$collection")
    [[ "$items" == "[]" ]] && return 0
    printf '%s\n' "$items"
    [[ -n "$(printf '%s' "$resp" | jq -r '._links.next.href // empty')" ]] || return 0
    page=$((page + 1))
    sleep "$KOMMO_RATE_SLEEP"
  done
}

# Leads de uma etapa, paginados (uma linha por página). O filtro por etapa precisa
# de pipeline_id e status_id juntos; status_id sozinho é ignorado pela API.
# Uso: kommo_stage_leads <pipeline_id> <status_id> ["with=source_id"]
kommo_stage_leads() {
  local pipe="${1:?pipeline_id obrigatório}" status="${2:?status_id obrigatório}" extra="${3:-}"
  kommo_paginate "$DOMAIN/api/v4/leads?filter[statuses][0][pipeline_id]=${pipe}&filter[statuses][0][status_id]=${status}${extra:+&$extra}&limit=250" leads
}
