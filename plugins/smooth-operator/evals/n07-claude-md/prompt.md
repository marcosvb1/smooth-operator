---
name: n07-claude-md
tags: [should-not-trigger, codebase]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Write a CLAUDE.md for this repo describing the build and test commands.
