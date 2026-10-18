---
name: n11-bigquery-script
tags: [should-not-trigger, integration]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Write a Python script that loads TikTok Ads reports into BigQuery every day.
