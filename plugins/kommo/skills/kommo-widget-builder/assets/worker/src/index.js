// Kommo lead-sources proxy.
// The Kommo /api/v4/sources endpoint is integration-only (the admin session can't
// call it from the widget). This Worker holds the integration long-lived token
// server-side and proxies ONLY the sources + pipelines endpoints, so the widget UI
// (running on https://<sub>.kommo.com) can manage lead sources.
//
// Security:
//   - CORS + Origin must be exactly https://<sub>.kommo.com (regex, not substring).
//   - No shared secret: anything in the widget JS is public. Optional
//     ALLOWED_ORIGIN var pins the one account that may use this Worker.
//   - Path whitelist: only `sources` (GET/POST/DELETE) and `leads/pipelines` (GET).
//     Even if the URL leaks, no access to leads/contacts/etc.

// Route whitelist shared with ../../devserver.js (edit allow.json, not here).
import ALLOW_RAW from './allow.json';
const ALLOW = ALLOW_RAW.map((a) => ({ method: a.method, re: new RegExp(a.path) }));

const KOMMO_ORIGIN = /^https:\/\/[a-z0-9-]+\.kommo\.com$/;

function originAllowed(origin, env) {
  if (!KOMMO_ORIGIN.test(origin)) return false;
  return !env.ALLOWED_ORIGIN || origin === env.ALLOWED_ORIGIN;
}

function corsHeaders(origin, env) {
  const allow = originAllowed(origin, env) ? origin : `https://${env.KOMMO_DOMAIN}`;
  return {
    'Access-Control-Allow-Origin': allow,
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, X-Requested-With',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const cors = corsHeaders(origin, env);
    const json = (obj, status = 200) =>
      new Response(typeof obj === 'string' ? obj : JSON.stringify(obj), {
        status,
        headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8' },
      });

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    const url = new URL(request.url);
    if (!url.pathname.startsWith('/k/')) return json({ error: 'not found' }, 404);

    // auth
    if (!originAllowed(origin, env)) return json({ error: 'forbidden origin' }, 403);

    const sub = url.pathname.slice(3); // after "/k/"
    const allowed = ALLOW.some((a) => a.method === request.method && a.re.test(sub));
    if (!allowed) return json({ error: 'endpoint not allowed', path: sub, method: request.method }, 403);

    const target = `https://${env.KOMMO_DOMAIN}/api/v4/${sub}${url.search}`;
    const init = {
      method: request.method,
      headers: {
        Authorization: `Bearer ${env.KOMMO_TOKEN}`,
        'Content-Type': 'application/json',
      },
    };
    if (request.method === 'POST' || request.method === 'DELETE') {
      init.body = await request.text();
    }

    const resp = await fetch(target, init);
    let body = await resp.text();
    // Kommo returns 204 + empty for empty lists; normalize so jQuery JSON parse is happy.
    const status = resp.status === 204 ? 200 : resp.status;
    if (!body) body = '{}';
    return json(body, status);
  },
};
