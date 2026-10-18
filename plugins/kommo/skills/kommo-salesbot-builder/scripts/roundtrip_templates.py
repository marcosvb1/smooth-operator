#!/usr/bin/env python3
"""
roundtrip_templates.py — prove the GENERATION path is faithful (not circular).

"compile -> passes validate.py" is circular: validate.py is the same authority that
generation targets. The real proof: for each template, recover the ORIGINAL corpus
slot values (by parallel-walking template.lir against parse_to_ir(source_bot)), compile
with them, and assert semantic_projection(compiled) == semantic_projection(source_bot).

If it holds, slotify+compile provably reconstructs a known-good bot. It also catches the
"half-slotted" bug class (a value replaced in model.text but NOT in the mirrored positions
action) that validate.py does not detect.

Run:  python3 scripts/roundtrip_templates.py [--corpus DIR]
Exit: 0 iff every template regenerates its source bot.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from salesbot_model import parse_to_ir, ir_to_export, semantic_projection, load_export  # noqa: E402
from compile import compile_template  # noqa: E402

DEFAULT_CORPUS = os.environ.get("SALESBOT_CORPUS")  # tests/run_all.sh builds a synthetic one when unset
TEMPLATES = os.path.join(HERE, "..", "templates")


def collect(tpl, src, sstr, snum):
    """Walk template.lir vs source IR in parallel; record placeholder -> original value."""
    if isinstance(tpl, str) and tpl.startswith("<<") and tpl.endswith(">>"):
        sstr[tpl[2:-2]] = src
    elif isinstance(tpl, bool):
        return
    elif isinstance(tpl, int) and tpl < 0:  # negative numeric sentinel
        snum[tpl] = src
    elif isinstance(tpl, dict) and isinstance(src, dict):
        for k in tpl:
            if k in src:
                collect(tpl[k], src[k], sstr, snum)
    elif isinstance(tpl, list) and isinstance(src, list) and len(tpl) == len(src):
        for a, b in zip(tpl, src):
            collect(a, b, sstr, snum)


def first_diff(a, b, p="$"):
    if type(a) is not type(b):
        return f"{p}: {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        if set(a) != set(b):
            return f"{p}: keys differ {sorted(set(a) ^ set(b))[:4]}"
        for k in a:
            d = first_diff(a[k], b[k], f"{p}.{k}")
            if d:
                return d
    elif isinstance(a, list):
        if len(a) != len(b):
            return f"{p}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{p}[{i}]")
            if d:
                return d
    elif a != b:
        return f"{p}: {repr(a)[:50]} vs {repr(b)[:50]}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    args = ap.parse_args()
    if not args.corpus or not os.path.isdir(args.corpus):
        sys.exit("corpus not found: pass --corpus DIR or set SALESBOT_CORPUS "
                 "(tests/run_all.sh builds a synthetic corpus when none is given)")

    ok = True
    files = sorted(f for f in os.listdir(TEMPLATES) if f.endswith(".json"))
    for tf in files:
        tpl = json.load(open(os.path.join(TEMPLATES, tf)))
        src = load_export(os.path.join(args.corpus, tpl["meta"]["source_bot"]))
        src_ir = parse_to_ir(src)
        sstr, snum = {}, {}
        collect(tpl["lir"], src_ir, sstr, snum)
        sent2name = {s["sentinel"]: s["name"] for s in tpl["slots"] if s.get("sentinel") is not None}
        values = dict(sstr)
        for sent, v in snum.items():
            if sent in sent2name:
                values[sent2name[sent]] = v
        regen = ir_to_export(compile_template(tpl, values))
        d = first_diff(semantic_projection(src), semantic_projection(regen))
        mark = "✓" if not d else "✗"
        if d:
            ok = False
        print(f"  {mark} {tf:<28} -> {tpl['meta']['source_bot']}" + (f"  DIFF {d}" if d else "  projection==source"))

    print("\n" + ("ALL TEMPLATES REGENERATE THEIR SOURCE" if ok else "TEMPLATE FIDELITY FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
