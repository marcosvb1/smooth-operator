---
name: n28-check-webhook
tags: [should-not-trigger, operation, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Check whether our Stripe webhook endpoint is still receiving events from the live account.
