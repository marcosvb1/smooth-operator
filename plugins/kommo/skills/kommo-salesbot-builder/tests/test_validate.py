#!/usr/bin/env python3
"""
test_validate.py — durable two-sided proof of the validator.

  POSITIVE: validate.py must PASS every known-good corpus bot (0 errors).
  NEGATIVE: validate.py must CATCH each malformed-bot mutation class.

Run:  python3 tests/test_validate.py [--corpus /path/to/examples]
Exit: 0 if all assertions hold, 1 otherwise.

This is the "sem erros" regression test: if a future format-model change breaks
either direction, this fails loudly.
"""
import copy
import json
import os
import sys

from proof import corpus_dir, corpus_files, error_codes
from salesbot_model import iter_handlers, text_steps


def positive(corpus):
    files = corpus_files(corpus)
    fails = []
    for name in files:
        with open(os.path.join(corpus, name)) as fh:
            codes = error_codes(json.load(fh))
        if codes:
            fails.append((name, codes))
    return len(files), fails


def mutations(base):
    """Return list of (name, mutated_wrapper or None if base lacks the feature, expected_error_code)."""
    out = []

    m = copy.deepcopy(base); del m["model"]["text"]
    out.append(("remove model.text", m, "MODEL"))

    m = copy.deepcopy(base); m["model"]["text"] = m["model"]["text"][:-2] + "XX"
    out.append(("corrupt text json", m, "TEXT_PARSE"))

    m = copy.deepcopy(base); t = json.loads(m["model"]["text"])
    first = next(iter(text_steps(t)))
    t[first].setdefault("question", []).append({"handler": "goto", "params": {"step": 99999, "type": "question"}})
    m["model"]["text"] = json.dumps(t)
    out.append(("dangling text goto", m, "GOTO_DANGLE"))

    m = copy.deepcopy(base); t = json.loads(m["model"]["text"])
    # mutate a block_uuid that also exists in positions
    pos = json.loads(m["model"]["positions"])
    pos_steps_with_uuid = {str(b.get("step")): b.get("block_uuid") for b in pos if b.get("block_uuid")}
    target = next((k for k in text_steps(t) if str(k) in pos_steps_with_uuid), None)
    if target:
        t[target]["block_uuid"] = "00000000-0000-0000-0000-000000000000"
        m["model"]["text"] = json.dumps(t)
    out.append(("block_uuid mismatch", m if target else None, "SYNC_UUID"))

    m = copy.deepcopy(base); pos = json.loads(m["model"]["positions"])
    for b in pos:
        if isinstance(b.get("goto"), dict) and "block" in b["goto"]:
            b["goto"]["block"] = 88888
            break
    m["model"]["positions"] = json.dumps(pos)
    out.append(("positions goto.block dangling", m, "POS_GOTO_DANGLE"))

    m = copy.deepcopy(base); t = json.loads(m["model"]["text"])
    first = next(iter(text_steps(t)))
    blk = t[first].setdefault("question", [{}])
    blk[0].setdefault("params", {})["text"] = "Z" * 70000
    m["model"]["text"] = json.dumps(t)
    out.append(("oversize >64KB", m, "SIZE"))

    m = copy.deepcopy(base); pos = json.loads(m["model"]["positions"])
    t = json.loads(m["model"]["text"])
    drop = next(iter(text_steps(t)), None)
    pos = [b for b in pos if str(b.get("step")) != str(drop)]
    m["model"]["positions"] = json.dumps(pos)
    out.append((f"drop positions block step {drop}", m, "SYNC_TEXT_POS"))

    # bare waits-condition target (not handler:goto) pointing nowhere
    m = copy.deepcopy(base); t = json.loads(m["model"]["text"]); done = False
    for h in iter_handlers(t):
        conds = h.get("params", {}).get("conditions", []) if h["handler"] == "waits" else []
        if conds and isinstance(conds[0].get("action"), dict):
            conds[0]["action"]["step"] = 99999
            done = True
            break
    if done:
        m["model"]["text"] = json.dumps(t)
    out.append(("dangling waits target", m if done else None, "GOTO_DANGLE"))

    # dangling action links.block (branch edge in positions)
    m = copy.deepcopy(base); pos = json.loads(m["model"]["positions"]); done = False
    for blk in pos:
        if not isinstance(blk, dict):
            continue
        for a in blk.get("actions", []) or []:
            if isinstance(a, dict):
                for lk in a.get("links", []) or []:
                    if isinstance(lk, dict) and "block" in lk:
                        lk["block"] = 88888
                        done = True
                        break
            if done:
                break
        if done:
            break
    if done:
        m["model"]["positions"] = json.dumps(pos)
    out.append(("dangling action links.block", m if done else None, "POS_LINK_DANGLE"))

    # remove the single start block
    m = copy.deepcopy(base); pos = json.loads(m["model"]["positions"])
    pos = [b for b in pos if not (isinstance(b, dict) and b.get("type") == "start")]
    m["model"]["positions"] = json.dumps(pos)
    out.append(("remove start block", m, "ONE_START"))

    # change_status with pipeline_id removed (structural — status alone is ambiguous)
    m = copy.deepcopy(base); t = json.loads(m["model"]["text"]); done = False
    for h in iter_handlers(t):
        p = h.get("params", {})
        if h["handler"] == "action" and p.get("name") == "change_status" and isinstance(p.get("params"), dict):
            p["params"].pop("pipeline_id", None)
            done = True
    if done:
        m["model"]["text"] = json.dumps(t)
    out.append(("change_status missing pipeline_id", m if done else None, "PIPELINE_REQUIRED"))

    # chat_sources id as string instead of int (structural type check)
    m = copy.deepcopy(base); t = json.loads(m["model"]["text"]); done = False
    for h in iter_handlers(t):
        srcs = h.get("params", {}).get("chat_sources") if h["handler"] == "send_message" else None
        if srcs and isinstance(srcs[0], dict) and "id" in srcs[0]:
            srcs[0]["id"] = str(srcs[0]["id"])
            done = True
    if done:
        m["model"]["text"] = json.dumps(t)
    out.append(("chat_sources id as string", m if done else None, "CHATSRC_TYPE"))

    return out


def main():
    corpus = corpus_dir()

    print("== POSITIVE: corpus must pass ==")
    n, fails = positive(corpus)
    if fails:
        for name, codes in fails:
            print(f"  ✗ {name}: {codes}")
        print(f"FAIL: {len(fails)}/{n} corpus bots produced errors")
    else:
        print(f"  ✓ all {n} corpus bots pass with 0 errors")

    print("\n== NEGATIVE: mutations must be caught ==")
    # pick a representative branching bot as mutation base
    base_path = os.path.join(corpus, "cadence-followup.source.json")
    if not os.path.isfile(base_path):
        base_path = os.path.join(corpus, corpus_files(corpus)[0])
    with open(base_path) as fh:
        base = json.load(fh)
    neg_fail = []
    for name, w, expect in mutations(base):
        if w is None:
            print(f"  ✗ {name:<32} the base bot has nothing to mutate; pick a base that has it")
            neg_fail.append(name)
            continue
        codes = error_codes(w)
        caught = expect in codes
        print(f"  {'✓' if caught else '✗'} {name:<32} expect [{expect}] -> {codes if codes else 'NOT CAUGHT'}")
        if not caught:
            neg_fail.append(name)

    ok = not fails and not neg_fail
    print(f"\n{'ALL TESTS PASS' if ok else 'TESTS FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
