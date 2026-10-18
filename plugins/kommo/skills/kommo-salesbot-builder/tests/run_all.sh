#!/usr/bin/env bash
# Health check da skill: roda todas as provas offline. Exit 0 só se todas passarem.
# Uso: bash tests/run_all.sh [CORPUS_DIR]
# Sem CORPUS_DIR nem $SALESBOT_CORPUS, monta um corpus sintético (templates compilados +
# viz/sample-bot.export.json). Um corpus de exports reais dá uma prova mais forte.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(dirname "$HERE")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; find "$SKILL" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null' EXIT
export PYTHONDONTWRITEBYTECODE=1

CORPUS="${1:-${SALESBOT_CORPUS:-}}"
if [ -z "$CORPUS" ]; then
  CORPUS="$TMP/corpus"
  python3 "$HERE/make_fixture_corpus.py" "$CORPUS" || exit 1
  echo "(corpus sintético; defina SALESBOT_CORPUS para provar contra exports reais)"
fi
rc=0

echo "### 1/4 validator (positive corpus + negative mutations)"
python3 "$HERE/test_validate.py" --corpus "$CORPUS" || rc=1

echo ""
echo "### 2/4 round-trip fidelity (parse->regenerate->diff + re-validate)"
if python3 "$SKILL/scripts/roundtrip.py" --corpus "$CORPUS" > "$TMP/rt.log" 2>&1; then
  tail -2 "$TMP/rt.log"
else
  cat "$TMP/rt.log"; rc=1
fi

echo ""
echo "### 3/4 template-generation fidelity (compile original values -> projection == source bot)"
python3 "$SKILL/scripts/roundtrip_templates.py" --corpus "$CORPUS" || rc=1

echo ""
echo "### 4/4 compile smoke (each template -> validate, structural only)"
for tpl in "$SKILL"/templates/*.json; do
  name="$(basename "$tpl" .json)"
  # valores mínimos: todo slot obrigatório ganha um placeholder; slots numéricos ganham 1
  vals="$TMP/$name.vals.json"
  python3 - "$tpl" "$vals" <<'PY'
import json,sys
tpl=json.load(open(sys.argv[1])); v={}
for s in tpl.get("slots",[]):
    if not s.get("required"): continue
    v[s["name"]] = 1 if s.get("sentinel") is not None else f"<{s['name']}>"
json.dump(v, open(sys.argv[2],"w"))
PY
  out="$TMP/$name.bot.json"
  if python3 "$SKILL/scripts/compile.py" "$tpl" --values "$vals" --out "$out" >/dev/null 2>&1; then
    echo "  ✓ $name compiles + validates (structural)"
  else
    echo "  ✗ $name FAILED compile/validate"; rc=1
  fi
done

echo ""
[ $rc -eq 0 ] && echo "ALL SKILL PROOFS PASS" || echo "SKILL PROOFS FAILED"
exit $rc
