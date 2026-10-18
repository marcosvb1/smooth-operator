---
name: p26-activecampaign-colinha-pt
tags: [should-trigger, implicit, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Monta uma colinha com os IDs das listas, tags e campos do nosso ActiveCampaign pra você consultar antes de disparar qualquer coisa.
