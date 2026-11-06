---
name: p21-mailchimp-stale
tags: [should-trigger, audit, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Our Mailchimp reference files are from last year. Check them against the live account and fix whatever is wrong.
