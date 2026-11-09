#!/usr/bin/env python3
"""Runner for Meta Ads jobs. The input file's job_type picks the job (see JOBS)."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from meta_ads_core import MetaAdsClient
from meta_ads_core import MetaAdsError
from meta_ads_core import adset_number
from meta_ads_core import load_profile_context
from meta_ads_core import write_json_report


def load_input(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class Item(dict):
    """A job item: reading a field it doesn't have is a "missing field" error."""

    def __missing__(self, key: str) -> Any:
        raise MetaAdsError(f"missing field {key!r}")


def job_items(payload: dict[str, Any]) -> list[Item]:
    """Each item with the root fields as defaults: an item field wins, a null is absent."""
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise MetaAdsError("Input must include non-empty 'items' list")
    root = {k: v for k, v in payload.items() if k != "items" and v is not None}
    return [Item({**root, **{k: v for k, v in item.items() if v is not None}}) for item in items]


def run_items(
    client: MetaAdsClient,
    payload: dict[str, Any],
    seed: dict[str, str],
    job: Callable[[MetaAdsClient, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Run job per item; one failing item doesn't stop the others. seed maps report
    fields to item fields, copied into the row even when the item fails."""
    rows: list[dict[str, Any]] = []
    for item in job_items(payload):
        row: dict[str, Any] = {out: item.get(key) for out, key in seed.items()}
        try:
            row.update(job(client, item))
            row["status"] = "ok"
        except Exception as exc:
            row.update(status="error", error=str(exc))
        rows.append(row)
    return {
        "ok": sum(1 for r in rows if r["status"] == "ok"),
        "error": sum(1 for r in rows if r["status"] != "ok"),
        "items": rows,
    }


def _build_output_path(output: str | None, job_type: str, profile: str) -> Path:
    if output:
        return Path(output)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path(os.getenv("ADS_OPS_RUNS_DIR", "ads-ops-runs")) / "meta"
    return runs_dir / f"{profile}_{job_type or 'unknown'}_{stamp}.json"


def run_audit(client: MetaAdsClient, payload: dict[str, Any]) -> dict[str, Any]:
    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        raise MetaAdsError("audit requires 'campaign_id'")

    adsets = client.get_campaign_adsets(str(campaign_id))
    return {
        "campaign_id": campaign_id,
        "adsets_count": len(adsets),
        "next_adset_number": max(map(adset_number, (a.get("name") for a in adsets)), default=0) + 1,
        "adsets": adsets,
    }


def place_ad(client: MetaAdsClient, item: dict[str, Any], creative_id: str) -> dict[str, Any]:
    ad_id = client.create_ad(
        name=str(item["ad_name"]),
        adset_id=str(item["adset_id"]),
        creative_id=creative_id,
        status=str(item.get("status", "PAUSED")),
        tracking_specs=item.get("tracking_specs"),
    )
    return {"creative_id": creative_id, "ad_id": ad_id}


def video_ad(client: MetaAdsClient, item: dict[str, Any]) -> dict[str, Any]:
    video_id = str(
        item.get("video_id")
        or client.upload_video_from_url(str(item["video_url"]), str(item["ad_name"]))
    )
    thumbnail_url = str(item.get("thumbnail_url") or client.get_video_thumbnail(video_id))
    creative_id = client.create_creative_video(
        name=str(item["ad_name"]),
        video_id=video_id,
        message=str(item["message"]),
        link=str(item["link"]),
        thumbnail_url=thumbnail_url,
        url_tags=item.get("url_tags"),
    )
    return {"video_id": video_id, "thumbnail_url": thumbnail_url, **place_ad(client, item, creative_id)}


def image_ad(client: MetaAdsClient, item: dict[str, Any]) -> dict[str, Any]:
    image_hash = item.get("image_hash")
    if not image_hash and item.get("image_path"):
        image_hash = client.upload_image_from_path(str(item["image_path"]))
    if not image_hash and item.get("image_url"):
        image_hash = client.upload_image_from_url(str(item["image_url"]))
    if not image_hash:
        raise MetaAdsError("image_hash, image_path or image_url is required")
    creative_id = client.create_creative_image_link_data(
        name=str(item["ad_name"]),
        message=str(item["message"]),
        link=str(item["link"]),
        image_hash=str(image_hash),
        url_tags=item.get("url_tags"),
    )
    return {"image_hash": str(image_hash), **place_ad(client, item, creative_id)}


def existing_post_ad(client: MetaAdsClient, item: dict[str, Any]) -> dict[str, Any]:
    if not item.get("link"):
        raise MetaAdsError("existing_post_ads requires link (item.link or payload.link)")
    creative_id = client.create_creative_from_instagram_media(
        name=str(item["ad_name"]),
        source_instagram_media_id=str(item["post_id"]),
        link=str(item["link"]),
        object_id=item.get("object_id"),
        url_tags=item.get("url_tags"),
        call_to_action_type=str(item.get("call_to_action_type") or "LEARN_MORE"),
    )
    return place_ad(client, item, creative_id)


def run_adsets(client: MetaAdsClient, payload: dict[str, Any]) -> dict[str, Any]:
    """Create ad sets. Each campaign's highest number is read once and counted up
    locally, so a dry-run plans the same names --execute will create."""
    highest: dict[str, int] = {}

    def adset(client: MetaAdsClient, item: dict[str, Any]) -> dict[str, Any]:
        campaign_id = str(item["campaign_id"])
        if campaign_id not in highest:
            names = (a.get("name") for a in client.get_campaign_adsets(campaign_id))
            highest[campaign_id] = max(map(adset_number, names), default=0)
        row = create_adset(client, item, campaign_id, highest[campaign_id] + 1)
        highest[campaign_id] = max(highest[campaign_id], adset_number(row["name"]))
        return row

    return run_items(client, payload, {"campaign_id": "campaign_id", "requested_name": "name"}, adset)


def create_adset(client: MetaAdsClient, item: dict[str, Any], campaign_id: str, next_number: int) -> dict[str, Any]:
    name = item.get("name")
    if item.get("auto_number") or not name:
        template = str(item.get("name_template", "{num:02d} - Novo Adset"))
        name = template.format(num=next_number)
    adset_id = client.create_adset(
        campaign_id=campaign_id,
        name=str(name),
        daily_budget=int(item["daily_budget"]),
        optimization_goal=str(item["optimization_goal"]),
        billing_event=str(item["billing_event"]),
        bid_strategy=item.get("bid_strategy") or None,
        targeting=dict(item["targeting"]),
        promoted_object=dict(item.get("promoted_object", {})) or None,
        status=str(item.get("status", "PAUSED")),
    )
    return {"name": str(name), "adset_id": adset_id}


def ad_creative_update(client: MetaAdsClient, item: dict[str, Any]) -> dict[str, Any]:
    ad_id = str(item["ad_id"])
    creative_id = item.get("creative_id") or client.create_creative_asset_feed(
        name=str(item.get("creative_name") or f"creative_update_{ad_id}"),
        message=str(item["message"]),
        link=str(item["link"]),
        feed_hash=str(item["feed_hash"]),
        stories_hash=str(item["stories_hash"]),
        url_tags=item.get("url_tags"),
    )
    client.update_ad_creative(ad_id=ad_id, creative_id=str(creative_id))
    return {"creative_id": str(creative_id)}


def duplicate(level: str) -> Callable[[MetaAdsClient, dict[str, Any]], dict[str, Any]]:
    """Clone item["id"] with Meta's /copies endpoint (see MetaAdsClient.copy)."""
    return lambda client, item: client.copy(level, str(item["id"]), item)


def items_job(
    seed: dict[str, str], job: Callable[[MetaAdsClient, dict[str, Any]], dict[str, Any]]
) -> Callable[[MetaAdsClient, dict[str, Any]], dict[str, Any]]:
    return lambda client, payload: run_items(client, payload, seed, job)


AD_SEED = {"ad_name": "ad_name", "adset_id": "adset_id"}
# job_type -> job. Each template in ../templates is named after its job_type.
JOBS: dict[str, Callable[[MetaAdsClient, dict[str, Any]], dict[str, Any]]] = {
    "audit": run_audit,
    "adsets": run_adsets,
    "video_ads": items_job(AD_SEED, video_ad),
    "image_ads": items_job(AD_SEED, image_ad),
    "existing_post_ads": items_job({**AD_SEED, "post_id": "post_id"}, existing_post_ad),
    "update_ads": items_job({"ad_id": "ad_id"}, ad_creative_update),
    "duplicate_campaigns": items_job({"source_id": "id"}, duplicate("campaigns")),
    "duplicate_adsets": items_job({"source_id": "id"}, duplicate("adsets")),
    "duplicate_ads": items_job({"source_id": "id"}, duplicate("ads")),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Meta Ads job named by the input's job_type: " + ", ".join(JOBS)
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Profile name from the ads-ops config (see /ads-ops:setup). "
        "Defaults to meta.default_profile, then env vars.",
    )
    parser.add_argument("--input", required=True, help="Path to JSON input file")
    parser.add_argument("--output", help="Path to JSON output file")
    parser.add_argument(
        "--execute", action="store_true", help="Run real API calls. Default is dry-run."
    )
    return parser.parse_args()


def find_placeholders(value: Any, path: str = "$") -> list[str]:
    """Return JSON paths whose string values still hold <PLACEHOLDER> markers."""
    if isinstance(value, dict):
        return [
            hit
            for key, child in value.items()
            if not str(key).startswith("_")
            for hit in find_placeholders(child, f"{path}.{key}")
        ]
    if isinstance(value, list):
        return [
            hit
            for index, child in enumerate(value)
            for hit in find_placeholders(child, f"{path}[{index}]")
        ]
    if isinstance(value, str) and re.search(r"<[A-Z0-9_]+>", value):
        return [path]
    return []


def main() -> int:
    args = parse_args()
    payload = load_input(Path(args.input))
    job_type = str(payload.get("job_type", "")).strip().lower()
    report: dict[str, Any] = {
        "profile": args.profile,
        "job_type": job_type,
        "dry_run": not args.execute,
    }
    output_path = _build_output_path(args.output, job_type, args.profile or "default")

    def finish(code: int) -> int:
        write_json_report(output_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return code

    try:
        if job_type not in JOBS:
            raise MetaAdsError(f"job_type must be one of: {', '.join(JOBS)}")
        placeholders = find_placeholders(payload)
        if placeholders:
            raise MetaAdsError(
                "Input still has unfilled placeholders at: " + ", ".join(placeholders)
            )
        context = load_profile_context(args.profile, overrides=payload.get("context"))
        report.update(profile=context.profile, ad_account=context.ad_account)
        output_path = _build_output_path(args.output, job_type, context.profile)
        client = MetaAdsClient(context=context, dry_run=not args.execute)
        result = JOBS[job_type](client, payload)
    except Exception as exc:
        report.update(status="error", error=str(exc))
        return finish(1)

    failed = int(result.get("error") or 0)
    report.update(status="partial" if failed else "ok", result=result)
    if not args.execute:
        report["planned_calls"] = client.planned_calls
    return finish(2 if failed else 0)


if __name__ == "__main__":
    raise SystemExit(main())
