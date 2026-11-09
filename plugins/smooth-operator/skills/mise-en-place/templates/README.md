---
tool: <tool>
route: <mcp:<connector> | cli:<cli> | api | docs>
default_account: <slug of the default account, same as its key in data.local.json>
validated_at: YYYY-MM-DD
---

# <Tool>: <what it's used for>

Use when: <situations in which this map should be read, in the user's words (e.g. "move a lead to another stage", "launch an ad on account X")>. Operational skill: <`.claude/skills/<tool>-ops/`, if any>.

> Read before operating. Rules in [rules.md](rules.md) (small tool: replace the link with a `## Rules` section in this file). IDs and config in `data.local.json` (shape in [data.example.json](data.example.json)).
> Source of each fact: `verified:YYYY-MM-DD`, `docs` or `inferred`.

## Purpose

<One or two sentences: what the user does with this tool and which goal guided this map.>

## Access

| Item | Value | Source |
| --- | --- | --- |
| Route | <MCP connector "<name>" / CLI `<cli>` / HTTP API / docs only> | verified:YYYY-MM-DD |
| Base URL and version | `<https://api.example.com/v1>` | |
| Credential | variable `$<TOOL>_TOKEN` (never the value) | |
| How to pick the account | <parameter, profile, variable `$<TOOL>_ACCOUNT_<PROFILE>`> | |

## Accounts

| Name | ID | Use | Currency / time zone | Default |
| --- | --- | --- | --- | --- |
| <account-a> | `<ACCOUNT_ID>` | <what it's for> | <CURRENCY> / <IANA_TIMEZONE> | yes |

<In a public or shared repo, replace the IDs with placeholders; the real ones live in `data.local.json`, outside git.>

## Objects

| Object | What it's for | Details | Source |
| --- | --- | --- | --- |
| <lead> | <opportunity in the pipeline> | [objects/lead.md](objects/lead.md) | verified:YYYY-MM-DD |
| <task> | <out of scope; listed only> | — | docs |

Relations: <campaign → ad set → ad> / <lead → contact → company>.

## Operations

| I want to… | How (tool, command or endpoint) | Payload | Source |
| --- | --- | --- | --- |
| <list the leads in a pipeline> | `<GET /leads?filter[pipeline_id]=<ID>>` | [payloads/list-leads.md](payloads/list-leads.md) | verified:YYYY-MM-DD |
| <create a lead> | `<POST /leads>` | [payloads/create-lead.md](payloads/create-lead.md) | docs |

## Open items

- <What stayed as `docs` and must be verified once there is access.>

## History

- YYYY-MM-DD: map created (<route>, <n> accounts, <n> objects).
