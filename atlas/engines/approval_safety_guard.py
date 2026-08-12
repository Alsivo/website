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

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "human_approval"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "approval_safety_status.json"
)


EXECUTABLE_DESTINATIONS = {
    "safe_execution",
}

HUMAN_DESTINATIONS = {
    "human_monetization",
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


def load_approval_map(
) -> dict[str, dict[str, Any]]:
    """approval_idをキーに承認案件を取得する。"""

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
        return {}

    approval_map: dict[
        str,
        dict[str, Any]
    ] = {}

    for item in queue:
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

        if not approval_id:
            continue

        approval_map[
            approval_id
        ] = item

    return approval_map


def load_routes(
) -> list[dict[str, Any]]:
    """Approved Action Routerの結果を取得する。"""

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

    return [
        item
        for item in routes
        if isinstance(
            item,
            dict,
        )
    ]


def validate_route(
    route: dict[str, Any],
    approval_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """1件のRouteを承認情報と再照合する。"""

    approval_id = str(
        route.get(
            "approval_id",
            "",
        )
    ).strip()

    action = str(
        route.get(
            "action",
            "",
        )
    ).strip()

    target = str(
        route.get(
            "target",
            "",
        )
    ).strip()

    destination = str(
        route.get(
            "destination",
            "",
        )
    ).strip()

    route_status = str(
        route.get(
            "route_status",
            "",
        )
    ).strip()

    base_result = {
        "checked_at":
            datetime.now().isoformat(),

        "approval_id":
            approval_id,

        "action":
            action,

        "target":
            target,

        "destination":
            destination,

        "route_status":
            route_status,

        "safe":
            False,

        "execution_allowed":
            False,

        "reason":
            "",
    }

    if not approval_id:
        base_result[
            "reason"
        ] = (
            "approval_idがないため"
            "実行を許可しません。"
        )

        return base_result

    approval = approval_map.get(
        approval_id
    )

    if not isinstance(
        approval,
        dict,
    ):
        base_result[
            "reason"
        ] = (
            "approval_idに対応する"
            "承認案件が存在しません。"
        )

        return base_result

    approval_status = str(
        approval.get(
            "status",
            "",
        )
    ).strip()

    if approval_status != "approved":
        base_result[
            "reason"
        ] = (
            "承認状態がapprovedではありません。"
            f" current={approval_status}"
        )

        return base_result

    approval_action = str(
        approval.get(
            "action",
            "",
        )
    ).strip()

    approval_target = str(
        approval.get(
            "target",
            "",
        )
    ).strip()

    if approval_action != action:
        base_result[
            "reason"
        ] = (
            "Routeのactionが"
            "承認内容と一致しません。"
        )

        return base_result

    if approval_target != target:
        base_result[
            "reason"
        ] = (
            "Routeのtargetが"
            "承認内容と一致しません。"
        )

        return base_result

    if route_status != "ready":
        base_result[
            "reason"
        ] = (
            "Route Statusがreadyではありません。"
            f" current={route_status}"
        )

        return base_result

    if destination in EXECUTABLE_DESTINATIONS:
        base_result[
            "safe"
        ] = True

        base_result[
            "execution_allowed"
        ] = True

        base_result[
            "reason"
        ] = (
            "approved状態とRoute内容が"
            "一致しているため、"
            "Safe Executionへの"
            "引き渡しを許可します。"
        )

        return base_result

    if destination in HUMAN_DESTINATIONS:
        base_result[
            "safe"
        ] = True

        base_result[
            "execution_allowed"
        ] = False

        base_result[
            "reason"
        ] = (
            "approved状態を確認しましたが、"
            "人間作業用Routeのため"
            "自動実行は許可しません。"
        )

        return base_result

    base_result[
        "reason"
    ] = (
        "許可されていないdestinationです："
        f"{destination}"
    )

    return base_result


def build_safety_results(
) -> list[dict[str, Any]]:
    """全Routeを安全性検証する。"""

    approval_map = (
        load_approval_map()
    )

    routes = (
        load_routes()
    )

    return [
        validate_route(
            route,
            approval_map,
        )
        for route in routes
    ]


def save_results(
    results: list[dict[str, Any]],
) -> Path:
    """Safety Guard結果を保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_count = sum(
        1
        for item in results
        if item.get(
            "safe"
        )
    )

    executable_count = sum(
        1
        for item in results
        if item.get(
            "execution_allowed"
        )
    )

    blocked_count = (
        len(results)
        - safe_count
    )

    payload = {
        "generated_at":
            datetime.now().isoformat(),

        "total":
            len(results),

        "safe":
            safe_count,

        "executable":
            executable_count,

        "blocked":
            blocked_count,

        "results":
            results,
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
    results: list[dict[str, Any]],
) -> None:
    """Safety Guard結果を表示する。"""

    safe_count = sum(
        1
        for item in results
        if item.get(
            "safe"
        )
    )

    executable_count = sum(
        1
        for item in results
        if item.get(
            "execution_allowed"
        )
    )

    blocked_count = (
        len(results)
        - safe_count
    )

    print(
        "\n===== Atlas Approval Safety Guard =====\n"
    )

    print(
        "Routes："
        f"{len(results)}"
    )

    print(
        "Safe："
        f"{safe_count}"
    )

    print(
        "Executable："
        f"{executable_count}"
    )

    print(
        "Blocked："
        f"{blocked_count}"
    )

    if results:
        print(
            "\n--- RESULTS ---"
        )

        for index, item in enumerate(
            results,
            start=1,
        ):
            print(
                f"[{index}] "
                f"{'SAFE' if item.get('safe') else 'BLOCKED'} / "
                f"{item.get('action', '')} / "
                f"{item.get('target', '')} / "
                f"{item.get('destination', '')} / "
                f"execute="
                f"{'YES' if item.get('execution_allowed') else 'NO'}"
            )

            print(
                "    "
                f"{item.get('reason', '')}"
            )


def main() -> None:
    """Approval Safety Guardを実行する。"""

    results = (
        build_safety_results()
    )

    filepath = (
        save_results(
            results
        )
    )

    print_summary(
        results
    )

    print()

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()