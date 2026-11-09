"""Shared plumbing for the offline proofs in this folder (corpus, validation, diffs)."""
import argparse
import os
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(SKILL, "scripts")
TEMPLATES = os.path.join(SKILL, "templates")
sys.path.insert(0, SCRIPTS)

from validate import validate  # noqa: E402


def corpus_dir():
    """--corpus DIR or $SALESBOT_CORPUS; run_all.sh builds a synthetic one when neither is set."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=os.environ.get("SALESBOT_CORPUS"))
    corpus = ap.parse_args().corpus
    if not corpus or not os.path.isdir(corpus):
        sys.exit("corpus not found: pass --corpus DIR or set SALESBOT_CORPUS "
                 "(tests/run_all.sh builds a synthetic corpus when none is given)")
    return corpus


def corpus_files(corpus):
    return sorted(f for f in os.listdir(corpus) if f.endswith(".json"))


def error_codes(wrapper):
    """ERROR-severity finding codes validate.py reports for a bot (empty = importable)."""
    return [f["code"] for f in validate(wrapper).items if f["severity"] == "ERROR"]


def first_diff(a, b, path="$"):
    """Human path to the first structural difference between a and b, or None."""
    if type(a) is not type(b):
        return f"{path}: type {type(a).__name__} vs {type(b).__name__}"
    if isinstance(a, dict):
        if set(a) != set(b):
            return f"{path}: keys differ {sorted(set(a) ^ set(b))[:4]}"
        for k in a:
            d = first_diff(a[k], b[k], f"{path}.{k}")
            if d:
                return d
    elif isinstance(a, list):
        if len(a) != len(b):
            return f"{path}: len {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_diff(x, y, f"{path}[{i}]")
            if d:
                return d
    elif a != b:
        return f"{path}: {repr(a)[:50]} vs {repr(b)[:50]}"
    return None
