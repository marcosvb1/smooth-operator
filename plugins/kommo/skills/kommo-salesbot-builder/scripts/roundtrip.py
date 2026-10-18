#!/usr/bin/env python3
"""
roundtrip.py — prove the format model is faithful against the known-good corpus.

For each bot:
  1. semantic_projection(original) == semantic_projection(ir_to_export(parse_to_ir(original)))
     -> the cosmetic set is exactly {x,y,z,width,height}; (de)serialization is lossless.
  2. ir_to_export(parse_to_ir(original)) passes validate.py
     -> regeneration (with fresh auto-layout) yields a structurally-valid, importable bot.

Run:  python3 scripts/roundtrip.py [--corpus DIR]
Exit: 0 iff all bots round-trip and re-validate.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from salesbot_model import parse_to_ir, ir_to_export, semantic_projection, load_export  # noqa: E402

VALIDATE = os.path.join(HERE, "validate.py")
DEFAULT_CORPUS = os.environ.get("SALESBOT_CORPUS")  # tests/run_all.sh builds a synthetic one when unset


def first_diff(a, b, path="$"):
    """Return a human path to the first structural difference, or None."""
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        ka, kb = set(a), set(b)
        if ka != kb:
            return f"{path}: keys differ +{sorted(ka-kb)[:3]} -{sorted(kb-ka)[:3]}"
        for k in a:
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
        return None
    if a != b:
        return f"{path}: {repr(a)[:40]} vs {repr(b)[:40]}"
    return None


def validate_ok(wrapper):
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(p, "w") as fh:
        json.dump(wrapper, fh, ensure_ascii=False)
    try:
        r = subprocess.run([sys.executable, VALIDATE, p, "--json"], capture_output=True, text=True)
        out = json.loads(r.stdout)
    finally:
        os.unlink(p)
    return out["errors"], [f["code"] for f in out["findings"] if f["severity"] == "ERROR"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    args = ap.parse_args()
    if not args.corpus or not os.path.isdir(args.corpus):
        sys.exit("corpus not found: pass --corpus DIR or set SALESBOT_CORPUS "
                 "(tests/run_all.sh builds a synthetic corpus when none is given)")
    files = sorted(f for f in os.listdir(args.corpus) if f.endswith(".json"))

    rt_fail, val_fail = [], []
    for name in files:
        w = load_export(os.path.join(args.corpus, name))
        regen = ir_to_export(parse_to_ir(w))
        d = first_diff(semantic_projection(w), semantic_projection(regen))
        if d:
            rt_fail.append((name, d))
        n_err, codes = validate_ok(regen)
        if n_err:
            val_fail.append((name, codes))
        mark = "✓" if not d and not n_err else "✗"
        extra = "" if not d else f"  RT-DIFF {d}"
        extra += "" if not n_err else f"  VAL {codes}"
        print(f"  {mark} {name}{extra}")

    print()
    print(f"round-trip identity: {len(files)-len(rt_fail)}/{len(files)} | re-validate: {len(files)-len(val_fail)}/{len(files)}")
    ok = not rt_fail and not val_fail
    print("ALL ROUND-TRIP PROOFS PASS" if ok else "ROUND-TRIP PROOF FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
