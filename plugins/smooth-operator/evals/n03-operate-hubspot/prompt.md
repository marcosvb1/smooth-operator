---
name: n03-operate-hubspot
tags: [should-not-trigger, operation]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Create a deal in HubSpot for Acme Corp, amount 5000, in the Qualified stage.
