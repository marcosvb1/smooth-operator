# <Tool>: rules of use

> Steering for any session that operates <Tool>. Updated YYYY-MM-DD.

## Before acting

- Read [README.md](README.md) and confirm the account with the user when there is more than one.
- <Another precondition.>

## Safety

- <Always create <paused/draft>; activating spends money and needs explicit confirmation.>
- <Show <account, amount, audience, link> and wait for a yes before <irreversible operation>.>
- Never write credentials to a file; use `$<TOOL>_TOKEN`.

## Limits and mechanics

- <Rate limit: <n> req/s; on 429 wait for `Retry-After`.>
- <Pagination by <cursor/offset>, at most <n> per page.>

## Formats

- <Amounts in <minor units/micros/major units> of the account currency (<CURRENCY>, exponent <n>).>
- <Dates in the account's time zone.>

## Account conventions

- <Naming pattern: `<PATTERN>`; example: `<ANONYMIZED EXAMPLE>`.>

## Stop and ask when

- <The account, pipeline or object is ambiguous.>
- <The API response doesn't match the map (suggest updating the map).>

## Known errors

| Error | Cause | Fix |
| --- | --- | --- |
| `<code>` | <cause> | <fix> |
