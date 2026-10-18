#!/usr/bin/env python3
"""
resolve_ids.py — Build a live account-ID inventory for a Kommo account.

The Salesbot export format embeds account-specific numeric IDs in many places
(pipeline_id, status_id, custom_field id + enum id, responsible_user_id, and
chat_sources channel ids). Those IDs differ per account and must NEVER be copied
from another account's bot. This script resolves them live so the generator and
validator can fill/verify them.

Resolvable via the public v4 API:  pipelines, statuses, users, custom fields (+enums).
NOT resolvable via the public v4 API:  chat_sources (messaging channels) — `/api/v4/sources`
returns 204 (or only the calling integration's own sources). Those are amojo channel ids.
This script flags that gap and, if given existing exported bots, lists the distinct
chat_source ids found in them so a human can confirm which belong to this account.

Credentials follow the kommo plugin convention (same as kommo-crm/scripts/kommo_env.sh):
  config (no tokens): $KOMMO_CONFIG, then ./.claude/kommo.local.json, then ~/.claude/kommo.local.json
      {"default_profile": "cliente-a", "profiles": {"cliente-a": {"domain": "cliente-a.kommo.com"}}}
  domain: env KOMMO_DOMAIN_<PROFILE> > profiles.<profile>.domain > env KOMMO_DOMAIN
  token:  env KOMMO_ACCESS_TOKEN_<PROFILE> > env KOMMO_ACCESS_TOKEN   (never from a file)
  <PROFILE> = profile name uppercased, '-' -> '_'.

Usage:
  python3 resolve_ids.py cliente-a
  python3 resolve_ids.py cliente-a --out /tmp/inv.cliente-a.json
  python3 resolve_ids.py cliente-a --scan-bots /path/to/exports
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

RATE_SLEEP = 0.18  # ~7 req/s ceiling

def find_config():
    explicit = os.environ.get("KOMMO_CONFIG")
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    for cand in (os.path.join(os.getcwd(), ".claude", "kommo.local.json"),
                 os.path.expanduser("~/.claude/kommo.local.json")):
        if os.path.isfile(cand):
            return cand
    return None


def env_key(profile):
    return profile.upper().replace("-", "_")


def load_creds(profile=None):
    """Return (profile, domain, token) using the kommo plugin convention."""
    cfg_path = find_config()
    cfg = {}
    if cfg_path:
        with open(cfg_path) as fh:
            cfg = json.load(fh)
    profiles = cfg.get("profiles", {}) or {}
    if not profile:
        profile = cfg.get("default_profile")
        if not profile and len(profiles) == 1:
            profile = next(iter(profiles))
        if not profile and len(profiles) > 1:
            sys.exit(f"ERROR: several profiles in {cfg_path} and no default_profile: {sorted(profiles)}. "
                     "Pass the profile explicitly.")
    key = env_key(profile) if profile else None
    domain = (os.environ.get(f"KOMMO_DOMAIN_{key}") if key else None) \
        or (profiles.get(profile, {}).get("domain") if profile else None) \
        or os.environ.get("KOMMO_DOMAIN")
    token = (os.environ.get(f"KOMMO_ACCESS_TOKEN_{key}") if key else None) \
        or os.environ.get("KOMMO_ACCESS_TOKEN")
    if not domain:
        sys.exit(f"ERROR: no Kommo domain for profile '{profile}'. Run /kommo:setup or set "
                 f"KOMMO_DOMAIN_{key or '<PROFILE>'}.")
    if not token:
        sys.exit(f"ERROR: no token. Set KOMMO_ACCESS_TOKEN_{key or '<PROFILE>'} (or KOMMO_ACCESS_TOKEN).")
    if not domain.startswith(("https://", "http://")):
        domain = "https://" + domain
    return profile or "default", domain.rstrip("/"), token


def api_get(domain, token, path, params=None):
    """GET helper. Returns (status_code, parsed_json_or_None)."""
    url = domain + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.getcode()
            body = resp.read().decode("utf-8")
            if code == 204 or not body.strip():
                return code, None
            return code, json.loads(body)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:  # noqa: BLE001
        print(f"  ! request error {path}: {e}", file=sys.stderr)
        return -1, None


def paginate(domain, token, path, embed_key):
    """Walk _links.next pages, collecting _embedded[embed_key]."""
    out = []
    page = 1
    while True:
        code, data = api_get(domain, token, path, {"limit": 250, "page": page})
        if code != 200 or not data:
            break
        items = data.get("_embedded", {}).get(embed_key, [])
        out.extend(items)
        if not data.get("_links", {}).get("next"):
            break
        page += 1
        time.sleep(RATE_SLEEP)
    return out


def fetch_pipelines(domain, token):
    code, data = api_get(domain, token, "/api/v4/leads/pipelines")
    time.sleep(RATE_SLEEP)
    if code != 200 or not data:
        return []
    out = []
    for p in data.get("_embedded", {}).get("pipelines", []):
        statuses = [
            {"id": s["id"], "name": s["name"]}
            for s in p.get("_embedded", {}).get("statuses", [])
        ]
        out.append({"id": p["id"], "name": p["name"], "statuses": statuses})
    return out


def fetch_users(domain, token):
    code, data = api_get(domain, token, "/api/v4/users")
    time.sleep(RATE_SLEEP)
    if code != 200 or not data:
        return []
    return [
        {"id": u["id"], "name": u.get("name"), "email": u.get("email")}
        for u in data.get("_embedded", {}).get("users", [])
    ]


def fetch_custom_fields(domain, token, entity):
    raw = paginate(domain, token, f"/api/v4/{entity}/custom_fields", "custom_fields")
    out = []
    for f in raw:
        enums = [
            {"id": e["id"], "value": e.get("value")}
            for e in (f.get("enums") or [])
        ]
        out.append(
            {"id": f["id"], "name": f.get("name"), "type": f.get("type"), "enums": enums}
        )
    return out


def fetch_chat_sources(domain, token):
    """Try /api/v4/sources. Usually 204 or only the integration's own sources. Report honestly."""
    code, data = api_get(domain, token, "/api/v4/sources")
    time.sleep(RATE_SLEEP)
    if code == 200 and data:
        srcs = data.get("_embedded", {}).get("sources", [])
        return {
            "resolvable_via_api": True,
            "sources": [
                {"id": s.get("id"), "name": s.get("name"), "pipeline_id": s.get("pipeline_id")}
                for s in srcs
            ],
        }
    return {
        "resolvable_via_api": False,
        "http_status": code,
        "note": (
            "chat_sources (messaging channel ids used in send_message) are NOT enumerable "
            "via /api/v4/sources. Lift the correct channel id from an existing working bot "
            "for the same channel in THIS account, or confirm with the account owner. "
            "Use --scan-bots to list ids seen in existing exports."
        ),
    }


def scan_bots_for_chat_sources(folder):
    """Extract distinct chat_source ids from exported bots (model.text)."""
    found = {}
    for name in os.listdir(folder):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(folder, name)) as fh:
                wrapper = json.load(fh)
            text = json.loads(wrapper.get("model", {}).get("text", "{}"))
        except Exception:  # noqa: BLE001
            continue
        for step in text.values():
            if not isinstance(step, dict):
                continue
            for block in ("question", "answer", "finish"):
                for h in step.get(block, []) or []:
                    p = (h or {}).get("params", {})
                    if not isinstance(p, dict):
                        continue
                    for cs in p.get("chat_sources", []) or []:
                        cid = cs.get("id")
                        if cid is not None:
                            found.setdefault(cid, []).append(name)
    return [{"id": cid, "seen_in": sorted(set(files))} for cid, files in sorted(found.items())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", nargs="?", help="profile in kommo.local.json, e.g. cliente-a (default: default_profile)")
    ap.add_argument("--out", help="write inventory JSON to this path (default: stdout)")
    ap.add_argument("--scan-bots", help="folder of exported bots to extract chat_source ids from")
    args = ap.parse_args()

    profile, domain, token = load_creds(args.profile)

    code, acct = api_get(domain, token, "/api/v4/account")
    time.sleep(RATE_SLEEP)
    if code != 200 or not acct:
        sys.exit(f"ERROR: /account returned {code}. Token may be expired.")

    print(f"Resolving inventory for {profile} ({acct.get('name')}, id {acct.get('id')})...", file=sys.stderr)

    inventory = {
        "profile": profile,
        "account_id": acct.get("id"),
        "account_name": acct.get("name"),
        "domain": domain,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "pipelines": fetch_pipelines(domain, token),
        "users": fetch_users(domain, token),
        "lead_custom_fields": fetch_custom_fields(domain, token, "leads"),
        "contact_custom_fields": fetch_custom_fields(domain, token, "contacts"),
        "chat_sources": fetch_chat_sources(domain, token),
    }
    if args.scan_bots:
        inventory["chat_sources"]["from_existing_bots"] = scan_bots_for_chat_sources(args.scan_bots)

    n_status = sum(len(p["statuses"]) for p in inventory["pipelines"])
    print(
        f"  pipelines={len(inventory['pipelines'])} statuses={n_status} "
        f"users={len(inventory['users'])} lead_cf={len(inventory['lead_custom_fields'])} "
        f"contact_cf={len(inventory['contact_custom_fields'])} "
        f"chat_sources_api={inventory['chat_sources']['resolvable_via_api']}",
        file=sys.stderr,
    )

    out_json = json.dumps(inventory, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out_json)
        print(f"  wrote {args.out}", file=sys.stderr)
    else:
        print(out_json)


if __name__ == "__main__":
    main()
