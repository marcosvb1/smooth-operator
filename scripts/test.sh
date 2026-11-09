#!/usr/bin/env bash
# Roda todos os testes offline do repo (sem rede e sem credenciais). O CI chama este
# arquivo; um teste novo entra aqui.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
rc=0
run() { echo "### $*"; "$@" || { echo "FALHOU: $*"; rc=1; }; echo; }

run bash "$ROOT/plugins/kommo/tests/test_scripts.sh"
run bash "$ROOT/plugins/kommo/skills/kommo-salesbot-builder/tests/run_all.sh"
run python3 "$ROOT/plugins/ads-ops/tests/test_meta_job.py"
run python3 "$ROOT/plugins/smooth-operator/skills/mise-en-place/scripts/check_secrets.py" --self-test
EVAL_DIRS=()
for cases in "$ROOT"/plugins/*/evals/CASES.md "$ROOT"/skills/*/evals/CASES.md; do
  [ -f "$cases" ] && EVAL_DIRS+=("$(dirname "$cases")")
done
run python3 "$ROOT/scripts/eval_cases.py" --check "${EVAL_DIRS[@]}"

[ $rc -eq 0 ] && echo "TODOS OS TESTES PASSARAM" || echo "HÁ TESTES FALHANDO"
exit $rc
