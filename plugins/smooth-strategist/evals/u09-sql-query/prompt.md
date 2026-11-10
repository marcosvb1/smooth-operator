---
name: u09-sql-query
tags: [should-not-trigger, code, holdout]
plugins: ["../.."]
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

Write a SQL query that returns monthly signups from the users table, which has a created_at timestamp.
