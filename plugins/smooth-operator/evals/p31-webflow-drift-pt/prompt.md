---
name: p31-webflow-drift-pt
tags: [should-trigger, audit, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Faz tempo que ninguém mexe nas anotações do Webflow. Confere se as collections e os IDs dos campos ainda batem com o site de hoje.
