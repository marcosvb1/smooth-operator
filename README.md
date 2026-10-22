# smooth-operator

Skills, plugins and mods for Claude: reusable tools, workflows and extensions that expand what Claude can do across projects.

This repo works as a Claude Code plugin marketplace.

## Layout

- `.claude-plugin/marketplace.json`: the marketplace catalog. Every plugin, mod or skill bundle must be listed here.
- `plugins/`: plugins and mods, one folder per plugin (see [plugins/README.md](plugins/README.md)).
- `skills/`: standalone skills, one folder per skill (see [skills/README.md](skills/README.md)).

## Contents

| Name | Type | What it does |
| --- | --- | --- |
| `ads-ops` | plugin | Meta Ads and TikTok Ads operations with dry-run and paused creation. |
| [`mise-en-place`](skills/mise-en-place/README.md) | skill | Prepares the workspace so Claude can operate real apps: a verified map of your account (IDs, fields, conventions, payloads, rules). |
| [`quero-que-desenhe`](skills/quero-que-desenhe/SKILL.md) | skill | In Brazilian Portuguese: explains any topic "like I'm 5" with big drawings, few words and everyday Brazilian references, as an HTML page. |

## Install

```bash
/plugin marketplace add marcosvb1/smooth-operator
/plugin install <plugin>@smooth-operator
```

Example: `/plugin install mise-en-place@smooth-operator`.

Per project: `claude plugin install <plugin>@smooth-operator --scope project`.
