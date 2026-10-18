---
name: p10-shopify-memory
tags: [should-trigger, implicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Create an operational memory for our Shopify store so future sessions know which store to use, the metafields we rely on, and which actions need my confirmation.
