---
name: p17-wrong-account-pain
tags: [should-trigger, implicit, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

The agent keeps picking the wrong Meta ad account. Make sure that never happens again: write down which account is ours and how we name campaigns.
