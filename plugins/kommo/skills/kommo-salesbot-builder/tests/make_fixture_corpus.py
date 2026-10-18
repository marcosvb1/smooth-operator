#!/usr/bin/env python3
"""
make_fixture_corpus.py — build a synthetic, account-free corpus for the offline proofs.

The original proofs ran against a private corpus of real exported bots. That corpus
is not shipped (real bots carry account ids and copy). This script rebuilds a
neutral stand-in so the proofs run anywhere:

  - each template in templates/ compiled with dummy values, saved under the
    template's meta.source_bot name (so roundtrip_templates.py finds it);
  - viz/sample-bot.export.json (a hand-written demo bot with fake ids).

Run against a real corpus instead by setting SALESBOT_CORPUS or passing --corpus to
the proof scripts; real bots give a stronger proof than this fixture.

Usage: python3 tests/make_fixture_corpus.py <out_dir>
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from compile import compile_template  # noqa: E402
from salesbot_model import ir_to_export, save_export  # noqa: E402

TEMPLATES = os.path.join(SKILL, "templates")
SAMPLE = os.path.join(SKILL, "viz", "sample-bot.export.json")

# dummy numeric ids per slot kind (positive, obviously fake)
KIND_BASE = {
    "chat_source": 9100, "status": 9200, "pipeline": 9300, "user": 9400,
    "custom_field": 9500, "enum": 9600, "int": 9700,
}
DELAYS = [3600, 86400, 172800, 604800, 2592000]


def dummy_values(template):
    vals, n, d = {}, 0, 0
    for s in template.get("slots", []):
        name, kind = s["name"], s.get("kind")
        if s.get("sentinel") is not None:
            if kind == "delay":
                vals[name] = DELAYS[d % len(DELAYS)]
                d += 1
            else:
                n += 1
                vals[name] = KIND_BASE.get(kind, 9900) + n
        elif kind == "raw":
            # placeholders of a lead custom field: {{lead.cf.ID}} / {{lead.cf.ID.ENUM}}
            vals[name] = "{{lead.cf.9501.9601}}" if name.endswith("_value") else "{{lead.cf.9501}}"
        else:
            vals[name] = f"<{name}>"
    return vals


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: make_fixture_corpus.py <out_dir>")
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for fn in sorted(os.listdir(TEMPLATES)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(TEMPLATES, fn)) as fh:
            tpl = json.load(fh)
        wrapper = ir_to_export(compile_template(tpl, dummy_values(tpl)))
        save_export(wrapper, os.path.join(out, tpl["meta"]["source_bot"]))
    shutil.copy(SAMPLE, os.path.join(out, "sample-bot.export.json"))
    print(f"fixture corpus -> {out}")


if __name__ == "__main__":
    main()
