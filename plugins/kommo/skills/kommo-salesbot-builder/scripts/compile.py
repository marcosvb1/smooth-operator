#!/usr/bin/env python3
"""
compile.py — fase-1 generator: fill a parameterized template into an import-ready bot.

A template (templates/*.json) is a known-good corpus bot's LIR with account-specific
LEAF values replaced by slots — the proven topology (block ids, goto, block_uuid,
action mirroring, text<->positions duality) is preserved verbatim, so the result is
consistent by construction. compile only substitutes slot values, then re-validates.

Template file:
  {
    "meta": {"name","pattern","description","source_bot","channels":[...]},
    "slots": [{"name","kind","required","hint","sentinel"(for numeric)}],
    "lir": { ...LIR with string sentinels "<<name>>" and numeric sentinels (negatives)... }
  }

Slot kinds: text | chat_source | status | pipeline | user | custom_field | enum | delay | int | raw
String slots appear in the LIR as the exact string "<<name>>" (or embedded — substring
replace is applied for text). Numeric slots appear as their declared negative "sentinel"
integer and are replaced by the provided integer value.

Usage:
  python3 scripts/compile.py templates/welcome-redirect.json --values vals.json \
      --inventory /tmp/inv.cliente-a.json --out bot.json
  # vals.json: {"welcome_text":"Olá!","chat_source":11111,"bot_name":"Boas-vindas"}
"""
import argparse
import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from salesbot_model import ir_to_export, save_export  # noqa: E402

VALIDATE = os.path.join(HERE, "validate.py")


def _subst(node, str_subs, num_subs):
    """Recursively substitute string sentinels and numeric sentinels."""
    if isinstance(node, dict):
        return {k: _subst(v, str_subs, num_subs) for k, v in node.items()}
    if isinstance(node, list):
        return [_subst(v, str_subs, num_subs) for v in node]
    if isinstance(node, str):
        out = node
        for token, val in str_subs.items():
            if out == token:
                return val  # whole-value replacement preserves non-string targets if val isn't str
            if token in out:
                out = out.replace(token, str(val))
        return out
    if isinstance(node, bool):
        return node
    if isinstance(node, int):
        if node in num_subs:
            return num_subs[node]
    return node


def compile_template(template, values):
    slots = {s["name"]: s for s in template.get("slots", [])}
    # required check
    missing = [n for n, s in slots.items() if s.get("required") and n not in values]
    if missing:
        raise SystemExit(f"ERROR: missing required slot value(s): {missing}")
    unknown = [k for k in values if k not in slots]
    if unknown:
        print(f"  warn: values for unknown slots ignored: {unknown}", file=sys.stderr)

    str_subs, num_subs = {}, {}
    for name, s in slots.items():
        if name not in values:
            continue
        val = values[name]
        sentinel = s.get("sentinel")
        if sentinel is not None:  # numeric slot
            num_subs[int(sentinel)] = val
        else:
            str_subs[f"<<{name}>>"] = val

    lir = copy.deepcopy(template["lir"])
    lir = _subst(lir, str_subs, num_subs)
    return lir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("--values", required=True, help="json file of slot -> value")
    ap.add_argument("--inventory", help="account inventory for the validation pass")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.template) as fh:
        template = json.load(fh)
    with open(args.values) as fh:
        values = json.load(fh)

    lir = compile_template(template, values)
    wrapper = ir_to_export(lir)
    save_export(wrapper, args.out)

    # mandatory validation gate
    cmd = [sys.executable, VALIDATE, args.out]
    if args.inventory:
        cmd += ["--inventory", args.inventory]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"COMPILE FAILED VALIDATION — {args.out} not safe to import", file=sys.stderr)
        sys.exit(1)
    print(f"OK: wrote validated bot -> {args.out}")


if __name__ == "__main__":
    main()
