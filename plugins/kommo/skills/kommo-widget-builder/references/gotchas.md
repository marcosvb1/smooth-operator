# Kommo widget gotchas (each one cost real debugging time)

Match the symptom/error string to the cause. Skim this before starting any
Kommo widget task.

## Packaging & upload

- **All files at the ZIP ROOT.** `manifest.json`, `script.js`, `i18n/`,
  `images/` must be top-level entries. Zipping the parent folder (so everything
  is under `widget/...`) makes Kommo reject the archive. Verify: `unzip -l x.zip`.
- **All 6 logos are mandatory** in `images/`: `logo.png`, `logo_dp.png`,
  `logo_main.png`, `logo_medium.png`, `logo_min.png`, `logo_small.png`. Missing
  any → upload/validation fails. Copies live in `assets/images/`.
- **`interface_version: 2` works with a classic `define(['jquery'])` script.js.**
  You don't need the React skeleton (`@kommo-crm/create-kommo-integration`) for
  most widgets. The skeleton is only worth it for heavy React UIs; it also adds
  Docker/webpack and a code-matching dev-mode setup.
- Only include manifest top-level blocks for `locations` you actually declare
  (`dp` for digital_pipeline, `advanced` for advanced_settings, `sms`, `mobile`,
  …). Extra blocks for unused locations → manifest rejected.
- **EXCEPTION: the top-level `settings` block is ALWAYS required**, even when
  `settings` is not in `locations`. Removing it → upload fails with
  `"settings" field is required in manifest.json`. Keep at least one optional
  field (e.g. `{"my_field": {"name": "settings.my_field", "type": "text",
  "required": false}}`) with matching i18n keys in every locale.

## Static-file paths (self.params)

- **`path`/`images_path` are deprecated (Nov 2025) — use `self.params.cdn_path`/
  `cdn_images_path` instead.** Same content, now CDN-proxied (falls back to the
  old path if CDN is disabled). If a widget hardcodes `/widgets/<code>/images/…`
  instead of reading `self.params.cdn_images_path`, it'll keep working (the old
  params aren't removed) but won't benefit from the CDN.

## ai_agent location

- **Declaring `ai_agent` in `locations` requires a `widget.ai_agent_description`
  key in EVERY `i18n/<locale>.json`, and it cannot be empty.** This is on top
  of the usual `widget.name`/`description` keys. Recommended ≤100 characters —
  it renders as a tile in the AI agent settings block and gets ellipsis-
  truncated past that. `ai_agent` can combine with other locations in the same
  manifest.

## Marketplace / public integration listing (NOT the private-integration path)

This skill's build workflow targets a **private integration** upload — the
zip/manifest rules above are everything Kommo validates for that path. If you
ever submit the same widget to the **Kommo Marketplace as a public
integration**, extra moderation rules kick in that do NOT apply to a private
upload:
- Widget name ≤30 chars total; no single word >19 chars; a symbol glued to a
  word with no surrounding space counts as part of that word (Kommo's own
  example: pad symbols with spaces to avoid this).
- Name must end with `via <creator>` or `by <creator>` (e.g. "WhatsApp via
  Zenvia" — a bare "WhatsApp" is rejected).
- Full checklist (branding image sizes, description length, oAuth2
  requirement, no Kommo branding in the name/logo, etc.) is a separate,
  much longer moderation pass — don't apply it to a private-integration task
  unless the user explicitly says "publicar no marketplace"/"submeter pra
  aprovação".

## Caching

- **Bump `widget.version` in manifest on EVERY re-upload.** Kommo serves the
  script as `script.js?v=<version>` and the browser caches by that string. If
  you re-upload new code with the same version, the old cached `script.js`
  keeps running and you'll debug a ghost. Symptom: your new `console.log`/
  behavior doesn't appear; the stack trace shows `script.js?v=<old>`. Fix: bump
  version, re-upload, hard refresh (Ctrl+Shift+R).

## The integration's token & keys

- **"Chaves e escopos" (Keys & scopes) tab disappears when the redirect URL is
  empty.** To get it back (and the "Gerar token de longa duração" button):
  open the integration → **Editar** → fill **URL de redirecionamento** with any
  valid URL (e.g. the account URL) → Salvar → reopen; the tab returns. The
  long-lived token (1 day–5 years) is generated there. The widget code lives in
  this tab too.
- **Uninstalling the widget/integration REVOKES its long-lived token.** Symptom:
  the proxy/N8N suddenly gets `401 "Invalid user name or password"` after it
  worked. During development NEVER uninstall+reinstall to "refresh" — use
  re-upload/update. If revoked: regenerate the token and update wherever it's
  stored (Worker secret, environment variable, N8N credential).
- Generating a long-lived token is the clean path for server-side callers
  (N8N, a Worker). Widgets themselves authenticate via the logged-in session,
  not this token.
- **Long-lived token and OAuth2 COEXIST on one integration** — they are
  independent credential types. Generating a long-lived token does NOT
  overwrite/break an OAuth2 grant, and vice versa. (The "Chaves e escopos" tab
  can disappear transiently, but it comes back — it is NOT mutually exclusive
  with OAuth2.) Key facts:
  - **OAuth2 (refresh token) is MORE robust than a long-lived token** — it
    auto-refreshes and does NOT die on widget reinstall. Prefer it for
    server-side callers (N8N) that must survive.
  - **An OAuth2 access token CAN create Sources** — it's the same widget
    integration, so it passes the `/sources` gate. So when the consumer (e.g.
    N8N) is already on OAuth2, create Sources **directly from it** (`POST
    /api/v4/sources` node with the OAuth2 credential) — no Worker needed.
  - The client-side widget-UI + Worker pattern needs a **long-lived token** in
    the Worker. You can still generate one even while OAuth2 is set up (they
    coexist) — just never click **"Regenerate secret key"** (that invalidates
    the `client_secret` and breaks OAuth2) and never uninstall (revokes both).
  - If an OAuth2 caller suddenly 401s after a widget reinstall, the grant was
    revoked — **Reconnect / re-authorize the OAuth2 credential** to refresh it.

## API behavior

- **`/api/v4/sources` is integration-only / widget-gated.**
  - A plain (non-widget) private-integration token → `400 "Integration needs
    widget to perform this operation"`. Uploading+installing a widget to the
    integration lifts this for the token (server-side).
  - The client-side admin session → `400 "Only integrations can access this
    endpoint"`. So a widget UI cannot call it directly; use the Worker proxy.
- **You cannot delete a lead via API.** `DELETE /api/v4/leads` (and
  `/api/v4/contacts`) → `405`. There is no lead-delete endpoint in v4. For test
  data, create via `POST /api/v4/leads/unsorted/forms` (an "incoming lead") and
  remove it with `DELETE /api/v4/leads/unsorted/{uid}/decline?user_id=<admin>` —
  that deletes the provisional lead+contact. NEVER use `POST /api/v4/leads` for
  throwaway tests: the lead gets stuck (UI-only deletion).
- `DELETE /api/v4/sources` with body `[{"id":...}]` works (204).
- **Note text is HTML-escaped server-side.** Saving a note whose `params.text`
  contains `"`, `&`, `<`, `>` stores them as `&quot;`/`&amp;`/`&lt;`/`&gt;` —
  so raw JSON stashed in a note fails `JSON.parse` on read (symptom: save
  "works", load finds the note, but the app silently falls back to defaults).
  Store machine payloads **base64-encoded** (the alphabet survives the
  sanitizer, UTF-8 via TextEncoder/btoa); on read, tolerate legacy payloads by
  unescaping the entities before parsing.
- **Empty lists return `204` + empty body**, not `200 []`. A `dataType:'json'`
  `$.ajax` (or any strict JSON parser) chokes on the empty body. Normalize: a
  proxy should turn `204`/empty into `200 {}`; a client should treat empty as
  `[]`.
- Lead **source attribution**: create the lead with `POST /api/v4/leads/complex`
  and `_embedded.source = {external_id, type:"widget"}` (`type` only accepts
  `"widget"`). Do not rely on `unsorted/forms` + `source_uid` for this. If the
  `external_id` matches no registered source (e.g. you passed the numeric `id`),
  the lead falls back to the integration's implicit source (label = the
  integration's name). 1 plain integration = 1 source label; a widget
  integration = up to 50 registered sources from one token. Details in
  `${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/references/sources-forms.md` §2.

## Dev mode (iterate without re-uploading)

- Enable per browser: console → `localStorage.setItem('<widget_code>_is_dev','<port>')`
  (e.g. `'9000'`), then refresh. `widget_code` is in the integration's
  **Chaves e escopos** tab.
- Kommo (HTTPS) will load `script.js` from your local server, so the server
  must be **HTTPS**; the browser must **trust the self-signed cert** once (visit
  `https://localhost:<port>/script.js` and proceed past the warning — in Chrome
  you can type `thisisunsafe` on the warning page).
- Cross-origin: the local server needs permissive **CORS** for the Kommo origin
  so the SPA can fetch the script + assets.
- Dev mode swaps the **script/assets** source to localhost; the **manifest**
  (locations, etc.) still comes from the installed widget — so adding a new
  location still requires a re-upload (with a version bump).
- To leave dev mode: `localStorage.removeItem('<widget_code>_is_dev')` + refresh.

## React skeleton & Card SDK (details in react-skeleton-and-card-sdk.md)

- **`self.set_settings()` does NOT persist server-side** — in-memory only
  outside the settings-modal save flow. For account-wide config from an
  advanced-settings page, store JSON in a note on a dedicated config contact.
- **Dev mode needs the widget code BAKED into the installed build**
  (`INTEGRATION_CODE` in `.prod.env` + one re-upload). Symptom: localStorage
  flag set but no localhost request — check `script.js?v=` for the actually
  installed version.
- **CleanWebpackPlugin wipes `dist/` whenever webpack starts** — starting
  `yarn dev` deletes the widget.zip you just built. Copy it out first.
- Once React is bundled, the zip gains a stray `script.js.LICENSE.txt` —
  set `TerserPlugin({ extractComments: false })`.
- **The UI kit renders unstyled unless you import
  `@kommo-crm/crm-react-ui-kit/assets/theme.css` + `assets/icons.css`** —
  components import their own CSS but nothing imports the variables.
- **The skeleton's global `page:changed` handler unmounts all React roots
  and never remounts.** Kommo fires it when the card refreshes (e.g. after
  a lead save) → blank tab. Keep a watchdog that re-renders when the
  container is on screen but empty.
- The Card SDK tab lives in the card's LEFT column (~400px). Two-column
  label/control layouts don't fit — stack them.
- **A missing `import React` in a `.tsx` file can lint clean and pass
  `tsc` yet still crash at runtime as `ReferenceError: React is not
  defined` (blank tab).** Cause: with no `.swcrc` and no swc-loader
  options, SWC's JSX transform defaults to the **classic** runtime
  (`React.createElement`, needs `React` in scope) — independent of
  `tsconfig.json`'s `"jsx": "react-jsx"` (automatic runtime, tsc-only)
  and of `eslint.config.mjs`'s disabled `react/react-in-jsx-scope`. Fix
  properly instead of re-adding the import: give swc-loader
  `options: { jsc: { transform: { react: { runtime: 'automatic',
  development: isDev } } } }` in `webpack.config.ts` so all three tools
  agree — then a missing `React` import can no longer crash anything.
  **webpack.config.ts changes require restarting `yarn dev`** — the
  running webpack-dev-server only re-reads source files, not its own
  config.

## i18n

- **i18n keys must be DOT-FREE.** `self.i18n(key)` treats every `.` in the key
  as a nested-path separator (`langs['a']['b']`). If the first segment is
  missing from the loaded langs, it crashes with
  `Cannot read properties of undefined (reading '')` — taking the whole React
  tree down (blank widget). Even `i18n('Saving...')` crashes. Keys like
  `"Sentence ending in a period."` too. Keep punctuation in the VALUE, never
  in the key, and wrap the i18n callback in try/catch.
- **Dev mode serves script.js only — i18n/langs still come from the UPLOADED
  zip.** New i18n keys show their fallback (the key itself) until the next
  re-upload.

## script.js render targets

- `advancedSettings()` renders a full page; inject into
  `document.querySelector('#work-area-' + self.params.widget_code)`.
- Core callbacks `render`, `init`, `bind_actions` must `return true` or the
  widget won't initialize.
- `onAddAsSource(pipeline_id)` fires when the admin adds the widget as a lead
  source in a pipeline's settings — available only if the manifest declares the
  `lead_sources` location.
