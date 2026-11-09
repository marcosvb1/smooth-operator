#!/usr/bin/env python3
"""
roundtrip.py — prove the format model is faithful against the known-good corpus.

For each bot:
  1. semantic_projection(original) == semantic_projection(ir_to_export(parse_to_ir(original)))
     -> the cosmetic set is exactly {x,y,z,width,height}; (de)serialization is lossless.
  2. ir_to_export(parse_to_ir(original)) passes validate.py
     -> regeneration (with fresh auto-layout) yields a structurally-valid, importable bot.

Run:  python3 tests/roundtrip.py [--corpus DIR]
Exit: 0 iff all bots round-trip and re-validate.
"""
import os
import sys

from proof import corpus_dir, corpus_files, error_codes, first_diff
from salesbot_model import ir_to_export, load_export, parse_to_ir, semantic_projection


def main():
    corpus = corpus_dir()
    files = corpus_files(corpus)
    rt_fail, val_fail = [], []
    for name in files:
        w = load_export(os.path.join(corpus, name))
        regen = ir_to_export(parse_to_ir(w))
        d = first_diff(semantic_projection(w), semantic_projection(regen))
        codes = error_codes(regen)
        if d:
            rt_fail.append(name)
        if codes:
            val_fail.append(name)
        extra = (f"  RT-DIFF {d}" if d else "") + (f"  VAL {codes}" if codes else "")
        print(f"  {'✗' if d or codes else '✓'} {name}{extra}")

    print()
    print(f"round-trip identity: {len(files)-len(rt_fail)}/{len(files)} | re-validate: {len(files)-len(val_fail)}/{len(files)}")
    ok = not rt_fail and not val_fail
    print("ALL ROUND-TRIP PROOFS PASS" if ok else "ROUND-TRIP PROOF FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
