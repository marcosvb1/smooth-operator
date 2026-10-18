---
name: n35-fix-intercom-script
tags: [should-not-trigger, operation, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

The Intercom API returns 404 when scripts/tag_conversation.py tags a conversation. Find the bug and fix it.
