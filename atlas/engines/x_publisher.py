import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

SOCIAL_PUBLISH_ROUTES_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_publish_routes.json"
)


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


def load_ready_x_routes(
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

    # 日本語などを含むため厳密なX文字数計算は
    # 後でAPI接続時に追加する。
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
            "status":
                "blocked",
            "posted":
                False,
            "reason":
                reason,
        }

    return {
        "status":
            "dry_run",
        "posted":
            False,
        "reason":
            "DRY RUNのためXには投稿していません。",
    }


def print_route(
    index: int,
    route: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """投稿予定内容を表示する。"""

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

    print(
        "Result："
        f"{result.get('reason', '')}"
    )

    print()


def main() -> None:
    """X PublisherをDRY RUNで実行する。"""

    routes = (
        load_ready_x_routes()
    )

    print(
        "\n===== Atlas X Publisher =====\n"
    )

    print(
        "Mode：DRY RUN"
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

    for index, route in enumerate(
        routes,
        start=1,
    ):
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


if __name__ == "__main__":
    main()