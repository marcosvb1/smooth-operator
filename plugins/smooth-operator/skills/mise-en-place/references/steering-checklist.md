# Steering checklist

Checklist for `rules.md`. Go through each item and record only what applies to the tool. One rule per line, in the imperative, with the reason when it isn't obvious.

## Safety

- Which operations spend money (activating a campaign, raising a budget, sending a paid message)?
- Which are irreversible (deleting, sending an email or WhatsApp message, publishing, charging, archiving without restore)?
- What is the safe default on creation (paused, draft, private, test mode)?
- Is there a dry-run, sandbox, test mode or validation flag (`validate_only`, `dry_run`)? How is it used?
- What needs the user's explicit confirmation before running? Write it as a gate: "show X, Y and Z and wait for a yes".

## Limits and mechanics

- Rate limit and how the API signals it (status 429, headers, its own error codes).
- Pagination: type, maximum page size, how to know it's done.
- Batches: how many items per call, whether a batch is atomic or partial.
- Propagation delay: what takes time to show up after creation (ad review, search indexing).
- API version in use and any known sunset date.

## Formats that mislead

- Money: the unit the API expects (minor units, micros, or major units) and the account currency's exponent. Minor units are not always cents: zero-decimal currencies such as JPY, KRW, CLP and VND have no subunit, and some have three decimals (KWD, BHD). A wrong exponent multiplies a budget by 100 or 1000.
- Dates: account time zone versus UTC, format (ISO, epoch seconds or milliseconds).
- IDs: string or number, prefixes (`act_`, `gid://`), different IDs between test and production.
- Enums: accepted values and the difference between the label shown and the API value.
- Fields that can only be written on creation, or that the API silently ignores.

## Account conventions

- Naming pattern (campaign, ad set, list, task) with an anonymized real example.
- Sequential numbering and where to check the next number.
- Default tags, folders, owners or pipelines.
- Who owns what: accounts that must not be touched, objects managed by automations.

## When to stop and ask

- Ambiguous account, pipeline or object (more than one candidate with the same name).
- An operation the map doesn't cover.
- An API response that doesn't match the map (the map may be stale: suggest updating it).
- A request that runs into one of the safety rules above.

## Known errors

For each error seen while mapping: message or code, cause and fix. This section grows with use; tell the user it's worth adding new errors as they show up.
