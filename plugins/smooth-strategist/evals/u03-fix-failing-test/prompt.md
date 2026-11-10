---
name: u03-fix-failing-test
tags: [should-not-trigger, code, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Fix the failing test in tests/test_meta_job.py.
