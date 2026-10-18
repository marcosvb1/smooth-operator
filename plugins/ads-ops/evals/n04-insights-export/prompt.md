---
name: n04-insights-export
tags: [should-not-trigger, export]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Export all Meta ad insights for Q3 to a CSV file.
