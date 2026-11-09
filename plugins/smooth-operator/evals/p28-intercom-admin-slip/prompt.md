---
name: p28-intercom-admin-slip
tags: [should-trigger, update, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

The Intercom tagging call failed twice today because you used the wrong admin ID. Keep that somewhere the next session will see it, so it doesn't happen a third time.
