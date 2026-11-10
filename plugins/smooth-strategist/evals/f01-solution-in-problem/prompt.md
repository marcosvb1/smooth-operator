---
name: f01-solution-in-problem
tags: [frame, trap]
plugins: ["../.."]
max_turns: 4
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Help me structure this problem: how do we roll out a chatbot to bring our support response time back down? Median time to resolve a ticket went from 9 to 26 hours over the last two quarters. Ticket volume is flat. From the ticketing export, about 70% of the elapsed time on an average ticket is now spent waiting for the billing team to answer an internal handoff; first reply to the customer still goes out within the hour.
