---
name: n32-reconcile
tags: [should-not-trigger, operation, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Reconcile last month's QuickBooks bank transactions against our Stripe payouts.
