---
name: p33-greenhouse-one-file
tags: [should-trigger, implicit, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Put everything an assistant would need to post jobs in our Greenhouse account without asking me into one file: job board IDs, departments, custom fields and the approval rules.
