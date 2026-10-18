# Kommo widget anatomy

## File structure (zip, all at ROOT)

```
manifest.json   (required)
script.js       (the logic; classic AMD)
i18n/           (one JSON per declared locale: en.json, pt.json, …)
images/         (the 6 mandatory logos)
style.css       (optional)
templates/      (optional Twig templates)
```

## manifest.json

```jsonc
{
  "widget": {
    "name": "widget.name",                 // i18n key
    "description": "widget.description",
    "short_description": "widget.short_description",
    "version": "1.0.0",                     // BUMP on every re-upload
    "interface_version": 2,
    "init_once": false,
    "locale": ["pt", "en"],                 // must have a matching i18n/<x>.json each
    "installation": true,
    "support": { "link": "https://...", "email": "you@example.com" }
  },
  "locations": ["settings", "advanced_settings", "lead_sources"],
  "advanced": { "title": "advanced.title" }, // ONLY if advanced_settings is in locations
  "settings": {                              // the install/settings modal fields
    "some_field": { "name": "settings.some_field", "type": "text", "required": false }
  }
}
```

Rules: include a top-level block ONLY for locations you declared (`dp` for
`digital_pipeline`, `advanced` for `advanced_settings`, `sms`, `mobile`, …).
Each i18n key (`widget.name`, `settings.some_field`, `advanced.title`) must
exist in every `i18n/<locale>.json`.

## locations (where the widget mounts)

Full official list (declare in manifest `locations`). `-1`/`-0` suffix applies
to `lcard`, `ccard`, `comcard`, `llist`, `clist`, `tlist`: `1` shows the widget
panel on the card's right side, `0` initializes without it.

- `lcard`/`ccard`/`comcard` — lead/contact/company card.
- `llist`/`clist`/`tlist` — leads/contacts/tasks list (multi-select rows →
  "More" menu → widget action; the panel isn't added until a row is checked).
- `settings` — install/config modal. **Always required as a top-level manifest
  block even when not declared in `locations`** (see gotchas.md).
- `advanced_settings` — full settings page (mounts into
  `#work-area-<widget_code>`); needs the `advanced` manifest block +
  `advancedSettings` callback.
- `card_sdk` — Card SDK tab; also declare `lcard`/`ccard`/`comcard` to have it
  appear on that entity's card.
- `catalogs` — Lists SDK; needs a `loadCatalogElement` callback.
- `digital_pipeline` — Digital Pipeline settings; needs a Python DP endpoint +
  a `logo_dp.png` at 174×109.
- `lead_sources` — addable as a lead source → enables
  `onAddAsSource(pipeline_id)`.
- `widget_page` — left-nav page (Public integrations only).
- `sms` — usable as a system SMS sender.
- `mobile_card` — available in the mobile app.
- `salesbot_designer` — selectable inside the Salesbot constructor (see the
  `salesbot_designer` section below).
- `website_chat_button` — usable as a website chat button.
- `everywhere` — catch-all; the widget decides internally where to render.
  The only location that never takes a `-1`/`-0` suffix.
- `ai_agent` — shows inside the AI agent settings block (added 2025).
  **Requires the `widget.ai_agent_description` i18n key (non-empty, ≤100
  chars recommended) in every declared locale** — see gotchas.md.

## script.js (classic AMD)

```javascript
define(['jquery'], function ($) {
  var CustomWidget = function () {
    var self = this;
    // self.system()  -> system vars (account, user, etc.)
    // self.langs     -> the i18n object for the active locale
    // self.params.widget_code -> this widget's code (for render targets)
    this.callbacks = {
      settings: function () { return true; },        // settings modal opens
      init: function () { return true; },             // MUST return true
      bind_actions: function () { return true; },     // MUST return true
      render: function () { return true; },           // MUST return true
      onSave: function () { return true; },           // settings saved
      onInstall: function () { return true; },        // installed
      advancedSettings: function () {                 // advanced_settings page render
        var code = self.params && self.params.widget_code;
        var area = document.querySelector('#work-area-' + code);
        if (area) { /* area.innerHTML = ...; bind events */ }
        return true;
      },
      onAddAsSource: function (pipeline_id) { return true; }, // needs lead_sources location
      destroy: function () {}
    };
    return this;
  };
  return CustomWidget;
});
```

### self.params (static-file paths)

`self.params` tells the widget where Kommo is serving its own uploaded files
from — used as `base_path` in `self.render()`/`getTemplate()` calls, or to
build an asset URL by hand:

- `cdn_path` — absolute path to the widget's static files, CDN-proxied when
  available (falls back to the old `path` if CDN is disabled). Replaces the
  deprecated `path` (`/widgets/#WIDGET_NAME#`).
- `cdn_images_path` — same, for `images/`. Replaces the deprecated
  `images_path` (`/widgets/#WIDGET_NAME#/images`).

Prefer `self.params.cdn_path`/`cdn_images_path` in new code (Nov 2025+);
`path`/`images_path` still work but are deprecated.

### Calling the Kommo API from the widget (client-side)

The widget runs in the admin's logged-in session, so same-origin `$.ajax` to
`/api/v4/...` is authenticated as the **user**:

```javascript
$.ajax({ url: '/api/v4/leads/pipelines', method: 'GET',
         headers: { 'X-Requested-With': 'XMLHttpRequest' } });
```

This works for most read endpoints. It does NOT work for **integration-only**
endpoints (e.g. `/api/v4/sources` → `400 "Only integrations can access this
endpoint"`) — route those through a Worker (see sources-and-worker.md).

## salesbot_designer (a step inside the Salesbot constructor)

Needed when a bot must call an external service through `widget_request`. Without
this widget, a pasted `widget_request` block imports but never fires (runtime
contract and failure modes in
`${CLAUDE_PLUGIN_ROOT}/skills/kommo-salesbot-builder/references/api-and-runtime.md`).

1. `"locations": ["salesbot_designer", ...]` plus a top-level `salesbot_designer`
   object in the manifest. Each key is a handler code; its `settings` become the
   fields of the modal the bot author fills in:

```json
"salesbot_designer": {
  "logo": "/images/logo_min.png",
  "call_service": {
    "name": "salesbot.call_service",
    "settings": {
      "url":  { "name": "salesbot.url",  "type": "text", "default_value": "https://example.com/hook", "manual": true },
      "data": { "name": "salesbot.data", "type": "text", "default_value": "{{lead.id}}", "manual": true }
    }
  }
}
```

2. `onSalesbotDesignerSave(handler_code, params)` in `script.js` builds the step
   the bot stores. Return a JSON string with the `widget_request` handler (and
   the jump after it):

```js
onSalesbotDesignerSave: function (handler_code, params) {
  return JSON.stringify([{
    question: [
      { handler: 'widget_request',
        params: { url: params.url, data: [params.data] } },
      { handler: 'goto', params: { type: 'question', step: 1 } }
    ]
  }]);
}
```

3. Add the `salesbot.*` keys to every `i18n/<locale>.json`.

The exact shape of the manifest object and of the returned step changes between
Kommo versions; check it against
<https://developers.kommo.com/docs/private-chatbot-integration> before publishing,
and test with one real bot run (an import that succeeds does not prove the POST fires).

## i18n/<locale>.json

```json
{
  "widget": { "name": "My Widget", "short_description": "...", "description": "...", "tour_description": "..." },
  "advanced": { "title": "My Widget — Settings" },
  "settings": { "some_field": "Field label" }
}
```

## images (the 6 logos — all required)

`logo.png`, `logo_dp.png`, `logo_main.png`, `logo_medium.png`, `logo_min.png`,
`logo_small.png`. If the user has no art, copy the neutral gray placeholders in
`assets/images/` (right sizes, no branding) and ask the user for real art
before publishing.

## Local HTTPS dev server (for dev mode)

A minimal Node HTTPS static server with CORS that serves the widget folder lets
you iterate `script.js` live (see `assets/devserver.js` for a ready one):
generate a self-signed cert (`openssl req -x509 -newkey rsa:2048 -keyout
dev-key.pem -out dev-cert.pem -days 365 -nodes -subj "/CN=localhost"`), serve on
:9000 with `Access-Control-Allow-Origin` reflecting the `*.kommo.com` origin.
Then enable dev mode (see gotchas.md → Dev mode).
