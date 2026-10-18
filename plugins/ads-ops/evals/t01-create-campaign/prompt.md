---
name: t01-create-campaign
tags: [should-trigger, tiktok, explicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Create a TikTok campaign for app installs with two ad groups, both paused.
