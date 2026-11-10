---
name: t03-churn-by-plan
tags: [should-trigger, analyze, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Here are last quarter's cancellations by plan. Basic: 400 customers, 36 cancelled. Pro: 250 customers, 10 cancelled. Enterprise: 40 customers, 6 cancelled. What should I take from this?
