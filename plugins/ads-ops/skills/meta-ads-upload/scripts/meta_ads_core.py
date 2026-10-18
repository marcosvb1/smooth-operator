#!/usr/bin/env python3
"""Meta Ads core helpers for create/update/audit workflows."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


CONFIG_ENV = "ADS_OPS_CONFIG"
CONFIG_FILENAME = "ads-ops.local.json"


class MetaAdsError(RuntimeError):
    pass


@dataclass
class CompanyContext:
    company: str
    access_token: str
    ad_account: str
    page_id: str
    ig_user_id: str
    api_version: str = "v25.0"

    @property
    def base_url(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}"


def find_config_path() -> Path | None:
    """Locate the ads-ops config: $ADS_OPS_CONFIG, ./.claude, then ~/.claude."""
    explicit = os.getenv(CONFIG_ENV)
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise MetaAdsError(f"{CONFIG_ENV} points to a missing file: {path}")
        return path
    for base in (Path.cwd() / ".claude", Path.home() / ".claude"):
        path = base / CONFIG_FILENAME
        if path.is_file():
            return path
    return None


def load_meta_profiles() -> tuple[dict[str, dict[str, Any]], str | None]:
    """Return (profiles, default_profile) from the 'meta' section of the config."""
    path = find_config_path()
    if path is None:
        return {}, None
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    meta = config.get("meta") or {}
    profiles = {str(k).lower(): v for k, v in (meta.get("profiles") or {}).items()}
    default = meta.get("default_profile")
    return profiles, (str(default).lower() if default else None)


def load_company_context(
    company: str | None = None, overrides: dict[str, Any] | None = None
) -> CompanyContext:
    profiles, default_profile = load_meta_profiles()
    key = (company or default_profile or "default").lower().strip()
    if company and profiles and key not in profiles:
        raise MetaAdsError(
            f"Profile '{key}' not found in config. Available: {', '.join(sorted(profiles))}"
        )
    defaults = profiles.get(key, {})
    extra = overrides or {}
    if "access_token" in extra:
        raise MetaAdsError(
            "Do not put access_token in the input JSON; use META_ACCESS_TOKEN_<PROFILE> or META_ACCESS_TOKEN."
        )
    prefix = re.sub(r"[^A-Z0-9]", "_", key.upper())

    token = (
        os.getenv(f"META_ACCESS_TOKEN_{prefix}")
        or os.getenv("META_ACCESS_TOKEN")
    )
    ad_account = (
        extra.get("ad_account")
        or defaults.get("ad_account")
        or os.getenv(f"META_AD_ACCOUNT_{prefix}")
        or os.getenv("META_AD_ACCOUNT")
    )
    page_id = (
        extra.get("page_id")
        or defaults.get("page_id")
        or os.getenv(f"META_PAGE_ID_{prefix}")
        or os.getenv("META_PAGE_ID")
    )
    ig_user_id = (
        extra.get("ig_user_id")
        or defaults.get("ig_user_id")
        or os.getenv(f"META_IG_USER_ID_{prefix}")
        or os.getenv("META_IG_USER_ID")
        or ""
    )
    api_version = str(
        extra.get("api_version")
        or defaults.get("api_version")
        or os.getenv("META_API_VERSION", "v25.0")
    )

    if not token:
        raise MetaAdsError(
            f"Missing token. Set META_ACCESS_TOKEN_{prefix} or META_ACCESS_TOKEN "
            "(never store tokens in the config file or input JSON)."
        )
    if not ad_account:
        raise MetaAdsError(
            "Missing ad account. Run /ads-ops:setup, set META_AD_ACCOUNT, "
            "or pass context.ad_account in the input JSON."
        )
    if not page_id:
        raise MetaAdsError(
            "Missing page id. Run /ads-ops:setup, set META_PAGE_ID, "
            "or pass context.page_id in the input JSON."
        )
    if not str(ad_account).startswith("act_"):
        ad_account = f"act_{ad_account}"

    return CompanyContext(
        company=key,
        access_token=str(token),
        ad_account=str(ad_account),
        page_id=str(page_id),
        ig_user_id=str(ig_user_id),
        api_version=api_version,
    )


def write_json_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


class MetaAdsClient:
    def __init__(
        self,
        context: CompanyContext,
        dry_run: bool = True,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        sleep_seconds: float = 0.3,
    ) -> None:
        self.context = context
        self.dry_run = dry_run
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.sleep_seconds = sleep_seconds
        self.planned_calls: list[dict[str, Any]] = []

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Reads are safe, so they run for real even in dry-run (audit and
        # auto-numbering need real data). Writes are only recorded.
        if self.dry_run and method.upper() != "GET":
            self.planned_calls.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "params": params or {},
                    "files": sorted(files) if files else [],
                }
            )
            fake_id = f"dry_{int(time.time() * 1000)}"
            return {
                "id": fake_id,
                "dry_run": True,
                "method": method,
                "path": path,
                "params": params or {},
            }

        # Token goes in the Authorization header, never in the URL or body, so
        # it can't leak through exception messages that echo the request URL.
        payload = dict(params or {})
        headers = {"Authorization": f"Bearer {self.context.access_token}"}
        url = f"{self.context.base_url}/{path.lstrip('/')}"

        last_error: str | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                is_get = method.upper() == "GET"
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    params=payload if is_get else None,
                    data=None if is_get else payload,
                    files=files,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = str(exc).replace(self.context.access_token, "***")
                # Só GET repete sozinho: um POST que deu timeout pode ter gravado.
                if is_get and attempt < self.max_retries:
                    time.sleep(attempt)
                    continue
                raise MetaAdsError(f"Network error for {path}: {last_error}") from exc

            data: dict[str, Any]
            try:
                data = response.json()
            except ValueError as exc:
                text = response.text[:400]
                raise MetaAdsError(f"Invalid JSON response for {path}: {text}") from exc

            if response.status_code < 400 and "error" not in data:
                if self.sleep_seconds:
                    time.sleep(self.sleep_seconds)
                return data

            err = data.get("error", {})
            err_message = err.get("message", response.text[:400])
            last_error = f"{response.status_code} {err_message}"
            retriable = response.status_code in {429, 500, 502, 503, 504}
            if retriable and method.upper() == "GET" and attempt < self.max_retries:
                time.sleep(attempt)
                continue
            raise MetaAdsError(f"Meta API error on {path}: {last_error}")

        raise MetaAdsError(f"Request failed on {path}: {last_error}")

    def get_campaign_adsets(self, campaign_id: str) -> list[dict[str, Any]]:
        result = self._request(
            "GET",
            f"{campaign_id}/adsets",
            params={"fields": "id,name,status", "limit": "500"},
        )
        return result.get("data", [])

    def get_next_adset_number(self, campaign_id: str) -> int:
        adsets = self.get_campaign_adsets(campaign_id)
        max_number = 0
        for adset in adsets:
            name = str(adset.get("name", ""))
            match = re.match(r"^\s*(\d+)", name)
            if not match:
                continue
            number = int(match.group(1))
            if number > max_number:
                max_number = number
        return max_number + 1

    def upload_image_from_path(self, image_path: str, name: str | None = None) -> str:
        if self.dry_run:
            safe_name = (name or Path(image_path).name or "image").replace(" ", "_")
            return f"dry_hash_{safe_name}"

        path = Path(image_path)
        if not path.exists():
            raise MetaAdsError(f"Image not found: {image_path}")

        filename = name or path.name
        with path.open("rb") as handle:
            data = self._request(
                "POST",
                f"{self.context.ad_account}/adimages",
                params={},
                files={"filename": (filename, handle, "image/png")},
            )
        images = data.get("images", {})
        if filename not in images or "hash" not in images[filename]:
            raise MetaAdsError(f"Image hash missing for {filename}")
        return str(images[filename]["hash"])

    def upload_image_from_url(self, image_url: str, name: str | None = None) -> str:
        if self.dry_run:
            safe_name = (name or Path(image_url).name or "image").replace(" ", "_")
            return f"dry_hash_{safe_name}"

        with requests.get(image_url, timeout=self.timeout_seconds) as response:
            response.raise_for_status()
            suffix = Path(image_url).suffix or ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                temp.write(response.content)
                temp_path = temp.name
        try:
            return self.upload_image_from_path(temp_path, name=name)
        finally:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    def upload_video_from_url(self, video_url: str, title: str) -> str:
        if self.dry_run:
            return f"dry_video_{title.replace(' ', '_')}"

        data = self._request(
            "POST",
            f"{self.context.ad_account}/advideos",
            params={"source": video_url, "title": title},
        )
        video_id = data.get("id")
        if not video_id:
            raise MetaAdsError("Missing video id from upload response")
        return str(video_id)

    def get_video_thumbnail(self, video_id: str) -> str:
        if self.dry_run:
            return f"https://example.com/{video_id}.jpg"

        data = self._request("GET", video_id, params={"fields": "picture"})
        thumb = data.get("picture")
        if not thumb:
            raise MetaAdsError(f"Thumbnail not found for video {video_id}")
        return str(thumb)

    def create_adset(
        self,
        campaign_id: str,
        name: str,
        daily_budget: int,
        optimization_goal: str,
        billing_event: str,
        targeting: dict[str, Any],
        promoted_object: dict[str, Any] | None = None,
        bid_strategy: str | None = None,
        status: str = "PAUSED",
    ) -> str:
        params: dict[str, Any] = {
            "campaign_id": campaign_id,
            "name": name,
            "daily_budget": str(daily_budget),
            "optimization_goal": optimization_goal,
            "billing_event": billing_event,
            "targeting": json.dumps(targeting),
            "status": status,
        }
        if bid_strategy:
            # Em CBO a estratégia fica na campanha e o ad set não pode repetir.
            params["bid_strategy"] = bid_strategy
        if promoted_object:
            params["promoted_object"] = json.dumps(promoted_object)

        data = self._request("POST", f"{self.context.ad_account}/adsets", params=params)
        adset_id = data.get("id")
        if not adset_id:
            raise MetaAdsError("Missing adset id")
        return str(adset_id)

    def create_creative_video(
        self,
        name: str,
        video_id: str,
        message: str,
        link: str,
        thumbnail_url: str,
        url_tags: str | None = None,
    ) -> str:
        story_spec = {
            "page_id": self.context.page_id,
            "video_data": {
                "video_id": video_id,
                "message": message,
                "image_url": thumbnail_url,
                "call_to_action": {"type": "LEARN_MORE", "value": {"link": link}},
            },
        }
        if self.context.ig_user_id:
            story_spec["instagram_user_id"] = self.context.ig_user_id

        params: dict[str, Any] = {
            "name": name,
            "object_story_spec": json.dumps(story_spec),
        }
        if url_tags:
            params["url_tags"] = url_tags

        data = self._request(
            "POST", f"{self.context.ad_account}/adcreatives", params=params
        )
        creative_id = data.get("id")
        if not creative_id:
            raise MetaAdsError("Missing creative id (video)")
        return str(creative_id)

    def create_creative_image_link_data(
        self,
        name: str,
        message: str,
        link: str,
        image_hash: str,
        url_tags: str | None = None,
    ) -> str:
        story_spec = {
            "page_id": self.context.page_id,
            "link_data": {
                "link": link,
                "message": message,
                "image_hash": image_hash,
                "call_to_action": {"type": "LEARN_MORE", "value": {"link": link}},
            },
        }
        if self.context.ig_user_id:
            story_spec["instagram_user_id"] = self.context.ig_user_id

        params: dict[str, Any] = {
            "name": name,
            "object_story_spec": json.dumps(story_spec),
        }
        if url_tags:
            params["url_tags"] = url_tags

        data = self._request(
            "POST", f"{self.context.ad_account}/adcreatives", params=params
        )
        creative_id = data.get("id")
        if not creative_id:
            raise MetaAdsError("Missing creative id (image)")
        return str(creative_id)

    def create_creative_asset_feed(
        self,
        name: str,
        message: str,
        link: str,
        feed_hash: str,
        stories_hash: str,
        url_tags: str | None = None,
    ) -> str:
        story_spec: dict[str, Any] = {"page_id": self.context.page_id}
        if self.context.ig_user_id:
            story_spec["instagram_user_id"] = self.context.ig_user_id

        asset_feed_spec = {
            "images": [
                {"hash": feed_hash, "adlabels": [{"name": "img_feed"}]},
                {"hash": stories_hash, "adlabels": [{"name": "img_stories"}]},
            ],
            "bodies": [{"text": message, "adlabels": [{"name": "body_default"}]}],
            "link_urls": [
                {"website_url": link, "adlabels": [{"name": "link_default"}]}
            ],
            "call_to_action_types": ["LEARN_MORE"],
            "ad_formats": ["SINGLE_IMAGE"],
            "asset_customization_rules": [
                {
                    "customization_spec": {
                        "publisher_platforms": ["facebook", "instagram"],
                        "facebook_positions": ["story", "facebook_reels"],
                        "instagram_positions": ["story", "reels"],
                    },
                    "image_label": {"name": "img_stories"},
                    "body_label": {"name": "body_default"},
                    "link_url_label": {"name": "link_default"},
                    "priority": 1,
                },
                {
                    "customization_spec": {
                        "publisher_platforms": ["facebook", "instagram"],
                        "facebook_positions": ["feed"],
                        "instagram_positions": ["stream"],
                    },
                    "image_label": {"name": "img_feed"},
                    "body_label": {"name": "body_default"},
                    "link_url_label": {"name": "link_default"},
                    "priority": 2,
                },
                {
                    # Catch-all: sem ele, os demais placements ficam a critério da Meta.
                    "customization_spec": {},
                    "image_label": {"name": "img_feed"},
                    "body_label": {"name": "body_default"},
                    "link_url_label": {"name": "link_default"},
                    "priority": 3,
                },
            ],
        }

        params: dict[str, Any] = {
            "name": name,
            "object_story_spec": json.dumps(story_spec),
            "asset_feed_spec": json.dumps(asset_feed_spec),
        }
        if url_tags:
            params["url_tags"] = url_tags

        data = self._request(
            "POST", f"{self.context.ad_account}/adcreatives", params=params
        )
        creative_id = data.get("id")
        if not creative_id:
            raise MetaAdsError("Missing creative id (asset feed)")
        return str(creative_id)

    def create_creative_from_instagram_media(
        self,
        name: str,
        source_instagram_media_id: str,
        link: str,
        object_id: str | None = None,
        url_tags: str | None = None,
        call_to_action_type: str = "LEARN_MORE",
    ) -> str:
        params: dict[str, Any] = {
            "name": name,
            "source_instagram_media_id": source_instagram_media_id,
            "object_id": object_id or self.context.page_id,
            "call_to_action": json.dumps(
                {"type": call_to_action_type, "value": {"link": link}}
            ),
        }
        if self.context.ig_user_id:
            params["instagram_user_id"] = self.context.ig_user_id
        if url_tags:
            params["url_tags"] = url_tags

        data = self._request(
            "POST", f"{self.context.ad_account}/adcreatives", params=params
        )
        creative_id = data.get("id")
        if not creative_id:
            raise MetaAdsError("Missing creative id (existing post)")
        return str(creative_id)

    def create_ad(
        self,
        name: str,
        adset_id: str,
        creative_id: str,
        status: str = "PAUSED",
        tracking_specs: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> str:
        params = {
            "name": name,
            "adset_id": adset_id,
            "creative": json.dumps({"creative_id": creative_id}),
            "status": status,
        }
        if tracking_specs:
            params["tracking_specs"] = json.dumps(tracking_specs)

        data = self._request("POST", f"{self.context.ad_account}/ads", params=params)
        ad_id = data.get("id")
        if not ad_id:
            raise MetaAdsError("Missing ad id")
        return str(ad_id)

    def update_ad_creative(self, ad_id: str, creative_id: str) -> str:
        data = self._request(
            "POST",
            ad_id,
            params={"creative": json.dumps({"creative_id": creative_id})},
        )
        if data.get("success") is False:
            raise MetaAdsError(f"Failed to update ad {ad_id}")
        return ad_id

    # --- Copy / Duplicate ------------------------------------------------
    # The Graph API exposes /{object_id}/copies endpoints that create
    # server-side clones of campaigns, adsets, and ads.  This is much faster
    # and safer than reading every field and re-posting, because Meta handles
    # internal references (pixels, audiences, creatives) automatically.

    def copy_campaign(
        self,
        campaign_id: str,
        deep_copy: bool = True,
        rename_strategy: str = "DEEP_RENAME",
        rename_prefix: str | None = None,
        rename_suffix: str | None = None,
        status_option: str = "PAUSED",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Duplicate a campaign via POST /{campaign_id}/copies.

        With deep_copy=True, all child adsets and ads are cloned too.
        Limits: max 3 adsets synchronously, 51 asynchronously.
        """
        params: dict[str, Any] = {
            "deep_copy": str(deep_copy).lower(),
            "rename_strategy": rename_strategy,
            "status_option": status_option,
        }
        if rename_prefix is not None:
            params["rename_prefix"] = rename_prefix
        if rename_suffix is not None:
            params["rename_suffix"] = rename_suffix
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        data = self._request("POST", f"{campaign_id}/copies", params=params)
        if not self.dry_run and not data.get("copied_campaign_id"):
            raise MetaAdsError(
                f"Missing copied_campaign_id for campaign {campaign_id}"
            )
        return data

    def copy_adset(
        self,
        adset_id: str,
        campaign_id: str | None = None,
        deep_copy: bool = True,
        rename_strategy: str = "DEEP_RENAME",
        rename_prefix: str | None = None,
        rename_suffix: str | None = None,
        status_option: str = "PAUSED",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Duplicate an adset via POST /{adset_id}/copies.

        Pass campaign_id to place the copy under a different campaign
        (useful for restructuring without rebuilding targeting from scratch).
        With deep_copy=True, child ads come along.
        """
        params: dict[str, Any] = {
            "deep_copy": str(deep_copy).lower(),
            "rename_strategy": rename_strategy,
            "status_option": status_option,
        }
        if campaign_id is not None:
            params["campaign_id"] = campaign_id
        if rename_prefix is not None:
            params["rename_prefix"] = rename_prefix
        if rename_suffix is not None:
            params["rename_suffix"] = rename_suffix
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        data = self._request("POST", f"{adset_id}/copies", params=params)
        if not self.dry_run and not data.get("copied_adset_id"):
            raise MetaAdsError(f"Missing copied_adset_id for adset {adset_id}")
        return data

    def copy_ad(
        self,
        ad_id: str,
        adset_id: str | None = None,
        rename_strategy: str = "NO_RENAME",
        rename_prefix: str | None = None,
        rename_suffix: str | None = None,
        status_option: str = "PAUSED",
    ) -> dict[str, Any]:
        """Duplicate an ad via POST /{ad_id}/copies.

        Pass adset_id to place the copy under a different adset.
        Ads don't have deep_copy since they have no children.
        """
        params: dict[str, Any] = {
            "rename_strategy": rename_strategy,
            "status_option": status_option,
        }
        if adset_id is not None:
            params["adset_id"] = adset_id
        if rename_prefix is not None:
            params["rename_prefix"] = rename_prefix
        if rename_suffix is not None:
            params["rename_suffix"] = rename_suffix

        data = self._request("POST", f"{ad_id}/copies", params=params)
        if not self.dry_run and not data.get("copied_ad_id"):
            raise MetaAdsError(f"Missing copied_ad_id for ad {ad_id}")
        return data
