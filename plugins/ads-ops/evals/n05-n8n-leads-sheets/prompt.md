---
name: n05-n8n-leads-sheets
tags: [should-not-trigger, integration]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Set up an n8n workflow that writes new Meta lead form submissions into Google Sheets.
