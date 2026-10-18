---
name: n05-mcp-server
tags: [should-not-trigger, mcp-server]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Write an MCP server that exposes our Stripe refunds to Claude.
