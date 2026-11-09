#!/usr/bin/env python3
"""Rebuild the case table of an eval suite's CASES.md from its case folders.

Each case folder holds prompt.md (frontmatter with tags; the prompt is the body) and
graders/*.md. The table lists the skills a case expects to fire (graders with min >= 1),
its tags (minus should-trigger/should-not-trigger, which the fires column already says)
and the prompt. Everything above the table is kept.

Usage: python3 scripts/eval_cases.py [--check] <evals_dir> [...]
--check exits 1 when a CASES.md is out of date instead of rewriting it.
"""
import re
import sys
from pathlib import Path

HEADER = "| id | fires | tags | prompt |\n| --- | --- | --- | --- |\n"


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    return match.group(1), match.group(2).strip()


def row(case):
    meta, prompt = frontmatter((case / "prompt.md").read_text(encoding="utf-8"))
    tags = [t.strip() for t in re.search(r"^tags:\s*\[(.*)\]", meta, re.M).group(1).split(",")]
    tags = ", ".join(t for t in tags if not t.startswith("should-"))
    fires = []
    for grader in sorted((case / "graders").glob("*.md")):
        g, _ = frontmatter(grader.read_text(encoding="utf-8"))
        minimum = re.search(r"^min:\s*(\d+)", g, re.M)
        skill = re.search(r'"\(\?:\[\\w-\]\+:\)\?([\w-]+)"', g)
        if minimum and int(minimum.group(1)) >= 1 and skill:
            fires.append(skill.group(1))
    prompt = " ".join(prompt.split()).replace("|", "\\|")
    return f"| `{case.name}` | {', '.join(fires) or 'none'} | {tags} | {prompt} |\n"


def build(evals):
    cases = sorted(p for p in evals.iterdir() if (p / "prompt.md").is_file())
    intro = (evals / "CASES.md").read_text(encoding="utf-8").split("| id |")[0]
    return intro + HEADER + "".join(row(c) for c in cases)


def main(argv):
    check = "--check" in argv
    stale = []
    for arg in (a for a in argv if not a.startswith("--")):
        target = Path(arg) / "CASES.md"
        text = build(Path(arg))
        if target.read_text(encoding="utf-8") != text:
            stale.append(str(target))
            if not check:
                target.write_text(text, encoding="utf-8")
    if check and stale:
        print("Out of date (run scripts/eval_cases.py on its folder): " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
