---
name: n13-write-skill
tags: [should-not-trigger, other]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Create a skill that sends a weekly Slack digest of open Jira tickets.
