---
name: n26-fix-n8n-workflow
tags: [should-not-trigger, operation, hard]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Fix the n8n workflow that syncs Typeform to HubSpot; it fails on the email field.
