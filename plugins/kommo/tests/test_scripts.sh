#!/usr/bin/env bash
# Testes locais dos scripts do plugin kommo: sem credenciais reais e sem chamadas
# externas (falhas de transporte usam http://127.0.0.1:9, que recusa conexão; o resto
# fala com tests/fake_kommo.py).

set -euo pipefail

TESTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN="$(dirname "$TESTS")"
ENV_SH="$PLUGIN/scripts/kommo_env.sh"
SCRIPT_DIR="$PLUGIN/skills/kommo-crm/scripts"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Isola o teste de configs reais do usuário (./.claude e ~/.claude).
export HOME="$WORK/home"
mkdir -p "$HOME"
cd "$WORK"
unset KOMMO_CONFIG KOMMO_DOMAIN KOMMO_ACCESS_TOKEN || true

bash -n \
  "$ENV_SH" \
  "$SCRIPT_DIR/dump_contacts.sh" \
  "$SCRIPT_DIR/funnel_snapshot.sh" \
  "$SCRIPT_DIR/pipeline_drift.sh" \
  "$PLUGIN/skills/kommo-salesbot-builder/scripts/resolve_ids.sh"

# 1. Domínio e token por perfil vindos do ambiente valem mesmo com KOMMO_CONFIG quebrado.
KOMMO_DOMAIN_CLIENTE_A="example.kommo.com" \
KOMMO_ACCESS_TOKEN_CLIENTE_A="dummy" \
KOMMO_CONFIG="/definitely/missing" \
bash -ec 'source "$1"; kommo_load_credentials cliente-a; [[ "$DOMAIN" == "https://example.kommo.com" && "$KOMMO_PROFILE" == "cliente-a" ]]' _ "$ENV_SH"

# 2. Config local: domínio do perfil + token do ambiente; default_profile quando o perfil é omitido.
mkdir -p "$WORK/.claude"
cat > "$WORK/.claude/kommo.local.json" <<'JSON'
{"default_profile": "cliente-b",
 "profiles": {"cliente-a": {"domain": "a.kommo.com"},
              "cliente-b": {"domain": "https://b.kommo.com/", "access_token": "nunca-usado"}}}
JSON
KOMMO_ACCESS_TOKEN_CLIENTE_B="dummy" \
bash -ec 'source "$1"; kommo_load_credentials; [[ "$DOMAIN" == "https://b.kommo.com" && "$KOMMO_PROFILE" == "cliente-b" ]]' _ "$ENV_SH"

# 3. Token nunca vem do arquivo: sem env, falha com código 2 mesmo com access_token no JSON.
set +e
bash -ec 'source "$1"; kommo_load_credentials cliente-b' _ "$ENV_SH" >/dev/null 2>&1
RC=$?
set -e
[[ "$RC" -eq 2 ]]

# 4. Token genérico serve para qualquer perfil.
KOMMO_ACCESS_TOKEN="dummy" \
bash -ec 'source "$1"; kommo_load_credentials cliente-a; [[ "$DOMAIN" == "https://a.kommo.com" ]]' _ "$ENV_SH"

# 5. Vários perfis sem default_profile e sem perfil informado: pergunta, não escolhe (código 2).
cat > "$WORK/.claude/kommo.local.json" <<'JSON'
{"profiles": {"cliente-a": {"domain": "a.kommo.com"}, "cliente-b": {"domain": "b.kommo.com"}}}
JSON
set +e
KOMMO_ACCESS_TOKEN="dummy" bash -ec 'source "$1"; kommo_load_credentials' _ "$ENV_SH" >/dev/null 2>&1
RC=$?
set -e
[[ "$RC" -eq 2 ]]

# 6. KOMMO_CONFIG tem prioridade sobre ./.claude/kommo.local.json.
echo '{"profiles": {"outro": {"domain": "outro.kommo.com"}}}' > "$WORK/alt.json"
KOMMO_CONFIG="$WORK/alt.json" KOMMO_ACCESS_TOKEN="dummy" \
bash -ec 'source "$1"; kommo_load_credentials; [[ "$DOMAIN" == "https://outro.kommo.com" ]]' _ "$ENV_SH"
rm -f "$WORK/.claude/kommo.local.json"

# 7. Falha de transporte continua sendo falha, não vira relatório vazio.
KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" \
KOMMO_ACCESS_TOKEN_TESTE="dummy" \
bash -ec 'source "$1"; kommo_load_credentials teste; ! kommo_get "$DOMAIN/api/v4/account" >/dev/null 2>&1' _ "$ENV_SH"

# 7d. Config que não é JSON é erro, mesmo com KOMMO_DOMAIN genérico definido.
echo '{quebrado' > "$WORK/bad.json"
set +e
KOMMO_CONFIG="$WORK/bad.json" KOMMO_DOMAIN="z.kommo.com" KOMMO_ACCESS_TOKEN="dummy" \
  bash -c 'source "$1"; kommo_load_credentials' _ "$ENV_SH" >/dev/null 2>&1
RC=$?
set -e
[[ "$RC" -eq 2 ]]
KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" \
KOMMO_ACCESS_TOKEN_TESTE="dummy" \
bash -ec 'source "$1"; kommo_load_credentials teste; ! kommo_paginate "$DOMAIN/api/v4/contacts" contacts >/dev/null 2>&1' _ "$ENV_SH"

# 7b. kommo_paginate segue _links.next, para na página vazia (204) e devolve uma linha por página.
PORT_FILE="$WORK/port"
python3 "$TESTS/fake_kommo.py" "$PORT_FILE" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null; rm -rf "$WORK"' EXIT
for _ in $(seq 50); do [[ -s "$PORT_FILE" ]] && break; sleep 0.1; done
PAGES=$(KOMMO_DOMAIN_TESTE="http://127.0.0.1:$(cat "$PORT_FILE")" KOMMO_ACCESS_TOKEN_TESTE="dummy" \
  bash -ec 'source "$1"; kommo_load_credentials teste; kommo_paginate "$DOMAIN/api/v4/contacts?limit=250" contacts' _ "$ENV_SH")
[[ "$PAGES" == $'[{"id":1}]\n[{"id":2}]' ]]

# 7a. kommo_get repete uma vez em 429; o kommo_request (escrita) nunca repete.
FAKE="http://127.0.0.1:$(cat "$PORT_FILE")"
KOMMO_DOMAIN_TESTE="$FAKE" KOMMO_ACCESS_TOKEN_TESTE="dummy" bash -ec '
  source "$1"; kommo_load_credentials teste
  [[ "$(kommo_get "$DOMAIN/api/v4/busy?id=get1" 2>/dev/null)" == "{\"ok\": true}" ]]
  if kommo_get "$DOMAIN/api/v4/busy?id=get2&n=2" >/dev/null 2>&1; then exit 1; fi
  if kommo_request PATCH "$DOMAIN/api/v4/busy?id=w1" "{}" >/dev/null 2>&1; then exit 1; fi' _ "$ENV_SH"

# 7c. O inventário do salesbot sai do mesmo cliente, com os campos que o validate.py lê.
INV=$(KOMMO_DOMAIN_TESTE="http://127.0.0.1:$(cat "$PORT_FILE")" KOMMO_ACCESS_TOKEN_TESTE="dummy" \
  "$PLUGIN/skills/kommo-salesbot-builder/scripts/resolve_ids.sh" teste 2>/dev/null)
jq -e '.account_id == 1 and .pipelines[0].statuses[1].id == 142 and .users[0].id == 5
  and .lead_custom_fields[0].enums[0].id == 70 and .contact_custom_fields[0].enums == []
  and .chat_sources.confirmed == []' <<<"$INV" >/dev/null

# 7e. Snapshot e drift de ponta a ponta contra o servidor falso (pipeline 10).
export KOMMO_DOMAIN_TESTE="$FAKE" KOMMO_ACCESS_TOKEN_TESTE="dummy"
REPORT_DIR="$WORK/snap" "$SCRIPT_DIR/funnel_snapshot.sh" teste 10 >/dev/null 2>&1
jq -e '._meta.total_active == 3 and ._meta.total_terminal == 1
  and ([.stages[] | {stage_id, leads_count, pct_of_active}] == [
    {stage_id: 100, leads_count: 0, pct_of_active: null}, {stage_id: 101, leads_count: 3, pct_of_active: 100},
    {stage_id: 102, leads_count: 0, pct_of_active: 0}, {stage_id: 142, leads_count: 1, pct_of_active: null}])' \
  "$WORK"/snap/kommo_teste_10_*.json >/dev/null
mkdir -p "$WORK/kommo-baselines"
cat > "$WORK/kommo-baselines/teste_10.md" <<'MD'
**Pipeline:** `Funil`

| sort | id | nome |
|---:|---:|---|
| 10 | 100 | Incoming leads |
| 20 | 101 | a |
| 30 | 102 | B |
| 10000 | 142 | Ganho |
MD
"$SCRIPT_DIR/pipeline_drift.sh" teste 10 >/dev/null
sed -i.bak 's/| 30 | 102 | B |/| 30 | 102 | Antigo |/' "$WORK/kommo-baselines/teste_10.md"
set +e
DRIFT_OUT=$("$SCRIPT_DIR/pipeline_drift.sh" teste 10)
RC=$?
set -e
[[ "$RC" -eq 1 ]] && grep -q 'baseline="Antigo" → API="B"' <<<"$DRIFT_OUT"
unset KOMMO_DOMAIN_TESTE KOMMO_ACCESS_TOKEN_TESTE

# 8. Baseline com tabela histórica e tabela atual: a última tabela vence.
BASELINE="$WORK/kommo-baselines/teste_1000.md"
mkdir -p "$(dirname "$BASELINE")"
cat > "$BASELINE" <<'MD'
# Pipeline de teste

**Pipeline:** `Funil de Teste`

## Estrutura antiga

| sort | id | nome |
|---:|---:|---|
| 10 | 100 | Incoming leads |
| 30 | 102 | tentativa de contato |

## Estrutura atual

| sort | id | nome | cor |
|---:|---:|---|---|
| 10 | 100 | Incoming leads | `#c1c1c1` |
| 20 | 101 | Em Qualificação | `#d6eaff` |
| 10000 | 142 | Venda ganha | `#CCFF66` |
| 11000 | 143 | Venda perdida | `#D5D8DB` |

Texto depois da tabela.
MD
OUT="$WORK/baseline.txt"
awk -f "$SCRIPT_DIR/extract_pipeline_baseline.awk" "$BASELINE" > "$OUT"
[[ "$(wc -l < "$OUT" | tr -d ' ')" == "4" ]]
grep -q '^101|Em Qualificação|20$' "$OUT"
[[ "$(awk -v want=name -f "$SCRIPT_DIR/extract_pipeline_baseline.awk" "$BASELINE")" == "Funil de Teste" ]]
! grep -q '^102|tentativa de contato|30$' "$OUT"

# O template do baseline também precisa ser legível pelo extrator.
awk -f "$SCRIPT_DIR/extract_pipeline_baseline.awk" "$SCRIPT_DIR/../references/baseline.template.md" > "$OUT"
grep -q '^142|' "$OUT" && grep -q '^143|' "$OUT"

# 9. Snapshot com falha de transporte sai com erro e não deixa arquivos.
REPORT_DIR="$WORK/reports"
mkdir -p "$REPORT_DIR"
if KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" KOMMO_ACCESS_TOKEN_TESTE="dummy" REPORT_DIR="$REPORT_DIR" \
  "$SCRIPT_DIR/funnel_snapshot.sh" teste 1 >/dev/null 2>&1; then
  echo "ERRO: snapshot aceitou falha de transporte" >&2
  exit 1
fi
[[ -z "$(ls -A "$REPORT_DIR")" ]]

# 10. Drift reserva o código 1 para drift real; falha técnica no GET devolve 2.
set +e
KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" KOMMO_ACCESS_TOKEN_TESTE="dummy" \
  "$SCRIPT_DIR/pipeline_drift.sh" teste 1000 >/dev/null 2>&1
DRIFT_EXIT=$?
# Baseline ausente também é 2.
KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" KOMMO_ACCESS_TOKEN_TESTE="dummy" \
  "$SCRIPT_DIR/pipeline_drift.sh" teste 999 >/dev/null 2>&1
MISSING_EXIT=$?
set -e
[[ "$DRIFT_EXIT" -eq 2 ]]
[[ "$MISSING_EXIT" -eq 2 ]]

echo "Kommo script tests passed"
