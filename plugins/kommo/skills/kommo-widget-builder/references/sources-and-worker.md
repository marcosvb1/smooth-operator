# Flagship recipe: lead-sources widget + Cloudflare Worker + N8N ingestion

This is the canonical pattern for **any integration-only Kommo endpoint**. Goal: let an operator create multiple
registered lead **Sources** from a UI inside Kommo, and have **N8N** push leads
attributed to a specific source.

## Why a Worker is needed

- Creating a registered Source = `POST /api/v4/sources`, which is **integration-
  only**. The widget's client-side session can't call it (`400 "Only
  integrations can access this endpoint"`).
- The integration's long-lived token *can* (once a widget is installed on it),
  but that token must NOT live in client-side widget JS (inspectable).
- So: a tiny **Cloudflare Worker** holds the token (secret) and proxies only the
  sources + pipelines endpoints. The widget UI calls the Worker.

## Architecture

```
Widget UI (advanced_settings page, client-side $.ajax)
   │  GET/POST/DELETE  https://<worker>.workers.dev/k/<sources|leads/pipelines>
   ▼
Cloudflare Worker (token as secret; Origin *.kommo.com + route whitelist)
   │  Authorization: Bearer <long-lived token of the widget integration>
   ▼
Kommo  /api/v4/sources   (create/list/delete registered sources)

N8N (server-side, holds the token directly — NOT via the Worker)
   POST /api/v4/leads/complex  with
   _embedded.source = { external_id, type: "widget" }   → lead's Fonte = that source
```

The N8N side does **not** use the Worker: N8N is server-side and can hold the
token directly, so it calls Kommo straight. The Worker exists only because the
widget UI is client-side.

## The Worker (see assets/worker/)

`assets/worker/src/index.js` is the deployed proxy. Key properties:
- Routes whitelisted in `worker/src/allow.json` (shared with `assets/devserver.js`,
  so dev mode proxies exactly the same routes): `GET/POST/DELETE sources`,
  `GET leads/pipelines`. Anything
  else → 403. So even if the URL leaks, no access to leads/contacts/etc.
- Auth: `Origin` must be `https://<sub>.kommo.com` (exact-match regex; browsers
  can't forge Origin cross-site). **No shared secret in the widget JS** — it would leak into the
  bundle; the route whitelist + token scope already bound the blast radius.
- Normalizes Kommo's `204`/empty to `200 {}` (so the widget's JSON parse is
  happy).
- Token + domain via env: `KOMMO_TOKEN` (secret), `KOMMO_DOMAIN` (var).
- Origin check only stops browsers on other sites; `curl` can send any Origin.
  That is why the whitelist must stay minimal (sources + pipelines).

Deploy:
```bash
cp -r "${CLAUDE_PLUGIN_ROOT}/skills/kommo-widget-builder/assets/worker" ./kommo-sources-worker
cd kommo-sources-worker
printf '%s' '<LONG_LIVED_TOKEN>' | npx wrangler secret put KOMMO_TOKEN
npx wrangler deploy   # → https://<name>.<subdomain>.workers.dev
```
Set `KOMMO_DOMAIN` and `account_id` in `wrangler.jsonc`. Point the widget's
`API_BASE` at `https://<worker-url>/k`.

## The widget UI

`advancedSettings()` renders a "Sources manager" into `#work-area-<widget_code>`:
a name input + pipeline `<select>` (from `GET /k/leads/pipelines`) + Add button
(`POST /k/sources` with `{name, external_id: slug(name), pipeline_id}`) + a table
of existing sources (`GET /k/sources`) with delete (`DELETE /k/sources` body
`[{id}]`). `external_id` is the stable slug N8N will reference. See
`assets/script.template.js` for the shape (its `API_BASE` + `api()` helper).

## N8N lead ingestion (leads/complex)

```http
POST https://<sub>.kommo.com/api/v4/leads/complex
Authorization: Bearer <long-lived token>
Content-Type: application/json
```
```json
[{
  "name": "Lead from Landing X",
  "pipeline_id": <PIPELINE_ID>,
  "_embedded": {
    "source": { "external_id": "lp-landing-x", "type": "widget" },
    "contacts": [{
      "name": "{{name}}",
      "custom_fields_values": [
        { "field_code": "PHONE", "values": [{ "value": "{{phone}}", "enum_code": "WORK" }] },
        { "field_code": "EMAIL", "values": [{ "value": "{{email}}", "enum_code": "WORK" }] }
      ]
    }]
  }
}]
```
- `_embedded.source.external_id` must equal a registered source's `external_id`;
  `type` only accepts `"widget"`. The created lead's **Fonte** = that source.
  `/api/v4/leads/complex` (lead + contact + source in one call) honors this —
  confirmed working.
- ⚠️ **`external_id` is the source's SLUG** (e.g. `"site-organico"`), **NOT its
  numeric `id`** (e.g. `12345`). Each source has both `id` and `external_id`.
  Passing the `id` here fails **silently**: the lead falls back to the
  integration's implicit source (label = the integration's name).
  Get the right value from `GET /api/v4/sources`.
- In N8N: HTTP Request node, Auth = **Header Auth** credential
  (`Authorization: Bearer <token>`) — never put the token in body/URL.
- Reminder: `leads/complex` creates a real lead (no API delete — 405). For a dry
  test, prefer `unsorted/forms` which is reversible.
