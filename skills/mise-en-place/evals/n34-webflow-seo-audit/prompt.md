---
name: n34-webflow-seo-audit
tags: [should-not-trigger, word-trap, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Audit our Webflow site for SEO problems: missing meta descriptions, broken links and oversized images.
