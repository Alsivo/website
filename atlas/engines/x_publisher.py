import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1


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

X_CREATE_POST_URL = (
    "https://api.x.com/2/tweets"
)


# =========================================================
# Environment
# =========================================================

load_dotenv(
    BASE_DIR / ".env"
)


def get_x_credentials() -> dict[str, str]:
    """X API認証情報を.envから取得する。"""

    credentials = {
        "api_key":
            os.getenv(
                "X_API_KEY",
                "",
            ).strip(),

        "api_key_secret":
            os.getenv(
                "X_API_KEY_SECRET",
                "",
            ).strip(),

        "access_token":
            os.getenv(
                "X_ACCESS_TOKEN",
                "",
            ).strip(),

        "access_token_secret":
            os.getenv(
                "X_ACCESS_TOKEN_SECRET",
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
            "X API認証情報が不足しています："
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


# =========================================================
# Route
# =========================================================

def load_ready_x_routes(
    article_slug: str = "",
) -> list[dict[str, Any]]:
    """X Publisherで処理可能なRouteだけ取得する。"""

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

        if platform != "x":
            continue

        if route_status != "ready":
            continue

        if publisher != "x_publisher":
            continue

        if not post_text:
            continue

        ready_routes.append(
            item
        )

    return ready_routes


# =========================================================
# Validation
# =========================================================

def validate_post_text(
    post_text: str,
) -> tuple[
    bool,
    str,
]:
    """X投稿文を最低限検証する。"""

    text = post_text.strip()

    if not text:
        return (
            False,
            "投稿文が空です。",
        )

    # 厳密なXのweighted length計算ではない。
    # 明らかな異常値のみここで止める。
    if len(text) > 500:
        return (
            False,
            (
                "投稿文が長すぎる可能性があります。"
                f" len={len(text)}"
            ),
        )

    return (
        True,
        "",
    )


# =========================================================
# Dry run
# =========================================================

def dry_run_publish(
    route: dict[str, Any],
) -> dict[str, Any]:
    """X投稿を実行せず内容だけ確認する。"""

    post_text = str(
        route.get(
            "post_text",
            "",
        )
    ).strip()

    valid, reason = (
        validate_post_text(
            post_text
        )
    )

    if not valid:
        return {
            "status": "blocked",
            "posted": False,
            "post_id": "",
            "reason": reason,
        }

    return {
        "status": "dry_run",
        "posted": False,
        "post_id": "",
        "reason":
            "DRY RUNのためXには投稿していません。",
    }



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


def mark_route_published(
    route: dict[str, Any],
    post_id: str,
) -> None:
    """
    X投稿成功後に、

    ・social_queue
    ・social_approval_queue
    ・social_publish_routes

    をpublished状態へ更新する。
    """

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
                != "x"
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
            item["published_at"] = published_at
            item["external_post_id"] = post_id
            item["error"] = ""
            item["updated_at"] = published_at

        queue_data["updated_at"] = (
            published_at
        )

        queue_data["pending"] = sum(
            1
            for item in queue
            if isinstance(item, dict)
            and item.get("status")
            == "pending"
        )

        queue_data["approved"] = sum(
            1
            for item in queue
            if isinstance(item, dict)
            and item.get("status")
            == "approved"
        )

        queue_data["published"] = sum(
            1
            for item in queue
            if isinstance(item, dict)
            and item.get("status")
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
                post_id
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
                post_id
            )

            item["reason"] = (
                "Xへの投稿が完了しました。"
            )

        routes_data["generated_at"] = (
            published_at
        )

        routes_data["ready"] = sum(
            1
            for item in routes
            if isinstance(item, dict)
            and item.get(
                "route_status"
            )
            == "ready"
        )

        routes_data["blocked"] = sum(
            1
            for item in routes
            if isinstance(item, dict)
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
# Real publish
# =========================================================

def publish_to_x(
    route: dict[str, Any],
) -> dict[str, Any]:
    """X API v2へ実際に投稿する。"""

    post_text = str(
        route.get(
            "post_text",
            "",
        )
    ).strip()

    valid, reason = (
        validate_post_text(
            post_text
        )
    )

    if not valid:
        return {
            "status": "blocked",
            "posted": False,
            "post_id": "",
            "reason": reason,
        }

    article_url = str(route.get("article_url", "")).strip()
    if not article_url:
        return {
            "status": "blocked",
            "posted": False,
            "post_id": "",
            "reason": "記事URLがないためXへ投稿しません。",
        }
    try:
        article_response = requests.get(article_url, timeout=20)
    except requests.RequestException as error:
        return {
            "status": "blocked",
            "posted": False,
            "post_id": "",
            "reason": f"記事の公開確認に失敗したためXへ投稿しません：{error}",
        }
    if article_response.status_code != 200:
        return {
            "status": "blocked",
            "posted": False,
            "post_id": "",
            "reason": f"記事が公開されていないためXへ投稿しません：HTTP {article_response.status_code}",
        }

    credentials = (
        get_x_credentials()
    )

    auth = OAuth1(
        credentials[
            "api_key"
        ],
        credentials[
            "api_key_secret"
        ],
        credentials[
            "access_token"
        ],
        credentials[
            "access_token_secret"
        ],
    )

    try:
        response = requests.post(
            X_CREATE_POST_URL,
            auth=auth,
            json={
                "text":
                    post_text,
            },
            timeout=30,
        )

    except requests.RequestException as error:
        return {
            "status": "error",
            "posted": False,
            "post_id": "",
            "reason":
                "X API通信に失敗しました："
                f"{error}",
        }

    if response.status_code not in {
        200,
        201,
    }:
        return {
            "status": "error",
            "posted": False,
            "post_id": "",
            "reason": (
                "X APIエラー："
                f"HTTP {response.status_code} / "
                f"{response.text}"
            ),
        }

    try:
        response_data = (
            response.json()
        )

    except ValueError:
        return {
            "status": "error",
            "posted": False,
            "post_id": "",
            "reason":
                "X APIのレスポンスJSONを"
                "解析できませんでした。",
        }

    data = response_data.get(
        "data",
        {},
    )

    if not isinstance(
        data,
        dict,
    ):
        data = {}

    post_id = str(
        data.get(
            "id",
            "",
        )
    ).strip()

    if not post_id:
        return {
            "status": "error",
            "posted": False,
            "post_id": "",
            "reason":
                "投稿自体は成功応答でしたが、"
                "Post IDを取得できませんでした。",
        }

    return {
        "status": "published",
        "posted": True,
        "post_id": post_id,
        "reason":
            "Xへの投稿が完了しました。",
    }


# =========================================================
# Console
# =========================================================

def print_route(
    index: int,
    route: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """投稿内容と結果を表示する。"""

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
        "--- POST ---"
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

    post_id = str(
        result.get(
            "post_id",
            "",
        )
    ).strip()

    if post_id:
        print(
            "Post ID："
            f"{post_id}"
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
    """X Publisherを実行する。"""

    routes = (
        load_ready_x_routes(article_slug)
    )

    print(
        "\n===== Atlas X Publisher =====\n"
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
            "投稿可能なX Routeはありません。"
        )
        return

    if apply_mode:
        # 実投稿する場合だけ認証情報を
        # 事前チェックする。
        get_x_credentials()

    for index, route in enumerate(
        routes,
        start=1,
    ):

        if apply_mode:
            result = (
                publish_to_x(
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
            post_id = str(
                result.get(
                    "post_id",
                    "",
                )
            ).strip()

            if post_id:
                mark_route_published(
                    route,
                    post_id,
                )

                print(
                    "[X Publisher] "
                    "投稿状態をpublishedへ更新しました。"
                )

        # 安全のため、実投稿時は
        # 一度の実行につき1件だけ投稿する。
        if apply_mode:
            break


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "Atlas X Publisher"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Xへ実際に投稿します。"
            "指定しない場合はDRY RUNです。"
        ),
    )

    parser.add_argument("--article-slug", default="")

    args = parser.parse_args()

    main(
        apply_mode=args.apply,
        article_slug=args.article_slug,
    )
