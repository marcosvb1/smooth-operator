---
name: p02-stripe-before-use
tags: [should-trigger, implicit]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

We're about to start using Claude to manage our Stripe account. Before anything else, map the account so you stop guessing product and price IDs.
