---
name: n22-dedupe
tags: [should-not-trigger, operation, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Clean up the duplicate contacts in our HubSpot portal.
