---
name: p14-n8n-audit-pt
tags: [should-trigger, audit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Revisa as referências do n8n que estão em docs/references/n8n e vê o que mudou na nossa instância desde a última vez.
