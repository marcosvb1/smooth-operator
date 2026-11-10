---
name: u08-summarize-text
tags: [should-not-trigger, writing, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Summarize this in three bullets: "The city council voted on Tuesday to extend the bike lane network by 12 km over the next two years. Funding comes from the regional transport budget. Construction starts in the spring and will close two lanes of the river road for about four months."
