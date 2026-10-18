---
name: p08-airtable-pain
tags: [should-trigger, implicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Finding out which Airtable base and table IDs we use takes several calls every session. Write them down once, in a file you'll read next time before touching Airtable.
