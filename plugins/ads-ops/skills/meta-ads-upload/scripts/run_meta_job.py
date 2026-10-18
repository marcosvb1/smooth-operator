#!/usr/bin/env python3
"""Unified runner for Meta Ads create/update/audit/duplicate jobs."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from meta_ads_core import MetaAdsClient
from meta_ads_core import MetaAdsError
from meta_ads_core import load_company_context
from meta_ads_core import write_json_report


def load_input(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise MetaAdsError("Input must include non-empty 'items' list")
    return items


def _build_output_path(output: str | None, mode: str, company: str) -> Path:
    if output:
        return Path(output)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path(os.getenv("ADS_OPS_RUNS_DIR", "ads-ops-runs")) / "meta"
    return runs_dir / f"{company}_{mode}_{stamp}.json"


def run_audit(client: MetaAdsClient, payload: dict[str, Any]) -> dict[str, Any]:
    campaign_id = payload.get("campaign_id")
    if not campaign_id:
        raise MetaAdsError("audit mode requires 'campaign_id'")

    adsets = client.get_campaign_adsets(str(campaign_id))
    next_number = client.get_next_adset_number(str(campaign_id))
    return {
        "campaign_id": campaign_id,
        "adsets_count": len(adsets),
        "next_adset_number": next_number,
        "adsets": adsets,
    }


def run_create_video_ads(
    client: MetaAdsClient, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    items = ensure_items(payload)
    url_tags = payload.get("url_tags")
    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {
            "ad_name": item.get("ad_name"),
            "adset_id": item.get("adset_id"),
            "status": "error",
        }
        try:
            ad_name = str(item["ad_name"])
            adset_id = str(item["adset_id"])
            link = str(item["link"])
            message = str(item["message"])

            video_id = item.get("video_id")
            if not video_id:
                video_url = str(item["video_url"])
                video_id = client.upload_video_from_url(video_url, ad_name)

            thumbnail_url = item.get("thumbnail_url")
            if not thumbnail_url:
                thumbnail_url = client.get_video_thumbnail(str(video_id))

            creative_id = client.create_creative_video(
                name=ad_name,
                video_id=str(video_id),
                message=message,
                link=link,
                thumbnail_url=str(thumbnail_url),
                url_tags=url_tags,
            )
            ad_id = client.create_ad(
                name=ad_name,
                adset_id=adset_id,
                creative_id=creative_id,
                status=str(item.get("status", "PAUSED")),
                tracking_specs=item.get("tracking_specs")
                or payload.get("tracking_specs"),
            )

            row.update(
                {
                    "video_id": str(video_id),
                    "thumbnail_url": str(thumbnail_url),
                    "creative_id": creative_id,
                    "ad_id": ad_id,
                    "status": "ok",
                }
            )
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)
    return output


def run_create_image_ads(
    client: MetaAdsClient, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    items = ensure_items(payload)
    url_tags = payload.get("url_tags")
    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {
            "ad_name": item.get("ad_name"),
            "adset_id": item.get("adset_id"),
            "status": "error",
        }
        try:
            ad_name = str(item["ad_name"])
            adset_id = str(item["adset_id"])
            link = str(item["link"])
            message = str(item["message"])

            image_hash = item.get("image_hash")
            if not image_hash and item.get("image_path"):
                image_hash = client.upload_image_from_path(str(item["image_path"]))
            if not image_hash and item.get("image_url"):
                image_hash = client.upload_image_from_url(str(item["image_url"]))
            if not image_hash:
                raise MetaAdsError("image_hash, image_path or image_url is required")

            creative_id = client.create_creative_image_link_data(
                name=ad_name,
                message=message,
                link=link,
                image_hash=str(image_hash),
                url_tags=url_tags,
            )
            ad_id = client.create_ad(
                name=ad_name,
                adset_id=adset_id,
                creative_id=creative_id,
                status=str(item.get("status", "PAUSED")),
                tracking_specs=item.get("tracking_specs")
                or payload.get("tracking_specs"),
            )

            row.update(
                {
                    "image_hash": str(image_hash),
                    "creative_id": creative_id,
                    "ad_id": ad_id,
                    "status": "ok",
                }
            )
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)
    return output


def run_create_adsets(
    client: MetaAdsClient, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    items = ensure_items(payload)
    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {
            "campaign_id": item.get("campaign_id"),
            "requested_name": item.get("name"),
            "status": "error",
        }
        try:
            campaign_id = str(item["campaign_id"])
            auto_number = bool(item.get("auto_number", False))
            name_template = str(item.get("name_template", "{num:02d} - Novo Adset"))
            name = item.get("name")
            if auto_number or not name:
                next_num = client.get_next_adset_number(campaign_id)
                name = name_template.format(num=next_num)

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

            row.update(
                {
                    "name": str(name),
                    "adset_id": adset_id,
                    "status": "ok",
                }
            )
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)
    return output


def run_create_existing_post_ads(
    client: MetaAdsClient, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    items = ensure_items(payload)
    default_url_tags = payload.get("url_tags")
    default_link = payload.get("link")
    default_status = str(payload.get("status", "PAUSED"))
    default_object_id = payload.get("object_id")
    default_tracking_specs = payload.get("tracking_specs")
    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {
            "ad_name": item.get("ad_name"),
            "adset_id": item.get("adset_id"),
            "post_id": item.get("post_id"),
            "status": "error",
        }
        try:
            ad_name = str(item["ad_name"])
            adset_id = str(item["adset_id"])
            post_id = str(item["post_id"])
            link = item.get("link") or default_link
            if not link:
                raise MetaAdsError(
                    "existing_post_ads requires link (item.link or payload.link)"
                )

            creative_id = client.create_creative_from_instagram_media(
                name=ad_name,
                source_instagram_media_id=post_id,
                link=str(link),
                object_id=str(item.get("object_id") or default_object_id or ""),
                url_tags=str(item.get("url_tags") or default_url_tags or ""),
                call_to_action_type=str(
                    item.get("call_to_action_type")
                    or payload.get("call_to_action_type")
                    or "LEARN_MORE"
                ),
            )
            ad_id = client.create_ad(
                name=ad_name,
                adset_id=adset_id,
                creative_id=creative_id,
                status=str(item.get("status", default_status)),
                tracking_specs=item.get("tracking_specs") or default_tracking_specs,
            )

            row.update(
                {
                    "creative_id": creative_id,
                    "ad_id": ad_id,
                    "status": "ok",
                }
            )
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)
    return output


def run_update_ads(
    client: MetaAdsClient, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    items = ensure_items(payload)
    url_tags = payload.get("url_tags")
    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {
            "ad_id": item.get("ad_id"),
            "status": "error",
        }
        try:
            ad_id = str(item["ad_id"])
            creative_id = item.get("creative_id")

            if not creative_id:
                creative_name = str(
                    item.get("creative_name") or f"creative_update_{ad_id}"
                )
                creative_id = client.create_creative_asset_feed(
                    name=creative_name,
                    message=str(item["message"]),
                    link=str(item["link"]),
                    feed_hash=str(item["feed_hash"]),
                    stories_hash=str(item["stories_hash"]),
                    url_tags=url_tags,
                )

            client.update_ad_creative(ad_id=ad_id, creative_id=str(creative_id))
            row.update({"creative_id": str(creative_id), "status": "ok"})
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)
    return output


def run_duplicate(
    client: MetaAdsClient, payload: dict[str, Any]
) -> dict[str, Any]:
    """Duplicate campaigns, adsets, or ads using Meta's /copies endpoint.

    This uses server-side duplication rather than read-and-recreate, which is
    faster and preserves internal references (pixels, audiences, etc.) that
    would be tedious to reconstruct manually.

    The input JSON follows the same items[] pattern as other modes. Each item
    needs an "id" field (the source object to clone).  Item-level fields
    override root-level defaults, so you can batch-duplicate with different
    settings per object.
    """
    job_type = str(payload.get("job_type", "")).strip().lower()
    items = ensure_items(payload)

    # Root-level defaults — items can override any of these
    defaults = {
        "deep_copy": payload.get("deep_copy", True),
        "rename_strategy": payload.get("rename_strategy", "DEEP_RENAME"),
        "rename_prefix": payload.get("rename_prefix"),
        "rename_suffix": payload.get("rename_suffix"),
        "status_option": payload.get("status_option", "PAUSED"),
        "start_time": payload.get("start_time"),
        "end_time": payload.get("end_time"),
    }

    output: list[dict[str, Any]] = []

    for item in items:
        row: dict[str, Any] = {"source_id": item.get("id"), "status": "error"}
        try:
            source_id = str(item["id"])

            # Merge item-level overrides with root defaults
            deep_copy = bool(item.get("deep_copy", defaults["deep_copy"]))
            rename_strategy = str(
                item.get("rename_strategy", defaults["rename_strategy"])
            )
            rename_prefix = item.get("rename_prefix", defaults["rename_prefix"])
            rename_suffix = item.get("rename_suffix", defaults["rename_suffix"])
            status_option = str(
                item.get("status_option", defaults["status_option"])
            )
            start_time = item.get("start_time", defaults["start_time"])
            end_time = item.get("end_time", defaults["end_time"])

            if job_type == "campaigns":
                data = client.copy_campaign(
                    campaign_id=source_id,
                    deep_copy=deep_copy,
                    rename_strategy=rename_strategy,
                    rename_prefix=rename_prefix,
                    rename_suffix=rename_suffix,
                    status_option=status_option,
                    start_time=str(start_time) if start_time else None,
                    end_time=str(end_time) if end_time else None,
                )
                row["copied_campaign_id"] = data.get("copied_campaign_id")
                row["ad_object_ids"] = data.get("ad_object_ids", [])

            elif job_type == "adsets":
                campaign_id = item.get("campaign_id") or payload.get(
                    "campaign_id"
                )
                data = client.copy_adset(
                    adset_id=source_id,
                    campaign_id=str(campaign_id) if campaign_id else None,
                    deep_copy=deep_copy,
                    rename_strategy=rename_strategy,
                    rename_prefix=rename_prefix,
                    rename_suffix=rename_suffix,
                    status_option=status_option,
                    start_time=str(start_time) if start_time else None,
                    end_time=str(end_time) if end_time else None,
                )
                row["copied_adset_id"] = data.get("copied_adset_id")
                row["ad_object_ids"] = data.get("ad_object_ids", [])

            elif job_type == "ads":
                adset_id = item.get("adset_id") or payload.get("adset_id")
                data = client.copy_ad(
                    ad_id=source_id,
                    adset_id=str(adset_id) if adset_id else None,
                    rename_strategy=rename_strategy,
                    rename_prefix=rename_prefix,
                    rename_suffix=rename_suffix,
                    status_option=status_option,
                )
                row["copied_ad_id"] = data.get("copied_ad_id")

            else:
                raise MetaAdsError(
                    "duplicate mode requires job_type in [campaigns, adsets, ads]"
                )

            row["status"] = "ok"
        except Exception as exc:
            row["error"] = str(exc)
        output.append(row)

    return {
        "job_type": f"duplicate_{job_type}",
        "ok": sum(1 for r in output if r["status"] == "ok"),
        "error": sum(1 for r in output if r["status"] != "ok"),
        "items": output,
    }


def run_create(client: MetaAdsClient, payload: dict[str, Any]) -> dict[str, Any]:
    job_type = str(payload.get("job_type", "")).strip().lower()
    if job_type == "video_ads":
        items = run_create_video_ads(client, payload)
    elif job_type == "image_ads":
        items = run_create_image_ads(client, payload)
    elif job_type == "adsets":
        items = run_create_adsets(client, payload)
    elif job_type == "existing_post_ads":
        items = run_create_existing_post_ads(client, payload)
    else:
        raise MetaAdsError(
            "create mode requires job_type in [video_ads, image_ads, adsets, existing_post_ads]"
        )

    return {
        "job_type": job_type,
        "ok": sum(1 for item in items if item["status"] == "ok"),
        "error": sum(1 for item in items if item["status"] != "ok"),
        "items": items,
    }


def run_update(client: MetaAdsClient, payload: dict[str, Any]) -> dict[str, Any]:
    items = run_update_ads(client, payload)
    return {
        "job_type": "ad_creative_update",
        "ok": sum(1 for item in items if item["status"] == "ok"),
        "error": sum(1 for item in items if item["status"] != "ok"),
        "items": items,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Meta Ads job (create/update/audit/duplicate)"
    )
    parser.add_argument(
        "--profile",
        "--company",
        dest="company",
        default=None,
        help="Profile name from the ads-ops config (see /ads-ops:setup). "
        "Defaults to meta.default_profile, then env vars.",
    )
    parser.add_argument(
        "--mode", required=True, choices=["create", "update", "audit", "duplicate"]
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
    try:
        placeholders = find_placeholders(payload)
        if placeholders:
            raise MetaAdsError(
                "Input still has unfilled placeholders at: " + ", ".join(placeholders)
            )
        context = load_company_context(args.company, overrides=payload.get("context"))
    except (MetaAdsError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    client = MetaAdsClient(context=context, dry_run=not args.execute)

    output_path = _build_output_path(args.output, args.mode, context.company)

    try:
        if args.mode == "audit":
            result = run_audit(client, payload)
        elif args.mode == "create":
            result = run_create(client, payload)
        elif args.mode == "duplicate":
            result = run_duplicate(client, payload)
        else:
            result = run_update(client, payload)
    except Exception as exc:
        report = {
            "profile": context.company,
            "mode": args.mode,
            "dry_run": not args.execute,
            "status": "error",
            "error": str(exc),
        }
        write_json_report(output_path, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    failed = int(result.get("error") or 0) if isinstance(result, dict) else 0
    report = {
        "profile": context.company,
        "ad_account": context.ad_account,
        "mode": args.mode,
        "dry_run": not args.execute,
        "status": "partial" if failed else "ok",
        "result": result,
    }
    if not args.execute:
        report["planned_calls"] = client.planned_calls
    write_json_report(output_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
