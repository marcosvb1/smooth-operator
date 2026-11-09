// Local HTTPS dev server for Kommo widget dev mode + API proxy.
//   - Serves ./widget over https://localhost:9000 (script.js, i18n, images) with CORS.
//   - Proxies /k/<path> -> https://<domain>/api/v4/<path> injecting the integration
//     Bearer token server-side, ONLY for the routes in worker/src/allow.json (the
//     same whitelist the Worker uses), so the widget UI can hit integration-only
//     endpoints like /sources that the admin session can't.
//
// Credentials come from the plugin's resolver, which exports DOMAIN and TOKEN:
//   source "${CLAUDE_PLUGIN_ROOT}/scripts/kommo_env.sh" && kommo_load_credentials <perfil> \
//     && node devserver.js
//   ALLOWED_ORIGIN (optional) pins the one Kommo account allowed to call the proxy.
//
// Localhost-only, dev use. Needs dev-key.pem / dev-cert.pem next to this file and
// the worker/ folder (for allow.json) copied alongside it.
const https = require('https');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.join(__dirname, 'widget');
const PORT = 9000;

if (!process.env.DOMAIN || !process.env.TOKEN) {
  console.error('DOMAIN/TOKEN not set. Run: source "${CLAUDE_PLUGIN_ROOT}/scripts/kommo_env.sh" && kommo_load_credentials <perfil>');
  process.exit(2);
}
const KOMMO_HOST = process.env.DOMAIN.replace(/^https?:\/\//, '').replace(/\/$/, '');
const TOKEN = process.env.TOKEN;
const KOMMO_ORIGIN = /^https:\/\/[a-z0-9-]+\.kommo\.com$/;
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || '';
const ALLOW_RAW = require('./worker/src/allow.json');
const ALLOW = ALLOW_RAW.map(function (a) {
  return { method: a.method, re: new RegExp(a.path) };
});
const ALLOW_METHODS = Array.from(new Set(ALLOW_RAW.map(function (a) { return a.method; })))
  .concat('OPTIONS').join(', ');

function originAllowed(o) {
  return KOMMO_ORIGIN.test(o) && (!ALLOWED_ORIGIN || o === ALLOWED_ORIGIN);
}

function routeAllowed(method, sub) {
  return ALLOW.some(function (a) { return a.method === method && a.re.test(sub); });
}

const TYPES = {
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png', '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8'
};

const opts = {
  key: fs.readFileSync(path.join(__dirname, 'dev-key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'dev-cert.pem'))
};

function cors(req, res) {
  var o = req.headers.origin || '';
  res.setHeader('Access-Control-Allow-Origin', originAllowed(o) ? o : 'https://' + KOMMO_HOST);
  res.setHeader('Access-Control-Allow-Methods', ALLOW_METHODS);
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With');
}

function proxy(req, res, rest) {
  var body = [];
  req.on('data', function (c) { body.push(c); });
  req.on('end', function () {
    var payload = Buffer.concat(body);
    var preq = https.request({
      host: KOMMO_HOST, port: 443, method: req.method,
      path: '/api/v4/' + rest,
      headers: {
        'Authorization': 'Bearer ' + TOKEN,
        'Content-Type': 'application/json',
        'Content-Length': payload.length
      }
    }, function (pres) {
      var out = [];
      pres.on('data', function (c) { out.push(c); });
      pres.on('end', function () {
        cors(req, res);
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        var bodyOut = Buffer.concat(out);
        // Kommo replies 204 + empty body for empty lists; jQuery json parse chokes.
        var status = pres.statusCode === 204 ? 200 : pres.statusCode;
        if (!bodyOut.length) bodyOut = Buffer.from('{}');
        res.writeHead(status);
        res.end(bodyOut);
        console.log(req.method, '/k/' + rest, '->', pres.statusCode);
      });
    });
    preq.on('error', function (e) { cors(req, res); res.writeHead(502); res.end(JSON.stringify({ error: String(e) })); });
    if (payload.length) preq.write(payload);
    preq.end();
  });
}

https.createServer(opts, function (req, res) {
  cors(req, res);
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }

  var url = decodeURIComponent(req.url.split('?')[0]);
  var qs = req.url.indexOf('?') > -1 ? req.url.slice(req.url.indexOf('?')) : '';

  // API proxy: /k/<kommo v4 path>
  if (url.indexOf('/k/') === 0) {
    if (!originAllowed(req.headers.origin || '')) { res.writeHead(403); return res.end('origin'); }
    var sub = url.slice(3);
    if (!routeAllowed(req.method, sub)) { res.writeHead(403); return res.end('endpoint not allowed: ' + req.method + ' ' + sub); }
    return proxy(req, res, sub + qs);
  }

  // static widget files
  if (url === '/' || url === '') url = '/manifest.json';
  var fp = path.join(ROOT, url);
  if (!fp.startsWith(ROOT)) { res.writeHead(403); return res.end('forbidden'); }
  fs.readFile(fp, function (err, data) {
    if (err) { console.log('404', url); res.writeHead(404); return res.end('not found'); }
    res.setHeader('Content-Type', TYPES[path.extname(fp)] || 'application/octet-stream');
    res.writeHead(200); res.end(data);
    console.log('200', url);
  });
}).listen(PORT, function () {
  console.log('dev server + proxy: https://localhost:' + PORT + ' (kommo=' + KOMMO_HOST + ')');
});
