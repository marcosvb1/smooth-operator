---
name: n17-integration-code-docs
tags: [should-not-trigger, codebase, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Document our HubSpot integration code: what each module in src/hubspot does and how they fit together.
