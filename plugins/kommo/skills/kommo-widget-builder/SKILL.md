---
name: kommo-widget-builder
description: >-
  This skill should be used to build, scaffold, fix, package and ship Kommo
  (ex-amoCRM) widgets and private integrations end-to-end — manifest.json,
  script.js, i18n, the 6 logos, zipping at root, uploading to a private
  integration, installing, dev-mode iteration, the React skeleton / Card SDK
  tab, and the Cloudflare Worker pattern for integration-only endpoints (like
  /api/v4/sources). Use whenever the user wants to create, build, debug, deploy
  or update a Kommo/amoCRM widget or custom integration — even if they only
  describe the behavior ("um widget que cria fontes", "adicionar uma aba nas
  configurações", "um botão no card do lead", "widget pro Kommo", "aba no card
  do lead") without saying "widget". Also for Kommo widget dev mode, the
  long-lived token, building a salesbot_designer widget (the step that makes
  widget_request fire) and a widget/Worker UI to manage sources inside Kommo.
  Loaded with hard-won gotchas that otherwise cost hours. NOT for creating lead
  sources or ingesting leads via the API (kommo-crm) nor for the Salesbot
  JSON and the widget_request → continue runtime (kommo-salesbot-builder).
---

# Kommo Widget Builder

Build Kommo (formerly amoCRM) widgets without rediscovering the platform's
sharp edges. A Kommo widget is a small front-end module that runs **inside the
Kommo SPA** (the admin's browser session), attached to a **private
integration**. This skill encodes the full build→install→iterate→ship loop and
the non-obvious traps that waste hours.

**Before doing anything, read the matching reference file** — the detail lives
there to keep this file scannable. Paths are relative to
`${CLAUDE_PLUGIN_ROOT}/skills/kommo-widget-builder/`; copy templates out of the
plugin into the user's project before editing them:
- `references/widget-anatomy.md` — manifest fields, locations, `script.js`
  callbacks, i18n, the 6 logos, zip rules, render targets.
- `references/gotchas.md` — every trap that cost real time. **Skim this first
  on any Kommo widget task; it will save you a debugging spiral.**
- `references/sources-and-worker.md` — the flagship worked example: a widget +
  Cloudflare Worker that creates lead **Sources** and lets N8N attribute leads
  to them. The canonical pattern for any **integration-only** Kommo endpoint.
- `references/react-skeleton-and-card-sdk.md` — the React skeleton CLI
  (`@kommo-crm/create-kommo-integration`) end-to-end: build/dev-mode traps,
  the crm-react-ui-kit, the **Card SDK tab** recipe (a tab inside the lead
  card), and where to persist widget config (spoiler: not `set_settings`).
- `assets/` — ready-to-copy templates: `manifest.template.json`,
  `script.template.js`, `i18n/` (pt + en with the manifest's keys), `worker/`
  (index.js + wrangler.jsonc), `devserver.js` (local HTTPS dev server + API
  proxy for dev mode), and the 6 logos.

## The mental model (internalize this first)

- A widget ships as a **zip with all files at the ROOT** (`manifest.json`,
  `script.js`, `i18n/`, `images/`) — never nested in a subfolder, or Kommo
  rejects it.
- The zip is uploaded to a **private integration** (Settings → Integrations →
  "+ Create integration" → "Fazer upload"). Uploading a widget is what turns a
  plain integration into a "widget" integration — and that **unlocks
  widget-gated API endpoints** for the integration's token.
- `script.js` is a classic AMD module: `define(['jquery'], function($){ ... })`
  exposing `this.callbacks`. This still works with `interface_version: 2` —
  you do NOT need the React skeleton for most widgets. When the widget IS a
  real UI (card tab, config pages), the skeleton earns its webpack weight —
  then read `references/react-skeleton-and-card-sdk.md` first.
- The widget runs **client-side in the admin's session**. It can `$.ajax` the
  account's own `/api/v4/...` — but **integration-only endpoints reject the
  session** (see the Worker pattern below).

## Build workflow

Follow these steps; consult `references/widget-anatomy.md` for field-level
detail as you go.

1. **Decide where it appears** — pick `locations` (e.g. `settings`,
   `advanced_settings`, `lead_sources`, `lcard-1`, `digital_pipeline`,
   `salesbot_designer`). Only include manifest blocks for locations you
   actually use, or Kommo rejects the manifest — **except the top-level
   `settings` block, which is always required**, even when `settings` is not in
   `locations`. A full-page custom UI → `advanced_settings` (renders into
   `#work-area-<widget_code>`). A settings form → `settings`.
2. **Scaffold the files** by copying `assets/` templates:
   - `manifest.json` — set `widget.name/description/short_description`,
     `version`, `interface_version: 2`, `locale`, `support`, your `locations`.
   - `script.js` — keep the callback skeleton; implement the ones you need
     (`render`, `init`, `bind_actions` must return `true`; plus `settings`,
     `advancedSettings`, `onSave`, `onInstall`, `onAddAsSource`, etc.).
   - `i18n/<lang>.json` — one per declared `locale`; keys referenced by
     `manifest.json` (`widget.name`, `settings.<field>`, `advanced.title`, …).
     Start from `assets/i18n/pt.json` and `en.json`; shape in
     `references/widget-anatomy.md`.
   - `images/` — **all 6 logos are mandatory**: `logo.png`, `logo_dp.png`,
     `logo_main.png`, `logo_medium.png`, `logo_min.png`, `logo_small.png`.
     Copy the neutral placeholders from `assets/images/` if the user has no art
     yet, and ask for real art before publishing.
3. **Zip at root**: `cd widget && zip -r -X ../widget.zip manifest.json script.js i18n images`.
   Verify with `unzip -l` that entries are NOT under a subfolder.
4. **Upload + install**: user uploads the zip to a private integration, fills a
   **redirect URL** (any valid URL — required; see gotchas), grants the needed
   scopes (usually `crm`), saves, and **installs**.
5. **Iterate with dev mode** (no re-upload per change): run a local HTTPS server
   serving the widget folder on a port (e.g. 9000) — `assets/devserver.js` does
   this and also proxies a whitelist of API routes with the integration token
   from env, the user trusts the cert
   once and sets `localStorage.setItem('<widget_code>_is_dev','9000')` in their
   Kommo tab, then just refreshes to see `script.js` changes. The `widget_code`
   is in the integration's **Chaves e escopos** tab. **Bump `version` in the
   manifest whenever you re-upload** — Kommo caches `script.js?v=<version>`.
6. **Need an integration-only endpoint?** (e.g. `/api/v4/sources`) → you can't
   call it from the widget's client-side session. Stand up the **Cloudflare
   Worker proxy** — see `references/sources-and-worker.md`.

## When the widget needs a server-side token (the Worker pattern)

Some Kommo endpoints are **integration-only**: the client-side admin session
gets `400 "Only integrations can access this endpoint"`. The widget can't hold
the integration token safely (client JS is inspectable). The fix is a tiny
**Cloudflare Worker** that holds the long-lived token as a secret and proxies
**only the whitelisted endpoints**, protected by an Origin check
(`*.kommo.com`) + a route whitelist. The widget UI calls the Worker; the Worker
calls Kommo. Full, deployed example in `references/sources-and-worker.md` +
`assets/worker/`.

Do NOT embed a shared secret in the widget JS to auth to the Worker — it leaks
into the inspectable bundle. Rely on Origin + route whitelist + the fact that
the token's scope already bounds the blast radius.

## Quick gotcha checklist (full list in references/gotchas.md)

- Files must be at the **zip root**.
- **All 6 logos** required.
- Manifest blocks only for declared `locations`, **but the top-level
  `settings` block is always required**.
- **Bump `version`** every re-upload (cache-bust for `script.js?v=`).
- The **"Chaves e escopos" tab disappears if the redirect URL is empty** — fill
  any valid URL and save to get it (and the long-lived token button) back.
- **Uninstalling the widget REVOKES the long-lived token.** To update, always
  re-upload/update — never uninstall+install.
- `/api/v4/sources` and similar are **widget-gated / integration-only**.
- Reading static files? Use `self.params.cdn_path`/`cdn_images_path`, not the
  deprecated `path`/`images_path`.
- Using the `ai_agent` location? Every `i18n/<locale>.json` needs a non-empty
  `widget.ai_agent_description` key.
- **You cannot delete a lead via API** (`DELETE /api/v4/leads` → 405). For
  tests use the `unsorted/forms` flow, which is reversible via `.../decline`.
- Kommo returns **204 + empty body** for empty lists — normalize to `{}` before
  a JSON parser sees it.

## Working style

Build the smallest valid widget first and get it installed — that proves the
zip/manifest/upload path and unlocks the integration's token. Then flesh out
the UI under dev mode. When something fails, the **exact error string** tells
you which gotcha you hit — match it against `references/gotchas.md` before
guessing.

## Credenciais

Mesma convenção do plugin (veja a skill `kommo-crm`): perfil no config `kommo.local.json`
(`$KOMMO_CONFIG`, `./.claude/` ou `~/.claude/`), token só em `KOMMO_ACCESS_TOKEN_<PERFIL>` ou
`KOMMO_ACCESS_TOKEN`. Se houver mais de uma conta configurada e o pedido não disser qual, pergunte.

O **token da integração** (long-lived, escopos `crm` e outros) é gerado na aba "Chaves e escopos"
da integração privada. **Nunca** coloque no `script.js` (o JS do widget é público): no Worker ele
vira secret (`wrangler secret put KOMMO_TOKEN`), no `assets/devserver.js` vem de variável de
ambiente. Vale um perfil próprio para a integração-widget (ex.: `cliente-a-widget`), separado do
token de operação.

## Gates

- Upload de nova versão do widget é rotina (com `version` incrementada).
- **Desinstalar o widget exige confirmação explícita do usuário**: revoga o long-lived token e
  quebra o que depende dele (Worker, n8n, OAuth2).
- Criar/apagar fontes, criar leads de teste e qualquer outra escrita no CRM seguem os gates da
  skill `kommo-crm` (`${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/references/safety-gates.md`). Para testar ingestão, prefira
  `unsorted/forms`, que é reversível.

## Relacionados

- Criar fontes de lead pela API, ingestão via `leads/complex` e tokens:
  `${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/references/sources-forms.md`.
- Gates de escrita no CRM: `${CLAUDE_PLUGIN_ROOT}/skills/kommo-crm/references/safety-gates.md`.
- Montar o widget `salesbot_designer`: seção própria em `references/widget-anatomy.md`. O
  contrato de runtime `widget_request` → `continue` (ACK em 2s, `return_url`, modos de falha):
  `${CLAUDE_PLUGIN_ROOT}/skills/kommo-salesbot-builder/references/api-and-runtime.md`.
