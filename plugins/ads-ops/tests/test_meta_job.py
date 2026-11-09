#!/usr/bin/env python3
"""Offline test of the Meta Ads runner: every template runs, no real write leaves dry-run,
and --execute sends what the template asks for. The Graph API is faked; no token needed.

Run: python3 plugins/ads-ops/tests/test_meta_job.py   (needs `requests` installed)
"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skills" / "meta-ads-upload"
sys.path.insert(0, str(SKILL / "scripts"))

import requests  # noqa: E402

import meta_ads_core  # noqa: E402
import run_meta_job  # noqa: E402

TEMPLATES = sorted(p.name.replace(".template.json", "") for p in (SKILL / "templates").glob("*.template.json"))
BASE = None  # set in main() from the context, so the version lives only in meta_ads_core
SENT = []


class Response:
    status_code = 200

    def __init__(self, data):
        self.data = data
        self.text = json.dumps(data)

    def json(self):
        return self.data


def fake_graph(method, url, params=None, data=None, files=None, headers=None, timeout=None):
    path = url.removeprefix(BASE + "/")
    SENT.append((method, path, params if method == "GET" else data))
    if method == "GET":
        if path.endswith("/adsets"):
            return Response({"data": [{"id": "1", "name": "07 - Broad"}, {"id": "2", "name": "sem número"}]})
        return Response({"picture": "https://example.com/thumb.jpg"})
    if path.endswith("/copies"):
        return Response({"copied_campaign_id": "c1", "copied_adset_id": "s1", "copied_ad_id": "a1"})
    return Response({"id": f"id{len(SENT)}"})


class Download:
    content = b"\x89PNG fake"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass


def run(name, execute, fill="42"):
    raw = (SKILL / "templates" / f"{name}.template.json").read_text()
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = Path(tmp, "in.json"), Path(tmp, "out.json")
        inp.write_text(re.sub(r"<[A-Z0-9_]+>", fill, raw) if fill else raw)
        sys.argv = ["run_meta_job", "--input", str(inp), "--output", str(out)]
        sys.argv += ["--execute"] if execute else []
        SENT.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_meta_job.main()
        return rc, json.loads(out.read_text()), list(SENT)


def main():
    requests.request = fake_graph
    requests.get = lambda url, timeout=None: Download()
    meta_ads_core.time.sleep = lambda seconds: None
    home = tempfile.mkdtemp()  # no ads-ops config: the context comes from the env vars below
    os.chdir(home)
    os.environ["HOME"] = home
    os.environ.pop("ADS_OPS_CONFIG", None)
    os.environ.update(META_ACCESS_TOKEN="dummy", META_AD_ACCOUNT="123", META_PAGE_ID="9", META_IG_USER_ID="77")
    global BASE
    BASE = meta_ads_core.load_profile_context().base_url
    failures = []

    def check(cond, msg):
        if not cond:
            failures.append(msg)

    check(sorted(run_meta_job.JOBS) == TEMPLATES, f"one template per job_type: {TEMPLATES}")
    for name in TEMPLATES:
        rc, report, sent = run(name, execute=False)
        check(report["status"] == "ok" and report["job_type"] == name, f"{name}: dry-run {report}")
        check(all(method == "GET" for method, _, _ in sent), f"{name}: dry-run sent a write")

    rc, report, sent = run("image_ads", execute=False, fill=None)
    check(rc == 1 and "placeholders" in report["error"] and not sent, "unfilled template: error report, no calls")

    client = meta_ads_core.MetaAdsClient(meta_ads_core.load_profile_context(), dry_run=True)
    result = run_meta_job.JOBS["adsets"](client, {"campaign_id": "42", "items": [{"name": "x"}]})
    check(result["items"][0]["error"] == "missing field 'daily_budget'", f"missing field: {result}")

    two = {"campaign_id": "42", "auto_number": True, "daily_budget": 1, "optimization_goal": "x",
           "billing_event": "y", "targeting": {}, "items": [{}, {}]}
    result = run_meta_job.JOBS["adsets"](meta_ads_core.MetaAdsClient(client.context, dry_run=True), two)
    check([r.get("name") for r in result["items"]] == ["08 - Novo Adset", "09 - Novo Adset"],
          f"dry-run numbering counts up per item: {result}")

    rc, report, sent = run("image_ads", execute=False)
    uploads = [c for c in report["planned_calls"] if c["path"] == "act_123/adimages"]
    check(len(uploads) == 1 and report["result"]["items"][1]["image_hash"] == "dry_hash_ad02.png",
          f"image_url is downloaded and its upload planned: {report['result']}")

    rc, report, sent = run("video_ads", execute=False)
    planned = [c["path"] for c in report["planned_calls"]]
    check("act_123/advideos" in planned, f"dry-run upload is in planned_calls: {planned}")

    try:
        meta_ads_core.load_profile_context("nao-existe")
        check(False, "unknown --profile must not fall back to the generic env vars")
    except meta_ads_core.MetaAdsError:
        pass

    rc, report, _ = run("audit", execute=False)
    check(report["result"]["next_adset_number"] == 8, "audit: next number after '07 - ...' is 8")

    rc, report, sent = run("duplicate_adsets", execute=True)
    check(report["result"]["items"][0]["copied_adset_id"] == "s1", "duplicate: copied id in the report")
    check(sent == [("POST", "42/copies", {"deep_copy": "true", "rename_strategy": "DEEP_RENAME",
                                          "rename_suffix": " - Copy", "status_option": "PAUSED"})],
          f"duplicate_adsets: sent {sent}")

    rc, report, sent = run("existing_post_ads", execute=True)
    ads = [data for method, path, data in sent if path == "act_123/ads"]
    check(len(ads) == 2 and all(json.loads(a["tracking_specs"])[0]["fb_pixel"] == ["42"] for a in ads),
          "existing_post_ads: root tracking_specs reaches every ad")
    creatives = [data for method, path, data in sent if path == "act_123/adcreatives"]
    check(all(c["instagram_user_id"] == "77" and c["object_id"] == "9" for c in creatives),
          "existing_post_ads: creative uses the IG account and the page")

    rc, report, sent = run("video_ads", execute=True)
    check(report["status"] == "ok" and report["result"]["ok"] == 2, f"video_ads: {report['result']}")
    spec = json.loads([d for m, p, d in sent if p == "act_123/adcreatives"][0]["object_story_spec"])
    check(spec["page_id"] == "9" and spec["instagram_user_id"] == "77" and "video_data" in spec,
          "video_ads: story spec carries page, IG account and video")

    for f in failures:
        print("FAILED:", f)
    print("meta job tests passed" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
