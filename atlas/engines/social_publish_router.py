import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

APPROVAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_approval_queue.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "social"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "social_publish_routes.json"
)


PLATFORM_ROUTES = {
    "x": {
        "destination": "x",
        "publisher": "x_publisher",
    },
    "instagram": {
        "destination": "instagram",
        "publisher": "instagram_publisher",
    },
}


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


def build_route(
    item: dict[str, Any],
) -> dict[str, Any] | None:
    """承認済みSocial ActionからPublish Routeを作る。"""

    status = str(
        item.get(
            "status",
            "",
        )
    ).strip().lower()

    if status != "approved":
        return None

    platform = str(
        item.get(
            "platform",
            "",
        )
    ).strip().lower()

    route_config = (
        PLATFORM_ROUTES.get(
            platform
        )
    )

    if route_config is None:
        return {
            "approval_id":
                str(
                    item.get(
                        "approval_id",
                        "",
                    )
                ).strip(),

            "article_slug":
                str(
                    item.get(
                        "article_slug",
                        "",
                    )
                ).strip(),

            "platform":
                platform,

            "route_status":
                "blocked",

            "destination":
                "",

            "publisher":
                "",

            "reason":
                "未対応platformです。",

            "post_text":
                str(
                    item.get(
                        "post_text",
                        "",
                    )
                ).strip(),

            "article_url":
                str(
                    item.get(
                        "article_url",
                        "",
                    )
                ).strip(),
        }

    post_text = str(
        item.get(
            "post_text",
            "",
        )
    ).strip()

    if not post_text:
        return {
            "approval_id":
                str(
                    item.get(
                        "approval_id",
                        "",
                    )
                ).strip(),

            "article_slug":
                str(
                    item.get(
                        "article_slug",
                        "",
                    )
                ).strip(),

            "platform":
                platform,

            "route_status":
                "blocked",

            "destination":
                route_config[
                    "destination"
                ],

            "publisher":
                route_config[
                    "publisher"
                ],

            "reason":
                "post_textがありません。",

            "post_text":
                "",

            "article_url":
                str(
                    item.get(
                        "article_url",
                        "",
                    )
                ).strip(),
        }

    return {
        "approval_id":
            str(
                item.get(
                    "approval_id",
                    "",
                )
            ).strip(),

        "article_slug":
            str(
                item.get(
                    "article_slug",
                    "",
                )
            ).strip(),

        "article_title":
            str(
                item.get(
                    "article_title",
                    "",
                )
            ).strip(),

        "platform":
            platform,

        "route_status":
            "ready",

        "destination":
            route_config[
                "destination"
            ],

        "publisher":
            route_config[
                "publisher"
            ],

        "reason":
            "承認済み投稿です。",

        "post_text":
            post_text,

        "article_url":
            str(
                item.get(
                    "article_url",
                    "",
                )
            ).strip(),

        "approved_at":
            str(
                item.get(
                    "approved_at",
                    "",
                )
            ).strip(),

        "routed_at":
            datetime.now().isoformat(),
    }


def build_routes(
) -> list[dict[str, Any]]:
    """Publish Route一覧を作る。"""

    data = load_json(
        APPROVAL_QUEUE_FILE
    )

    queue = data.get(
        "queue",
        [],
    )

    if not isinstance(
        queue,
        list,
    ):
        raise RuntimeError(
            "Social Approval Queue形式が不正です。"
        )

    routes: list[
        dict[str, Any]
    ] = []

    for item in queue:

        if not isinstance(
            item,
            dict,
        ):
            continue

        route = build_route(
            item
        )

        if route is None:
            continue

        routes.append(
            route
        )

    return routes


def save_routes(
    routes: list[dict[str, Any]],
) -> Path:
    """Publish Routeを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ready = sum(
        1
        for item in routes
        if item.get(
            "route_status"
        )
        == "ready"
    )

    blocked = sum(
        1
        for item in routes
        if item.get(
            "route_status"
        )
        == "blocked"
    )

    payload = {
        "generated_at":
            datetime.now().isoformat(),

        "total":
            len(routes),

        "ready":
            ready,

        "blocked":
            blocked,

        "routes":
            routes,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_summary(
    routes: list[dict[str, Any]],
) -> None:
    """Route結果を表示する。"""

    print(
        "\n===== Atlas Social Publish Router =====\n"
    )

    ready = [
        item
        for item in routes
        if item.get(
            "route_status"
        )
        == "ready"
    ]

    blocked = [
        item
        for item in routes
        if item.get(
            "route_status"
        )
        == "blocked"
    ]

    print(
        "Total："
        f"{len(routes)}"
    )

    print(
        "Ready："
        f"{len(ready)}"
    )

    print(
        "Blocked："
        f"{len(blocked)}"
    )

    if routes:

        print(
            "\n--- ROUTES ---"
        )

        for index, item in enumerate(
            routes,
            start=1,
        ):

            print(
                f"[{index}] "
                f"{item.get('platform', '')} / "
                f"{item.get('route_status', '')} / "
                f"{item.get('publisher', '')} / "
                f"{item.get('article_slug', '')}"
            )


def main() -> None:
    """Social Publish Routerを実行する。"""

    routes = build_routes()

    filepath = save_routes(
        routes
    )

    print_summary(
        routes
    )

    print()

    print(
        "保存先："
        f"{filepath}"
    )


if __name__ == "__main__":
    main()
