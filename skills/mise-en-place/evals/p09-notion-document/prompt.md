---
name: p09-notion-document
tags: [should-trigger, explicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Document what works in our Notion workspace: which databases matter, their property names and types, and the payloads that worked when creating pages.
