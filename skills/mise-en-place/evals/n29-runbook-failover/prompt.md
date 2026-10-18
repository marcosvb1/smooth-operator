---
name: n29-runbook-failover
tags: [should-not-trigger, other, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Write a runbook for our on-call engineers on what to do when the Postgres primary fails over.
