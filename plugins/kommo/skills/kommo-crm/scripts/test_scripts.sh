#!/usr/bin/env bash
# Testes locais dos scripts: sem credenciais reais e sem chamadas externas
# (as falhas de transporte usam http://127.0.0.1:9, que recusa conexão).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_SH="$SCRIPT_DIR/kommo_env.sh"
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
  "$SCRIPT_DIR/pipeline_drift.sh"

# 1. Domínio e token por perfil vindos do ambiente valem mesmo com KOMMO_CONFIG quebrado.
KOMMO_DOMAIN_CLIENTE_A="example.kommo.com" \
KOMMO_ACCESS_TOKEN_CLIENTE_A="dummy" \
KOMMO_CONFIG="/definitely/missing" \
bash -c 'source "$1"; kommo_load_credentials cliente-a; [[ "$DOMAIN" == "https://example.kommo.com" && "$KOMMO_PROFILE" == "cliente-a" ]]' _ "$ENV_SH"

# 2. Config local: domínio do perfil + token do ambiente; default_profile quando o perfil é omitido.
mkdir -p "$WORK/.claude"
cat > "$WORK/.claude/kommo.local.json" <<'JSON'
{"default_profile": "cliente-b",
 "profiles": {"cliente-a": {"domain": "a.kommo.com"},
              "cliente-b": {"domain": "https://b.kommo.com/", "access_token": "nunca-usado"}}}
JSON
KOMMO_ACCESS_TOKEN_CLIENTE_B="dummy" \
bash -c 'source "$1"; kommo_load_credentials; [[ "$DOMAIN" == "https://b.kommo.com" && "$KOMMO_PROFILE" == "cliente-b" ]]' _ "$ENV_SH"

# 3. Token nunca vem do arquivo: sem env, falha com código 2 mesmo com access_token no JSON.
set +e
bash -c 'source "$1"; kommo_load_credentials cliente-b' _ "$ENV_SH" >/dev/null 2>&1
RC=$?
set -e
[[ "$RC" -eq 2 ]]

# 4. Token genérico serve para qualquer perfil.
KOMMO_ACCESS_TOKEN="dummy" \
bash -c 'source "$1"; kommo_load_credentials cliente-a; [[ "$DOMAIN" == "https://a.kommo.com" ]]' _ "$ENV_SH"

# 5. Vários perfis sem default_profile e sem perfil informado: pergunta, não escolhe (código 2).
cat > "$WORK/.claude/kommo.local.json" <<'JSON'
{"profiles": {"cliente-a": {"domain": "a.kommo.com"}, "cliente-b": {"domain": "b.kommo.com"}}}
JSON
set +e
KOMMO_ACCESS_TOKEN="dummy" bash -c 'source "$1"; kommo_load_credentials' _ "$ENV_SH" >/dev/null 2>&1
RC=$?
set -e
[[ "$RC" -eq 2 ]]

# 6. KOMMO_CONFIG tem prioridade sobre ./.claude/kommo.local.json.
echo '{"profiles": {"outro": {"domain": "outro.kommo.com"}}}' > "$WORK/alt.json"
KOMMO_CONFIG="$WORK/alt.json" KOMMO_ACCESS_TOKEN="dummy" \
bash -c 'source "$1"; kommo_load_credentials; [[ "$DOMAIN" == "https://outro.kommo.com" ]]' _ "$ENV_SH"
rm -f "$WORK/.claude/kommo.local.json"

# 7. Falha de transporte continua sendo falha, não vira relatório vazio.
KOMMO_DOMAIN_TESTE="http://127.0.0.1:9" \
KOMMO_ACCESS_TOKEN_TESTE="dummy" \
bash -c 'source "$1"; kommo_load_credentials teste; ! kommo_get "$DOMAIN/api/v4/account" >/dev/null 2>&1' _ "$ENV_SH"

bash -c 'source "$1"; [[ "$(kommo_collection_count "" contacts)" == "0" ]]; [[ "$(kommo_collection_json "" leads)" == "[]" ]]' _ "$ENV_SH"

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
