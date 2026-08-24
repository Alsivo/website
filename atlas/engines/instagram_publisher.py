import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]

SOCIAL_PUBLISH_ROUTES_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_publish_routes.json"
)

SOCIAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_queue.json"
)

SOCIAL_APPROVAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_approval_queue.json"
)

SITE_URL = "https://www.alsivo.com"

INSTAGRAM_API_BASE = (
    "https://graph.instagram.com/v24.0"
)


# =========================================================
# Environment
# =========================================================

load_dotenv(
    BASE_DIR / ".env"
)


def get_instagram_credentials() -> dict[str, str]:
    """Instagram API認証情報を取得する。"""

    credentials = {
        "access_token":
            os.getenv(
                "INSTAGRAM_ACCESS_TOKEN",
                "",
            ).strip(),

        "user_id":
            os.getenv(
                "INSTAGRAM_USER_ID",
                "",
            ).strip(),
    }

    missing = [
        key
        for key, value
        in credentials.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Instagram API認証情報が"
            "不足しています："
            + ", ".join(missing)
        )

    return credentials


# =========================================================
# JSON
# =========================================================

def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def save_json(
    filepath: Path,
    data: dict[str, Any],
) -> None:
    """JSONをUTF-8で保存する。"""

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    filepath.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


# =========================================================
# Route
# =========================================================

def load_ready_instagram_routes(
    article_slug: str = "",
) -> list[dict[str, Any]]:
    """Instagram用Ready Routeを取得する。"""

    data = load_json(
        SOCIAL_PUBLISH_ROUTES_FILE
    )

    routes = data.get(
        "routes",
        [],
    )

    if not isinstance(
        routes,
        list,
    ):
        return []

    ready_routes: list[
        dict[str, Any]
    ] = []

    for item in routes:

        if not isinstance(
            item,
            dict,
        ):
            continue

        if article_slug and str(item.get("article_slug", "")).strip() != article_slug:
            continue

        platform = str(
            item.get(
                "platform",
                "",
            )
        ).strip()

        route_status = str(
            item.get(
                "route_status",
                "",
            )
        ).strip()

        publisher = str(
            item.get(
                "publisher",
                "",
            )
        ).strip()

        post_text = str(
            item.get(
                "post_text",
                "",
            )
        ).strip()

        if platform != "instagram":
            continue

        if route_status != "ready":
            continue

        if (
            publisher
            != "instagram_publisher"
        ):
            continue

        if not post_text:
            continue

        ready_routes.append(
            item
        )

    return ready_routes


def build_image_url(
    route: dict[str, Any],
) -> str:
    """記事slugから公開Instagram画像URLを作る。"""

    slug = str(
        route.get(
            "article_slug",
            "",
        )
    ).strip()

    if not slug:
        return ""

    return (
        f"{SITE_URL}"
        f"/images/social/"
        f"{slug}-instagram.png"
    )


# =========================================================
# Validation
# =========================================================

def validate_route(
    route: dict[str, Any],
) -> tuple[
    bool,
    str,
    str,
]:
    """投稿内容を検証する。"""

    post_text = str(
        route.get(
            "post_text",
            "",
        )
    ).strip()

    if not post_text:
        return (
            False,
            "投稿文が空です。",
            "",
        )

    image_url = (
        build_image_url(
            route
        )
    )

    if not image_url:
        return (
            False,
            "Instagram画像URLを作成できません。",
            "",
        )

    # Metaから画像を取得できるか確認する
    try:
        response = requests.get(
            image_url,
            timeout=30,
        )

    except requests.RequestException as error:
        return (
            False,
            (
                "Instagram画像URLへ"
                "アクセスできません："
                f"{error}"
            ),
            image_url,
        )

    if response.status_code != 200:
        return (
            False,
            (
                "Instagram画像が"
                "公開されていません："
                f"HTTP {response.status_code}"
            ),
            image_url,
        )

    content_type = (
        response.headers.get(
            "Content-Type",
            "",
        )
    )

    if not content_type.startswith(
        "image/"
    ):
        return (
            False,
            (
                "公開URLが画像ではありません："
                f"{content_type}"
            ),
            image_url,
        )

    return (
        True,
        "",
        image_url,
    )


# =========================================================
# Dry run
# =========================================================

def dry_run_publish(
    route: dict[str, Any],
) -> dict[str, Any]:
    """投稿せず内容だけ確認する。"""

    valid, reason, image_url = (
        validate_route(
            route
        )
    )

    if not valid:
        return {
            "status": "blocked",
            "posted": False,
            "media_id": "",
            "container_id": "",
            "image_url": image_url,
            "reason": reason,
        }

    return {
        "status": "dry_run",
        "posted": False,
        "media_id": "",
        "container_id": "",
        "image_url": image_url,
        "reason":
            "DRY RUNのためInstagramには"
            "投稿していません。",
    }


# =========================================================
# Real publish
# =========================================================

def create_media_container(
    user_id: str,
    access_token: str,
    image_url: str,
    caption: str,
) -> tuple[
    bool,
    str,
    str,
]:
    """画像投稿用Media Containerを作る。"""

    endpoint = (
        f"{INSTAGRAM_API_BASE}"
        f"/{user_id}/media"
    )

    try:
        response = requests.post(
            endpoint,
            data={
                "image_url":
                    image_url,
                "caption":
                    caption,
                "access_token":
                    access_token,
            },
            timeout=30,
        )

    except requests.RequestException as error:
        return (
            False,
            "",
            (
                "Media Container作成時の"
                "通信に失敗しました："
                f"{error}"
            ),
        )

    if response.status_code not in {
        200,
        201,
    }:
        return (
            False,
            "",
            (
                "Media Container作成に"
                "失敗しました："
                f"HTTP {response.status_code} / "
                f"{response.text}"
            ),
        )

    try:
        data = response.json()

    except ValueError:
        return (
            False,
            "",
            "Media Containerレスポンスの"
            "JSON解析に失敗しました。",
        )

    container_id = str(
        data.get(
            "id",
            "",
        )
    ).strip()

    if not container_id:
        return (
            False,
            "",
            "Media Container IDを"
            "取得できませんでした。",
        )

    return (
        True,
        container_id,
        "",
    )


def publish_media_container(
    user_id: str,
    access_token: str,
    container_id: str,
) -> tuple[
    bool,
    str,
    str,
]:
    """作成済みMedia Containerを公開する。"""

    endpoint = (
        f"{INSTAGRAM_API_BASE}"
        f"/{user_id}/media_publish"
    )

    try:
        response = requests.post(
            endpoint,
            data={
                "creation_id":
                    container_id,
                "access_token":
                    access_token,
            },
            timeout=30,
        )

    except requests.RequestException as error:
        return (
            False,
            "",
            (
                "Instagram Publish時の"
                "通信に失敗しました："
                f"{error}"
            ),
        )

    if response.status_code not in {
        200,
        201,
    }:
        return (
            False,
            "",
            (
                "Instagram Publishに"
                "失敗しました："
                f"HTTP {response.status_code} / "
                f"{response.text}"
            ),
        )

    try:
        data = response.json()

    except ValueError:
        return (
            False,
            "",
            "Instagram Publishレスポンスの"
            "JSON解析に失敗しました。",
        )

    media_id = str(
        data.get(
            "id",
            "",
        )
    ).strip()

    if not media_id:
        return (
            False,
            "",
            "公開後Media IDを"
            "取得できませんでした。",
        )

    return (
        True,
        media_id,
        "",
    )


def wait_until_media_ready(
    container_id: str,
    access_token: str,
    timeout_seconds: int = 180,
) -> tuple[bool, str]:
    """Instagram側で画像コンテナの処理が終わるまで待つ。"""

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = requests.get(
                f"{INSTAGRAM_API_BASE}/{container_id}",
                params={
                    "fields": "status_code,status",
                    "access_token": access_token,
                },
                timeout=30,
            )
        except requests.RequestException as error:
            return False, f"Instagram画像の処理状態を確認できません：{error}"

        if response.status_code != 200:
            return (
                False,
                "Instagram画像の処理状態を確認できません："
                f"HTTP {response.status_code} / {response.text}",
            )

        data = response.json()
        status = str(data.get("status_code", "")).upper()
        if status == "FINISHED":
            return True, ""
        if status in {"ERROR", "EXPIRED"}:
            return False, f"Instagram側の画像処理に失敗しました：{data}"
        time.sleep(3)

    return False, "Instagram側の画像処理が時間内に完了しませんでした。"


def publish_to_instagram(
    route: dict[str, Any],
) -> dict[str, Any]:
    """Instagramへ画像投稿する。"""

    valid, reason, image_url = (
        validate_route(
            route
        )
    )

    if not valid:
        return {
            "status": "blocked",
            "posted": False,
            "media_id": "",
            "container_id": "",
            "image_url": image_url,
            "reason": reason,
        }

    credentials = (
        get_instagram_credentials()
    )

    post_text = str(
        route.get(
            "post_text",
            "",
        )
    ).strip()

    success, container_id, error = (
        create_media_container(
            user_id=credentials[
                "user_id"
            ],
            access_token=credentials[
                "access_token"
            ],
            image_url=image_url,
            caption=post_text,
        )
    )

    if not success:
        return {
            "status": "error",
            "posted": False,
            "media_id": "",
            "container_id": "",
            "image_url": image_url,
            "reason": error,
        }

    ready, error = wait_until_media_ready(
        container_id=container_id,
        access_token=credentials["access_token"],
    )
    if not ready:
        return {
            "status": "error",
            "posted": False,
            "media_id": "",
            "container_id": container_id,
            "image_url": image_url,
            "reason": error,
        }

    success, media_id, error = (
        publish_media_container(
            user_id=credentials[
                "user_id"
            ],
            access_token=credentials[
                "access_token"
            ],
            container_id=container_id,
        )
    )

    if not success:
        return {
            "status": "error",
            "posted": False,
            "media_id": "",
            "container_id":
                container_id,
            "image_url": image_url,
            "reason": error,
        }

    return {
        "status": "published",
        "posted": True,
        "media_id": media_id,
        "container_id":
            container_id,
        "image_url": image_url,
        "reason":
            "Instagramへの投稿が"
            "完了しました。",
    }


# =========================================================
# State update
# =========================================================

def mark_route_published(
    route: dict[str, Any],
    media_id: str,
) -> None:
    """投稿成功後に各JSONをpublishedへ更新する。"""

    approval_id = str(
        route.get(
            "approval_id",
            "",
        )
    ).strip()

    article_slug = str(
        route.get(
            "article_slug",
            "",
        )
    ).strip()

    published_at = (
        datetime.now().isoformat()
    )

    # -----------------------------------------------------
    # social_queue.json
    # -----------------------------------------------------

    queue_data = load_json(
        SOCIAL_QUEUE_FILE
    )

    queue = queue_data.get(
        "queue",
        [],
    )

    if isinstance(
        queue,
        list,
    ):
        for item in queue:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                str(
                    item.get(
                        "platform",
                        "",
                    )
                ).strip()
                != "instagram"
            ):
                continue

            if (
                str(
                    item.get(
                        "article_slug",
                        "",
                    )
                ).strip()
                != article_slug
            ):
                continue

            item["status"] = "published"
            item["published"] = True
            item["published_at"] = (
                published_at
            )
            item["external_post_id"] = (
                media_id
            )
            item["error"] = ""
            item["updated_at"] = (
                published_at
            )

        queue_data["updated_at"] = (
            published_at
        )

        queue_data["pending"] = sum(
            1
            for item in queue
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "status"
            )
            == "pending"
        )

        queue_data["approved"] = sum(
            1
            for item in queue
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "status"
            )
            == "approved"
        )

        queue_data["published"] = sum(
            1
            for item in queue
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "status"
            )
            == "published"
        )

        queue_data["total"] = len(
            queue
        )

        save_json(
            SOCIAL_QUEUE_FILE,
            queue_data,
        )

    # -----------------------------------------------------
    # social_approval_queue.json
    # -----------------------------------------------------

    approval_data = load_json(
        SOCIAL_APPROVAL_QUEUE_FILE
    )

    approval_queue = (
        approval_data.get(
            "queue",
            [],
        )
    )

    if isinstance(
        approval_queue,
        list,
    ):
        for item in approval_queue:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                str(
                    item.get(
                        "approval_id",
                        "",
                    )
                ).strip()
                != approval_id
            ):
                continue

            item["status"] = "published"
            item["published"] = True
            item["published_at"] = (
                published_at
            )
            item["external_post_id"] = (
                media_id
            )
            item["updated_at"] = (
                published_at
            )

        approval_data["updated_at"] = (
            published_at
        )

        save_json(
            SOCIAL_APPROVAL_QUEUE_FILE,
            approval_data,
        )

    # -----------------------------------------------------
    # social_publish_routes.json
    # -----------------------------------------------------

    routes_data = load_json(
        SOCIAL_PUBLISH_ROUTES_FILE
    )

    routes = routes_data.get(
        "routes",
        [],
    )

    if isinstance(
        routes,
        list,
    ):
        for item in routes:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                str(
                    item.get(
                        "approval_id",
                        "",
                    )
                ).strip()
                != approval_id
            ):
                continue

            item["route_status"] = (
                "published"
            )

            item["published_at"] = (
                published_at
            )

            item["external_post_id"] = (
                media_id
            )

            item["reason"] = (
                "Instagramへの投稿が"
                "完了しました。"
            )

        routes_data["generated_at"] = (
            published_at
        )

        routes_data["ready"] = sum(
            1
            for item in routes
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "route_status"
            )
            == "ready"
        )

        routes_data["blocked"] = sum(
            1
            for item in routes
            if isinstance(
                item,
                dict,
            )
            and item.get(
                "route_status"
            )
            == "blocked"
        )

        routes_data["total"] = len(
            routes
        )

        save_json(
            SOCIAL_PUBLISH_ROUTES_FILE,
            routes_data,
        )


# =========================================================
# Console
# =========================================================

def print_route(
    index: int,
    route: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """投稿予定内容・結果を表示する。"""

    print(
        "--------------------------------"
    )

    print(
        f"[{index}]"
    )

    print(
        "Approval ID："
        f"{route.get('approval_id', '')}"
    )

    print(
        "Article："
        f"{route.get('article_slug', '')}"
    )

    print(
        "Status："
        f"{result.get('status', '')}"
    )

    print()

    print(
        "Image："
        f"{result.get('image_url', '')}"
    )

    print()

    print(
        "--- CAPTION ---"
    )

    print(
        str(
            route.get(
                "post_text",
                "",
            )
        )
    )

    print()

    container_id = str(
        result.get(
            "container_id",
            "",
        )
    ).strip()

    if container_id:
        print(
            "Container ID："
            f"{container_id}"
        )

    media_id = str(
        result.get(
            "media_id",
            "",
        )
    ).strip()

    if media_id:
        print(
            "Media ID："
            f"{media_id}"
        )

    print(
        "Result："
        f"{result.get('reason', '')}"
    )

    print()


# =========================================================
# Main
# =========================================================

def main(
    apply_mode: bool = False,
    article_slug: str = "",
) -> None:
    """Instagram Publisherを実行する。"""

    routes = (
        load_ready_instagram_routes(article_slug)
    )

    print(
        "\n===== Atlas Instagram Publisher =====\n"
    )

    print(
        "Mode："
        + (
            "APPLY"
            if apply_mode
            else "DRY RUN"
        )
    )

    print(
        "Ready："
        f"{len(routes)}"
    )

    print()

    if not routes:
        print(
            "投稿可能なInstagram Routeは"
            "ありません。"
        )
        return

    if apply_mode:
        get_instagram_credentials()

    for index, route in enumerate(
        routes,
        start=1,
    ):

        if apply_mode:
            result = (
                publish_to_instagram(
                    route
                )
            )

        else:
            result = (
                dry_run_publish(
                    route
                )
            )

        print_route(
            index,
            route,
            result,
        )

        if (
            apply_mode
            and result.get(
                "posted"
            )
            is True
        ):
            media_id = str(
                result.get(
                    "media_id",
                    "",
                )
            ).strip()

            if media_id:
                mark_route_published(
                    route,
                    media_id,
                )

                print(
                    "[Instagram Publisher] "
                    "投稿状態をpublishedへ"
                    "更新しました。"
                )

        # 安全のため実投稿時は
        # 1回につき1件のみ
        if apply_mode:
            break


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Atlas Instagram Publisher"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Instagramへ実際に投稿します。"
            "指定しない場合はDRY RUNです。"
        ),
    )

    parser.add_argument("--article-slug", default="")

    args = parser.parse_args()

    main(
        apply_mode=args.apply,
        article_slug=args.article_slug,
    )
