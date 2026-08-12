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

APPROVED_ROUTES_FILE = (
    BASE_DIR
    / "data"
    / "human_approval"
    / "approved_action_routes.json"
)

ATLAS_ALERT_FILE = (
    BASE_DIR
    / "data"
    / "alerts"
    / "latest_alert.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "notifications"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "notification_queue.json"
)


LEVEL_PRIORITY = {
    "CRITICAL": 100,
    "WARNING": 80,
    "ACTION": 60,
    "INFO": 40,
}


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONファイルを安全に読み込む。"""

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


def build_approval_notifications(
) -> list[dict[str, Any]]:
    """pending承認案件を通知化する。"""

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

    notifications: list[
        dict[str, Any]
    ] = []

    for item in queue:
        if not isinstance(
            item,
            dict,
        ):
            continue

        if (
            str(
                item.get(
                    "status",
                    "",
                )
            ).strip()
            != "pending"
        ):
            continue

        approval_id = str(
            item.get(
                "approval_id",
                "",
            )
        ).strip()

        action = str(
            item.get(
                "action",
                "",
            )
        ).strip()

        target = str(
            item.get(
                "target",
                "",
            )
        ).strip()

        notifications.append(
            {
                "notification_id":
                    (
                        "approval:"
                        f"{approval_id}"
                    ),

                "created_at":
                    datetime.now().isoformat(),

                "source":
                    "human_approval",

                "level":
                    "ACTION",

                "priority":
                    int(
                        item.get(
                            "priority",
                            0,
                        )
                        or 0
                    ),

                "title":
                    (
                        "承認待ちActionがあります："
                        f"{action}"
                    ),

                "target":
                    target,

                "message":
                    str(
                        item.get(
                            "reason",
                            "",
                        )
                    ).strip(),

                "next_action":
                    (
                        "Approval State Managerで"
                        "approveまたはrejectしてください。"
                    ),

                "approval_id":
                    approval_id,

                "action":
                    action,

                "status":
                    "pending",
            }
        )

    return notifications


def build_route_notifications(
) -> list[dict[str, Any]]:
    """承認済みRouteを通知化する。"""

    data = load_json(
        APPROVED_ROUTES_FILE
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

    notifications: list[
        dict[str, Any]
    ] = []

    for item in routes:
        if not isinstance(
            item,
            dict,
        ):
            continue

        approval_id = str(
            item.get(
                "approval_id",
                "",
            )
        ).strip()

        route_status = str(
            item.get(
                "route_status",
                "",
            )
        ).strip()

        action = str(
            item.get(
                "action",
                "",
            )
        ).strip()

        target = str(
            item.get(
                "target",
                "",
            )
        ).strip()

        destination = str(
            item.get(
                "destination",
                "",
            )
        ).strip()

        next_engine = str(
            item.get(
                "next_engine",
                "",
            )
        ).strip()

        if route_status == "blocked":
            level = "WARNING"

            title = (
                "承認済みActionのRouteが"
                "BLOCKEDです"
            )

            next_action = (
                "Router設定またはAction種別を"
                "確認してください。"
            )

        elif (
            route_status == "ready"
            and destination
            == "human_monetization"
        ):
            level = "ACTION"

            title = (
                "承認済み収益化Actionがあります："
                f"{target}"
            )

            next_action = (
                "収益化ワークフローを"
                "人間が確認してください。"
            )

        elif (
            route_status == "ready"
            and destination
            == "safe_execution"
        ):
            level = "INFO"

            title = (
                "承認済みActionが"
                "Safe Execution待ちです"
            )

            next_action = (
                "Safe Executorへの"
                "引き渡し状態を確認してください。"
            )

        else:
            continue

        notifications.append(
            {
                "notification_id":
                    (
                        "route:"
                        f"{approval_id}:"
                        f"{route_status}"
                    ),

                "created_at":
                    datetime.now().isoformat(),

                "source":
                    "approved_action_router",

                "level":
                    level,

                "priority":
                    int(
                        item.get(
                            "priority",
                            0,
                        )
                        or 0
                    ),

                "title":
                    title,

                "target":
                    target,

                "message":
                    str(
                        item.get(
                            "reason",
                            "",
                        )
                    ).strip(),

                "next_action":
                    next_action,

                "approval_id":
                    approval_id,

                "action":
                    action,

                "destination":
                    destination,

                "next_engine":
                    next_engine,

                "status":
                    route_status,
            }
        )

    return notifications


def build_alert_notifications(
) -> list[dict[str, Any]]:
    """Atlas Alertを通知化する。"""

    data = load_json(
        ATLAS_ALERT_FILE
    )

    alerts = data.get(
        "alerts",
        [],
    )

    if not isinstance(
        alerts,
        list,
    ):
        return []

    notifications: list[
        dict[str, Any]
    ] = []

    for index, item in enumerate(
        alerts,
        start=1,
    ):
        if not isinstance(
            item,
            dict,
        ):
            continue

        level = str(
            item.get(
                "level",
                "INFO",
            )
        ).strip().upper()

        if level not in LEVEL_PRIORITY:
            level = "INFO"

        title = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        reason = str(
            item.get(
                "reason",
                "",
            )
        ).strip()

        next_action = str(
            item.get(
                "next",
                "",
            )
        ).strip()

        source = str(
            item.get(
                "source",
                "",
            )
        ).strip()

        notifications.append(
            {
                "notification_id":
                    (
                        "alert:"
                        f"{index}:"
                        f"{level}:"
                        f"{source}:"
                        f"{title}"
                    ),

                "created_at":
                    datetime.now().isoformat(),

                "source":
                    "atlas_alert",

                "level":
                    level,

                "priority":
                    LEVEL_PRIORITY[
                        level
                    ],

                "title":
                    title,

                "target":
                    source,

                "message":
                    reason,

                "next_action":
                    next_action,

                "status":
                    "active",
            }
        )

    return notifications


def deduplicate_notifications(
    notifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """notification_id単位で重複を除去する。"""

    unique: dict[
        str,
        dict[str, Any]
    ] = {}

    for item in notifications:
        notification_id = str(
            item.get(
                "notification_id",
                "",
            )
        ).strip()

        if not notification_id:
            continue

        if (
            notification_id
            not in unique
        ):
            unique[
                notification_id
            ] = item

    return list(
        unique.values()
    )


def sort_notifications(
    notifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """重要度順に並べる。"""

    def sort_key(
        item: dict[str, Any],
    ) -> tuple[int, int, str]:

        level = str(
            item.get(
                "level",
                "INFO",
            )
        ).strip().upper()

        return (
            LEVEL_PRIORITY.get(
                level,
                0,
            ),
            int(
                item.get(
                    "priority",
                    0,
                )
                or 0
            ),
            str(
                item.get(
                    "created_at",
                    "",
                )
            ),
        )

    return sorted(
        notifications,
        key=sort_key,
        reverse=True,
    )


def build_notification_queue(
) -> list[dict[str, Any]]:
    """全通知ソースを統合する。"""

    notifications = []

    notifications.extend(
        build_approval_notifications()
    )

    notifications.extend(
        build_route_notifications()
    )

    notifications.extend(
        build_alert_notifications()
    )

    notifications = (
        deduplicate_notifications(
            notifications
        )
    )

    notifications = (
        sort_notifications(
            notifications
        )
    )

    return notifications


def save_notifications(
    notifications: list[dict[str, Any]],
) -> Path:
    """通知キューを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    level_counts = {
        "CRITICAL": 0,
        "WARNING": 0,
        "ACTION": 0,
        "INFO": 0,
    }

    for item in notifications:
        level = str(
            item.get(
                "level",
                "INFO",
            )
        ).strip().upper()

        if level in level_counts:
            level_counts[
                level
            ] += 1

    payload = {
        "generated_at":
            datetime.now().isoformat(),

        "total":
            len(
                notifications
            ),

        "requires_attention":
            any(
                item.get(
                    "level"
                )
                in {
                    "CRITICAL",
                    "WARNING",
                    "ACTION",
                }
                for item in notifications
            ),

        "counts":
            level_counts,

        "notifications":
            notifications,
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
    notifications: list[dict[str, Any]],
) -> None:
    """通知キューを表示する。"""

    print(
        "\n===== Atlas Notification Engine =====\n"
    )

    print(
        "Total："
        f"{len(notifications)}"
    )

    for level in [
        "CRITICAL",
        "WARNING",
        "ACTION",
        "INFO",
    ]:
        count = sum(
            1
            for item in notifications
            if item.get(
                "level"
            )
            == level
        )

        print(
            f"{level}：{count}"
        )

    if notifications:
        print(
            "\n--- NOTIFICATIONS ---"
        )

        for index, item in enumerate(
            notifications[:20],
            start=1,
        ):
            print(
                f"[{index}] "
                f"{item.get('level', '')} / "
                f"{item.get('source', '')} / "
                f"{item.get('title', '')}"
            )


def main() -> None:
    """Notification Engineを更新する。"""

    notifications = (
        build_notification_queue()
    )

    filepath = (
        save_notifications(
            notifications
        )
    )

    print_summary(
        notifications
    )

    print()
    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()