import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

APPROVAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "human_approval"
    / "approval_queue.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "human_approval"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "approved_action_routes.json"
)


SAFE_EXECUTION_ACTIONS = {
    "TITLE_ONLY",
    "STRENGTHEN",
    "REWRITE",
}

HUMAN_MONETIZATION_ACTIONS = {
    "MONETIZE",
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


def load_approved_items(
) -> list[dict[str, Any]]:
    """Approval Queueからapproved案件を取得する。"""

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
        return []

    return [
        item
        for item in queue
        if (
            isinstance(
                item,
                dict,
            )
            and str(
                item.get(
                    "status",
                    "",
                )
            ).strip()
            == "approved"
        )
    ]


def determine_route(
    item: dict[str, Any],
) -> dict[str, str]:
    """Actionに応じたルートを決定する。"""

    action = str(
        item.get(
            "action",
            "",
        )
    ).strip()

    target_type = str(
        item.get(
            "target_type",
            "",
        )
    ).strip()

    if action in SAFE_EXECUTION_ACTIONS:
        if target_type != "article":
            return {
                "route_status":
                    "blocked",
                "destination":
                    "",
                "next_engine":
                    "",
                "reason":
                    (
                        "記事変更Actionですが"
                        "target_typeがarticleではありません。"
                    ),
            }

        return {
            "route_status":
                "ready",
            "destination":
                "safe_execution",
            "next_engine":
                "safe_executor",
            "reason":
                (
                    "承認済みの記事変更Actionのため"
                    "Safe Executorへ引き渡します。"
                ),
        }

    if action in HUMAN_MONETIZATION_ACTIONS:
        return {
            "route_status":
                "ready",
            "destination":
                "human_monetization",
            "next_engine":
                "domestic_asp_candidate_queue",
            "reason":
                (
                    "収益化Actionは外部ASP確認など"
                    "人間作業を含むため、"
                    "自動実行せず収益化ワークフローへ送ります。"
                ),
        }

    return {
        "route_status":
            "blocked",
        "destination":
            "",
        "next_engine":
            "",
        "reason":
            (
                "承認済みですが対応ルートが"
                f"定義されていません：{action}"
            ),
    }


def build_route_item(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Approved案件からRoute情報を作る。"""

    route = determine_route(
        item
    )

    return {
        "routed_at":
            datetime.now().isoformat(),

        "approval_id":
            str(
                item.get(
                    "approval_id",
                    "",
                )
            ).strip(),

        "approval_status":
            str(
                item.get(
                    "status",
                    "",
                )
            ).strip(),

        "action":
            str(
                item.get(
                    "action",
                    "",
                )
            ).strip(),

        "source":
            str(
                item.get(
                    "source",
                    "",
                )
            ).strip(),

        "target_type":
            str(
                item.get(
                    "target_type",
                    "",
                )
            ).strip(),

        "target":
            str(
                item.get(
                    "target",
                    "",
                )
            ).strip(),

        "priority":
            int(
                item.get(
                    "priority",
                    0,
                )
                or 0
            ),

        "decision_note":
            str(
                item.get(
                    "decision_note",
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

        **route,
    }


def build_routes(
    approved_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Approved案件すべてのRouting結果を作る。"""

    routes = [
        build_route_item(
            item
        )
        for item in approved_items
    ]

    routes.sort(
        key=lambda item: (
            int(
                item.get(
                    "priority",
                    0,
                )
                or 0
            ),
            str(
                item.get(
                    "approved_at",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    return routes


def save_routes(
    routes: list[dict[str, Any]],
) -> Path:
    """Routing結果を保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    ready_count = sum(
        1
        for item in routes
        if item.get(
            "route_status"
        )
        == "ready"
    )

    blocked_count = sum(
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
            ready_count,

        "blocked":
            blocked_count,

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
    """Routing結果を表示する。"""

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
        "\n===== Atlas Approved Action Router =====\n"
    )

    print(
        "Approved："
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
                f"{item.get('route_status', '')} / "
                f"{item.get('action', '')} / "
                f"{item.get('target', '')} / "
                f"{item.get('destination', '')} / "
                f"{item.get('next_engine', '')}"
            )


def main() -> None:
    """Approved Action Routingを更新する。"""

    approved_items = (
        load_approved_items()
    )

    routes = (
        build_routes(
            approved_items
        )
    )

    filepath = (
        save_routes(
            routes
        )
    )

    print_summary(
        routes
    )

    print()
    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()