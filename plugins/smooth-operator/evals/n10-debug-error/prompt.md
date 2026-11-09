---
name: n10-debug-error
tags: [should-not-trigger, operation]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

I'm getting INVALID_ARGUMENT from the Google Ads API when I upload offline conversions. What's usually wrong?
