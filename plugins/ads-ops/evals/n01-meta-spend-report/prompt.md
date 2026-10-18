---
name: n01-meta-spend-report
tags: [should-not-trigger, reporting]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Pull last week's spend and CPA by campaign from our Meta Ads account.
