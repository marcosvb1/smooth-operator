---
name: n16-export
tags: [should-not-trigger, operation]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Export all contacts from our Mailchimp audience to a CSV.
