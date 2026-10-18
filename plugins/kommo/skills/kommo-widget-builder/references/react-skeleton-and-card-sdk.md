# React skeleton (create-kommo-integration) & Card SDK tab

Worked knowledge from building a production custom-fields widget (card tab +
advanced settings page, 2026-07).
Use the skeleton when the widget is a real UI (field panels, config pages).
For anything smaller, the classic AMD path in `widget-anatomy.md` is less
machinery.

## Scaffolding

```bash
npx @kommo-crm/create-kommo-integration@latest <dir> --pt   # or --en/--es
```

Interactive prompts: support link + email, `init_once` (say No for card
widgets that re-render per card), widget locales (Space marks, Enter
confirms), locations (checkbox list — the CLI labels `advanced_settings`
with a typo, `[advanced_settins]`), and "add test functionality?" (say No
for a clean scaffold). Output: a monorepo — `client/` (webpack + swc + TS +
React) and `server/` (optional dev backend, usually ignorable).

## Build

- `corepack yarn build` inside `client/` (yarn is often not on PATH; corepack
  is). Runs eslint + tsc as a gate, then webpack → `dist/` + `dist/widget.zip`
  with root-level entries (ZipPlugin). The manifest/i18n/images live in
  `client/public/`.
- **CleanWebpackPlugin wipes `dist/` on EVERY webpack start — including the
  dev server.** Your freshly built widget.zip vanishes when you start
  `yarn dev`. Copy the zip out of `dist/` right after building.
- Production minification extracts license comments into
  `script.js.LICENSE.txt` inside the zip once React is bundled. Add
  `optimization.minimizer = [new TerserPlugin({ extractComments: false })]`
  to keep the zip clean.

## Dev mode (skeleton flavor)

- Envs: `client/deploy/dev/.dev.env` and `client/deploy/prod/.prod.env` —
  set `INTEGRATION_CODE` (widget code from "Chaves e escopos") and
  `LOCALHOST_PORT` (default 9000).
- **The localStorage dev-mode check runs inside the INSTALLED script**, and
  the widget code is baked in at build time. So dev mode only works after
  one re-upload of a build with the real `INTEGRATION_CODE` in `.prod.env`.
  Symptom of skipping this: localStorage flag set but only the CDN request
  (`script.js?v=...`) appears — no localhost request. Check the `?v=` to see
  which version is actually installed.
- The dev server is plain HTTP on localhost with permissive CORS; Chrome
  treats `http://localhost` as trustworthy from HTTPS pages — **no
  self-signed-cert dance needed** (unlike the classic recipe).
- Dev mode swaps `script.js` ONLY. Manifest, locations and **i18n/langs
  still come from the uploaded zip** — new i18n keys show their fallback
  until the next re-upload.
- Check the port before starting: stale dev servers from other widget
  projects love to squat on 9000 (`lsof -nP -iTCP:9000 -sTCP:LISTEN`).

## UI kit (@kommo-crm/crm-react-ui-kit)

- storybook.kommo.com is the live catalog. Import per component
  (`.../Button`, `.../Input`, …); every component takes a mandatory `theme`
  prop (`ButtonPrimaryTheme`, `InputLightTheme`, `TextareaLightTheme`, …).
- **Components import their own CSS, but nothing imports
  `assets/theme.css` + `assets/icons.css`** — the CSS variables and icons
  everything depends on. Import both once (e.g. in integration.ts) or the
  kit renders colorless/broken.
- Controlled Checkbox/Switcher use `isChecked` (not `checked`).
- Select is compound:
  `Select(theme, value, onChange) > Select.Button(SelectButtonLightTheme) >
  Select.Value + Select.Arrow(SelectArrowTheme)`, then
  `Select.List(SelectListTheme) > Select.Item({value, option}, index,
  SelectItemTheme) > Select.Option`.
- The kit's utility hooks (`@kommo-crm/react-hooks`) are generic UI hooks
  (useDebounce, keyboard navigation) — NOT CRM-data hooks.

## Card SDK tab (a tab inside the lead card)

The tab renders in the card's LEFT column — **~400px wide**. Design for
narrow: stacked labels, full-width controls.

1. Locations: `lcard-0` + `card_sdk` (plus the always-mandatory `settings`
   block in the manifest — see gotchas).
2. Implement the 4 mandatory callbacks: `loadPreloadedData` (fires when the
   tab initializes — render here), `loadElements`, `linkCard`,
   `searchDataInCard`. When not using the standard products mechanism, the
   last three are empty `Promise.resolve([])` stubs.
3. The tab body container is `#<widget_code>`
   (`self.get_settings().widget_code`). Mount React into it.
4. **The skeleton's global `page:changed` handler unmounts every React root
   and nothing remounts.** Kommo refreshes the card after a lead save, so
   the tab goes blank. Keep a watchdog interval: if the container is in the
   DOM but empty, re-render (which also refreshes data post-save).

## Storing widget config (advanced settings page)

- **`self.set_settings()` does NOT persist server-side** — it only mutates
  the in-memory widget object outside the settings-modal save flow. Verified
  live: config gone after reload.
- Account-wide config that works with session auth + documented v4 endpoints:
  store the JSON as a **note on a dedicated, clearly-named config contact**
  (e.g. `[Widget] Config (nao apagar)`), text prefixed
  (`af_layout:v1:<json>`), newest matching note wins, ids cached in module
  scope. Degrade reads to null so the widget still renders on failure.

## Session API from the widget

- `PATCH /api/v4/leads/{id}` works via the logged-in session; the change is
  attributed to the logged-in user (never "the bot").
- BUT saves can trigger the account's Salesbot/Digital-Pipeline automations:
  expect bot edits right after yours and noise like
  `Error: The response_chat_source is not available for chatting` when a bot
  fires on a lead without an open chat. Pause-bots flags / test leads keep
  experiments clean.

## i18n in React pages

Use the template's `i18n('...')` util with **dot-free keys** (punctuation in
the value, never the key) and a try/catch wrapper — see gotchas for why a
key like `'Saving...'` blanks the whole widget.
