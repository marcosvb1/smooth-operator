---
name: n19-list-custom-fields
tags: [should-not-trigger, oneoff-question, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

List all the custom fields on our HubSpot deals with their types.
