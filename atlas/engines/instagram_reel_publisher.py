"""公開済みの7秒動画をInstagramリールとして自動投稿する。"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from engines.instagram_publisher import (
    INSTAGRAM_API_BASE,
    SOCIAL_PUBLISH_ROUTES_FILE,
    get_instagram_credentials,
    load_json,
    publish_media_container,
    save_json,
)


BASE_DIR = Path(__file__).resolve().parents[1]
SITE_URL = "https://www.alsivo.com"
REEL_THUMB_OFFSET_MS = 3500
HISTORY_FILE = BASE_DIR / "data" / "social" / "instagram_reel_history.json"
REEL_DIR = BASE_DIR.parent / "public" / "images" / "social"


def reel_url(slug: str) -> str:
    return f"{SITE_URL}/images/social/{slug}-instagram-reel.mp4"


def load_candidates(article_slug: str = "") -> list[dict[str, Any]]:
    data = load_json(SOCIAL_PUBLISH_ROUTES_FILE)
    routes = data.get("routes", [])
    if not isinstance(routes, list):
        return []
    history = load_json(HISTORY_FILE).get("items", [])
    published_slugs = {
        str(item.get("article_slug", "")).strip()
        for item in history
        if isinstance(item, dict) and item.get("status") == "published"
    }
    candidates = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        slug = str(route.get("article_slug", "")).strip()
        if not slug or slug in published_slugs:
            continue
        if not (REEL_DIR / f"{slug}-instagram-reel.mp4").is_file():
            continue
        if article_slug and slug != article_slug:
            continue
        if str(route.get("platform", "")).strip() != "instagram":
            continue
        if str(route.get("route_status", "")).strip() not in {"ready", "published"}:
            continue
        if not str(route.get("post_text", "")).strip():
            continue
        candidates.append(route)
    return candidates


def validate_public_video(url: str) -> None:
    try:
        response = requests.get(url, timeout=30, stream=True)
    except requests.RequestException as error:
        raise RuntimeError(f"リール動画URLへアクセスできません: {error}") from error
    if response.status_code != 200:
        raise RuntimeError(f"リール動画が公開されていません: HTTP {response.status_code}")
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("video/"):
        raise RuntimeError(f"公開URLが動画ではありません: {content_type}")


def create_reel_container(
    user_id: str,
    access_token: str,
    video_url: str,
    caption: str,
) -> str:
    response = requests.post(
        f"{INSTAGRAM_API_BASE}/{user_id}/media",
        data={
            "media_type": "REELS", "video_url": video_url,
            "caption": caption, "share_to_feed": "false",
            "thumb_offset": str(REEL_THUMB_OFFSET_MS),
            "access_token": access_token,
        },
        timeout=30,
    )
    if response.status_code not in {200, 201}:
        raise RuntimeError(
            "Reel Container作成に失敗しました: "
            f"HTTP {response.status_code} / {response.text}"
        )
    container_id = str(response.json().get("id", "")).strip()
    if not container_id:
        raise RuntimeError("Reel Container IDを取得できませんでした。")
    return container_id


def wait_until_ready(container_id: str, access_token: str) -> None:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        response = requests.get(
            f"{INSTAGRAM_API_BASE}/{container_id}",
            params={"fields": "status_code,status", "access_token": access_token},
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(
                "リール処理状態を取得できません: "
                f"HTTP {response.status_code} / {response.text}"
            )
        data = response.json()
        status = str(data.get("status_code", "")).upper()
        if status == "FINISHED":
            return
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Instagram側のリール処理に失敗しました: {data}")
        time.sleep(5)
    raise RuntimeError("Instagram側のリール処理が時間内に完了しませんでした。")


def record_published(slug: str, media_id: str, container_id: str) -> None:
    data = load_json(HISTORY_FILE)
    items = data.get("items", [])
    if not isinstance(items, list):
        items = []
    items.append({
        "article_slug": slug, "status": "published",
        "external_post_id": media_id, "container_id": container_id,
        "published_at": datetime.now().isoformat(),
    })
    data["items"] = items
    data["total"] = len(items)
    save_json(HISTORY_FILE, data)


def publish_reel(route: dict[str, Any]) -> str:
    slug = str(route.get("article_slug", "")).strip()
    caption = str(route.get("post_text", "")).strip()
    url = reel_url(slug)
    validate_public_video(url)
    credentials = get_instagram_credentials()
    container_id = create_reel_container(
        credentials["user_id"], credentials["access_token"], url, caption,
    )
    wait_until_ready(container_id, credentials["access_token"])
    success, media_id, error = publish_media_container(
        credentials["user_id"], credentials["access_token"], container_id,
    )
    if not success:
        raise RuntimeError(error)
    record_published(slug, media_id, container_id)
    return media_id


def main(apply_mode: bool = False, article_slug: str = "") -> None:
    candidates = load_candidates(article_slug)
    print("\n===== Atlas Instagram Reel Publisher =====\n")
    print(f"Mode: {'APPLY' if apply_mode else 'DRY RUN'}")
    print(f"Ready: {len(candidates)}")
    if not candidates:
        print("投稿可能なInstagram Reelはありません。")
        return
    route = candidates[0]
    slug = str(route.get("article_slug", "")).strip()
    if not apply_mode:
        print(f"DRY RUN: {reel_url(slug)}")
        return
    media_id = publish_reel(route)
    print(f"Instagramリールへの投稿が完了しました。 Media ID: {media_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ALSIVO Instagram Reel Publisher")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--article-slug", default="")
    args = parser.parse_args()
    main(args.apply, args.article_slug.strip())
