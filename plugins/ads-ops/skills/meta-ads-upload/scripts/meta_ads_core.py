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


# What /{id}/copies takes for each level. Only campaigns and adsets have children,
# so only they take deep_copy and a schedule; adsets and ads can move under a new parent.
COPY_LEVELS: dict[str, dict[str, Any]] = {
    "campaigns": {"result": "copied_campaign_id", "parent": None, "children": True},
    "adsets": {"result": "copied_adset_id", "parent": "campaign_id", "children": True},
    "ads": {"result": "copied_ad_id", "parent": "adset_id", "children": False},
}
COPY_DEFAULTS = {"deep_copy": True, "rename_strategy": "DEEP_RENAME", "status_option": "PAUSED"}


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
        # Token goes in the Authorization header, never in the URL or body, so
        # it can't leak through exception messages that echo the request URL.
        payload = dict(params or {})
        headers = {"Authorization": f"Bearer {self.context.access_token}"}
        url = f"{self.context.base_url}/{path.lstrip('/')}"
        is_get = method == "GET"

        last_error: str | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.request(
                    method=method,
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

            try:
                data: dict[str, Any] = response.json()
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
            if retriable and is_get and attempt < self.max_retries:
                time.sleep(attempt)
                continue
            raise MetaAdsError(f"Meta API error on {path}: {last_error}")

        raise MetaAdsError(f"Request failed on {path}: {last_error}")

    def _read(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """GET. Reads are safe, so they run for real even in dry-run (audit and
        auto-numbering need real data)."""
        return self._request("GET", path, params)

    def _write(
        self,
        path: str,
        params: dict[str, Any],
        id_key: str | None = "id",
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST. In dry-run it is only recorded and answers with a fake id under id_key.
        For real, the response must carry id_key (None: no id expected)."""
        if self.dry_run:
            self.planned_calls.append(
                {"method": "POST", "path": path, "params": params, "files": sorted(files or [])}
            )
            return {id_key or "id": f"dry_{int(time.time() * 1000)}", "dry_run": True}
        data = self._request("POST", path, params, files)
        if id_key and not data.get(id_key):
            raise MetaAdsError(f"Missing {id_key} in the response of {path}")
        return data

    def get_campaign_adsets(self, campaign_id: str) -> list[dict[str, Any]]:
        result = self._read(f"{campaign_id}/adsets", {"fields": "id,name,status", "limit": "500"})
        return result.get("data", [])

    def get_next_adset_number(self, campaign_id: str) -> int:
        numbers = [
            int(match.group(1))
            for adset in self.get_campaign_adsets(campaign_id)
            if (match := re.match(r"^\s*(\d+)", str(adset.get("name", ""))))
        ]
        return max(numbers, default=0) + 1

    def upload_image_from_path(self, image_path: str, name: str | None = None) -> str:
        if self.dry_run:
            safe_name = (name or Path(image_path).name or "image").replace(" ", "_")
            return f"dry_hash_{safe_name}"

        path = Path(image_path)
        if not path.exists():
            raise MetaAdsError(f"Image not found: {image_path}")

        filename = name or path.name
        with path.open("rb") as handle:
            data = self._write(
                f"{self.context.ad_account}/adimages",
                {},
                id_key="images",
                files={"filename": (filename, handle, "image/png")},
            )
        image = data["images"].get(filename, {})
        if "hash" not in image:
            raise MetaAdsError(f"Image hash missing for {filename}")
        return str(image["hash"])

    def upload_image_from_url(self, image_url: str, name: str | None = None) -> str:
        if self.dry_run:
            safe_name = (name or Path(image_url).name or "image").replace(" ", "_")
            return f"dry_hash_{safe_name}"

        with requests.get(image_url, timeout=self.timeout_seconds) as response:
            response.raise_for_status()
            suffix = Path(image_url).suffix or ".png"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                temp.write(response.content)
                temp_path = Path(temp.name)
        try:
            return self.upload_image_from_path(str(temp_path), name=name)
        finally:
            temp_path.unlink(missing_ok=True)

    def upload_video_from_url(self, video_url: str, title: str) -> str:
        if self.dry_run:
            return f"dry_video_{title.replace(' ', '_')}"
        data = self._write(
            f"{self.context.ad_account}/advideos", {"source": video_url, "title": title}
        )
        return str(data["id"])

    def get_video_thumbnail(self, video_id: str) -> str:
        if self.dry_run:
            return f"https://example.com/{video_id}.jpg"

        thumb = self._read(video_id, {"fields": "picture"}).get("picture")
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
        return str(self._write(f"{self.context.ad_account}/adsets", params)["id"])

    def _create_creative(
        self, name: str, url_tags: str | None, story_spec: dict[str, Any] | None = None, **params: Any
    ) -> str:
        """POST /adcreatives. With story_spec, page and Instagram account go inside it;
        without, the Instagram account goes at the top level."""
        params["name"] = name
        if story_spec is not None:
            story_spec = {"page_id": self.context.page_id, **story_spec}
            if self.context.ig_user_id:
                story_spec["instagram_user_id"] = self.context.ig_user_id
            params["object_story_spec"] = json.dumps(story_spec)
        elif self.context.ig_user_id:
            params["instagram_user_id"] = self.context.ig_user_id
        if url_tags:
            params["url_tags"] = url_tags
        return str(self._write(f"{self.context.ad_account}/adcreatives", params)["id"])

    def create_creative_video(
        self,
        name: str,
        video_id: str,
        message: str,
        link: str,
        thumbnail_url: str,
        url_tags: str | None = None,
    ) -> str:
        video_data = {
            "video_id": video_id,
            "message": message,
            "image_url": thumbnail_url,
            "call_to_action": {"type": "LEARN_MORE", "value": {"link": link}},
        }
        return self._create_creative(name, url_tags, {"video_data": video_data})

    def create_creative_image_link_data(
        self,
        name: str,
        message: str,
        link: str,
        image_hash: str,
        url_tags: str | None = None,
    ) -> str:
        link_data = {
            "link": link,
            "message": message,
            "image_hash": image_hash,
            "call_to_action": {"type": "LEARN_MORE", "value": {"link": link}},
        }
        return self._create_creative(name, url_tags, {"link_data": link_data})

    def create_creative_asset_feed(
        self,
        name: str,
        message: str,
        link: str,
        feed_hash: str,
        stories_hash: str,
        url_tags: str | None = None,
    ) -> str:
        def rule(image: str, priority: int, spec: dict[str, Any]) -> dict[str, Any]:
            return {
                "customization_spec": spec,
                "image_label": {"name": image},
                "body_label": {"name": "body_default"},
                "link_url_label": {"name": "link_default"},
                "priority": priority,
            }

        both = ["facebook", "instagram"]
        asset_feed_spec = {
            "images": [
                {"hash": feed_hash, "adlabels": [{"name": "img_feed"}]},
                {"hash": stories_hash, "adlabels": [{"name": "img_stories"}]},
            ],
            "bodies": [{"text": message, "adlabels": [{"name": "body_default"}]}],
            "link_urls": [{"website_url": link, "adlabels": [{"name": "link_default"}]}],
            "call_to_action_types": ["LEARN_MORE"],
            "ad_formats": ["SINGLE_IMAGE"],
            "asset_customization_rules": [
                rule("img_stories", 1, {
                    "publisher_platforms": both,
                    "facebook_positions": ["story", "facebook_reels"],
                    "instagram_positions": ["story", "reels"],
                }),
                rule("img_feed", 2, {
                    "publisher_platforms": both,
                    "facebook_positions": ["feed"],
                    "instagram_positions": ["stream"],
                }),
                # Catch-all: sem ele, os demais placements ficam a critério da Meta.
                rule("img_feed", 3, {}),
            ],
        }
        return self._create_creative(
            name, url_tags, {}, asset_feed_spec=json.dumps(asset_feed_spec)
        )

    def create_creative_from_instagram_media(
        self,
        name: str,
        source_instagram_media_id: str,
        link: str,
        object_id: str | None = None,
        url_tags: str | None = None,
        call_to_action_type: str = "LEARN_MORE",
    ) -> str:
        return self._create_creative(
            name,
            url_tags,
            source_instagram_media_id=source_instagram_media_id,
            object_id=object_id or self.context.page_id,
            call_to_action=json.dumps({"type": call_to_action_type, "value": {"link": link}}),
        )

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
        return str(self._write(f"{self.context.ad_account}/ads", params)["id"])

    def update_ad_creative(self, ad_id: str, creative_id: str) -> str:
        data = self._write(
            ad_id, {"creative": json.dumps({"creative_id": creative_id})}, id_key=None
        )
        if data.get("success") is False:
            raise MetaAdsError(f"Failed to update ad {ad_id}")
        return ad_id

    def copy(self, level: str, source_id: str, options: dict[str, Any]) -> dict[str, Any]:
        """Server-side clone via POST /{source_id}/copies (Meta keeps pixels, audiences
        and creatives wired). level is a COPY_LEVELS key; options may carry
        rename_strategy/prefix/suffix, status_option, the parent id and, for levels with
        children, deep_copy, start_time and end_time. Missing ones use COPY_DEFAULTS.
        Limits: deep copy of a campaign clones at most 3 adsets synchronously, 51 async.
        """
        spec = COPY_LEVELS[level]
        keys = ["rename_strategy", "rename_prefix", "rename_suffix", "status_option"]
        if spec["parent"]:
            keys.append(spec["parent"])
        if spec["children"]:
            keys += ["deep_copy", "start_time", "end_time"]
        merged = {**COPY_DEFAULTS, **{k: v for k, v in options.items() if v is not None}}
        params = {k: str(merged[k]) for k in keys if merged.get(k) is not None}
        if "deep_copy" in params:
            params["deep_copy"] = str(bool(merged["deep_copy"])).lower()
        return self._write(f"{source_id}/copies", params, id_key=spec["result"])
