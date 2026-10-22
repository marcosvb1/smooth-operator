# smooth-operator

Claude skills and plugins for operating real apps: CRMs, ad accounts, billing, project trackers. MIT licensed. Works as a Claude Code plugin marketplace and with `npx skills`.

## mise-en-place

**Your agent writes great docs. Ask it to work inside your CRM and it stalls.**

Every account is full of specifics: a HubSpot portal's own properties, a CRM's pipelines and stage IDs, an ads account's naming rules and money units. Without them, Claude learns your account by trial and error, one failed call at a time, in the middle of the job. Next session, it starts from zero again.

*Mise en place* is the kitchen habit of having everything in its place before cooking. This skill does the prep: before Claude works in a tool, it builds a short, verified map of *your* account (IDs, fields, conventions, payloads that worked, rules) and reads it every time after.

| | Without the map | With the map |
| --- | --- | --- |
| Lead source field | Guesses `hs_analytics_source` | Uses your custom `lead_origin` dropdown |
| Option value | Sends the label `"Instagram"` | Sends the internal value `paid_social` |
| Pipeline stage | Picks "Qualified" by its label | Uses stage `<STAGE_ID>` |
| Emails to contacts | Builds it and runs it | Asks for your yes first, because `rules.md` says so |
| Next session | Starts over | Reads `references/hubspot/README.md` and gets it right the first time |

### Install

Claude Code:

```bash
/plugin marketplace add marcosvb1/smooth-operator
/plugin install mise-en-place@smooth-operator
```

Any agent that reads Agent Skills (Claude Code, Codex, Gemini CLI, Cursor and others):

```bash
npx skills add marcosvb1/smooth-operator --skill mise-en-place
```

Then ask: "do the mise en place for Stripe", "map our Notion workspace before we use it", "update the Jira map".

### What you get

```
references/<tool>/
  README.md           # access route, accounts, default account, objects, operations
  rules.md            # what spends money, what can't be undone, what needs a yes first
  objects/<object>.md # fields, enum options and IDs
  payloads/<op>.md    # request and response that worked, errors seen and the fix
  data.example.json   # shape of the IDs, safe to commit
  data.local.json     # your real IDs, kept out of git
```

- **Quick mode** by default: the accounts, the 2 or 3 objects your goal needs, conventions, rules and known errors. Minutes, not hours. Ask for a "full map" to cover everything in scope.
- **Every fact is tagged** `verified:YYYY-MM-DD`, `docs` or `inferred`, so Claude knows how far to trust it.
- **Read-only mapping.** Writes are recorded only from a dry-run, from something you already asked for, or from a reversible test you approve.
- **No credentials and no personal data** in a map, ever: it stores environment variable names, IDs and structure, never records about people.

Works in Claude Code, Cowork and claude.ai. Full details in the [skill README](skills/mise-en-place/README.md).

### How it's tested

The skill ships with a [trigger eval](skills/mise-en-place/evals/README.md): 68 cases in English and Portuguese, 33 that should fire the skill and 35 near misses that shouldn't (one-off questions, day-to-day operation, the cooking meaning of "mise en place"), with a holdout set kept out of description edits. Graders are deterministic, so you can rerun it with `claude plugin eval`.

## More in this marketplace

| Name | Type | What it does |
| --- | --- | --- |
| [`ads-ops`](plugins/ads-ops/README.md) | plugin | Meta Ads and TikTok Ads operations: create, duplicate, update and audit campaigns with dry-run and paused creation. |
| [`kommo`](plugins/kommo/README.md) | plugin | Kommo CRM operations with approval gates, funnel reports, pipeline redesign, validated Salesbots and widgets. |
| [`quero-que-desenhe`](skills/quero-que-desenhe/SKILL.md) | skill | In Brazilian Portuguese: explains any topic "like I'm 5" as a comic-style HTML page with big drawings, few words and everyday Brazilian references. |

```bash
/plugin install ads-ops@smooth-operator
/plugin install kommo@smooth-operator
/plugin install quero-que-desenhe@smooth-operator
```

Per project: `claude plugin install <plugin>@smooth-operator --scope project`.

## Repo layout

- `.claude-plugin/marketplace.json`: the marketplace catalog. Every plugin, mod or skill bundle is listed here.
- `plugins/`: plugins and mods, one folder per plugin (see [plugins/README.md](plugins/README.md)).
- `skills/`: standalone skills, one folder per skill (see [skills/README.md](skills/README.md)).

## License

[MIT](LICENSE)
