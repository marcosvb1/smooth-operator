---
name: p13-linear-before-automation
tags: [should-trigger, implicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Map our Linear workspace before we automate triage: teams, workflow states with their IDs, and the labels we actually use.
