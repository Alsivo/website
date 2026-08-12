import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent

OPTIMIZATION_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "optimization"
    / "optimization_decision.json"
)

EXECUTION_PLAN_FILE = (
    BASE_DIR
    / "data"
    / "safe_execution"
    / "execution_plan.json"
)

HISTORY_DIR = (
    BASE_DIR
    / "data"
    / "optimization_history"
)

HISTORY_FILE = (
    HISTORY_DIR
    / "history.json"
)

EXECUTION_RESULT_FILE = (
    BASE_DIR
    / "data"
    / "safe_execution"
    / "execution_result.json"
)

def load_json(
    path: Path,
) -> dict[str, Any]:
    """JSONファイルを安全に読み込む。"""

    if not path.exists():
        return {}

    try:
        data = json.loads(
            path.read_text(
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


def load_history() -> list[dict[str, Any]]:
    """既存のOptimization履歴を読み込む。"""

    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(
            HISTORY_FILE.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []

    if isinstance(
        data,
        list,
    ):
        return [
            item
            for item in data
            if isinstance(
                item,
                dict,
            )
        ]

    if isinstance(
        data,
        dict,
    ):
        history = data.get(
            "history",
            [],
        )

        if isinstance(
            history,
            list,
        ):
            return [
                item
                for item in history
                if isinstance(
                    item,
                    dict,
                )
            ]

    return []


def build_history_entry(
    decision: dict[str, Any],
    execution_plan: dict[str, Any],
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    """今回のOptimization履歴を作る。"""

    selected = decision.get(
        "selected",
        {},
    )

    if not isinstance(
        selected,
        dict,
    ):
        selected = {}

    return {
        "recorded_at":
            datetime.now().isoformat(),

        # ----------------------------------------------------
        # Optimization Decision
        # ----------------------------------------------------

        "decision_status":
            str(
                decision.get(
                    "status",
                    "",
                )
            ),

        "trend_state":
            str(
                decision.get(
                    "trend_state",
                    "",
                )
            ),

        "action":
            str(
                selected.get(
                    "action",
                    "",
                )
            ),

        "source":
            str(
                selected.get(
                    "source",
                    "",
                )
            ),

        "target_type":
            str(
                selected.get(
                    "target_type",
                    "",
                )
            ),

        "target":
            str(
                selected.get(
                    "target",
                    "",
                )
            ),

        "priority":
            int(
                selected.get(
                    "priority",
                    0,
                )
                or 0
            ),

        "execution_mode":
            str(
                selected.get(
                    "execution_mode",
                    "",
                )
            ),

        "execution_allowed":
            bool(
                selected.get(
                    "execution_allowed",
                    False,
                )
            ),

        "reason":
            str(
                selected.get(
                    "reason",
                    "",
                )
            ),

        "next_action":
            str(
                selected.get(
                    "recommended_action",
                    "",
                )
            ),

        # ----------------------------------------------------
        # Safe Execution Plan
        # ----------------------------------------------------

        "safe_plan_status":
            str(
                execution_plan.get(
                    "status",
                    "",
                )
            ),

        "safe_plan_action":
            str(
                execution_plan.get(
                    "action",
                    "",
                )
            ),

        "safe_plan_target":
            str(
                execution_plan.get(
                    "target",
                    "",
                )
            ),

        "safe_plan_allowed":
            bool(
                execution_plan.get(
                    "execution_allowed",
                    False,
                )
            ),

        "next_executor":
            str(
                execution_plan.get(
                    "next_executor",
                    "",
                )
            ),

        # ----------------------------------------------------
        # Actual Execution Result
        # ----------------------------------------------------

        "execution_result_status":
            str(
                execution_result.get(
                    "status",
                    "",
                )
            ),

        "actually_executed":
            bool(
                execution_result.get(
                    "executed",
                    False,
                )
            ),

        "execution_result_action":
            str(
                execution_result.get(
                    "action",
                    "",
                )
            ),

        "execution_result_target":
            str(
                execution_result.get(
                    "target",
                    "",
                )
            ),

        "execution_dry_run":
            bool(
                execution_result.get(
                    "dry_run",
                    False,
                )
            ),

        "execution_result_reason":
            str(
                execution_result.get(
                    "reason",
                    "",
                )
            ),
    }


def is_duplicate(
    history: list[dict[str, Any]],
    entry: dict[str, Any],
) -> bool:
    """同じ判断を同日に重複記録しない。"""

    today = datetime.now().date().isoformat()

    for item in reversed(
        history
    ):
        recorded_at = str(
            item.get(
                "recorded_at",
                "",
            )
        )

        if not recorded_at.startswith(
            today
        ):
            continue

        if (
            item.get("action")
            == entry.get("action")
            and item.get("source")
            == entry.get("source")
            and item.get("target")
            == entry.get("target")
            and item.get("safe_plan_status")
            == entry.get("safe_plan_status")
            and item.get("safe_plan_action")
            == entry.get("safe_plan_action")
        ):
            return True

    return False


def save_history(
    history: list[dict[str, Any]],
) -> None:
    """Optimization履歴を保存する。"""

    HISTORY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "updated_at":
            datetime.now().isoformat(),
        "total":
            len(history),
        "history":
            history,
    }

    HISTORY_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    """Optimization Decisionと実行結果を履歴化する。"""

    decision = load_json(
        OPTIMIZATION_DECISION_FILE
    )

    execution_plan = load_json(
        EXECUTION_PLAN_FILE
    )

    execution_result = load_json(
        EXECUTION_RESULT_FILE
    )

    if not decision:
        raise RuntimeError(
            "Optimization Decisionが"
            "見つかりません。"
        )

    history = load_history()

    entry = build_history_entry(
        decision,
        execution_plan,
        execution_result,
    )

    duplicate = is_duplicate(
        history,
        entry,
    )

    if not duplicate:
        history.append(
            entry
        )

        save_history(
            history
        )

    print()

    print(
        "===== Atlas Optimization History ====="
    )

    print()

    print(
        f"History Entries：{len(history)}"
    )

    # --------------------------------------------------------
    # Optimization Decision
    # --------------------------------------------------------

    print(
        "\nDECISION"
    )

    print(
        "Action："
        f"{entry.get('action', '')}"
    )

    print(
        "Target："
        f"{entry.get('target', '')}"
    )

    print(
        "Priority："
        f"{entry.get('priority', 0)}"
    )

    print(
        "Execution Mode："
        f"{entry.get('execution_mode', '')}"
    )

    print(
        "Execution Allowed："
        + (
            "YES"
            if entry.get(
                "execution_allowed"
            )
            else "NO"
        )
    )

    # --------------------------------------------------------
    # Safe Execution Plan
    # --------------------------------------------------------

    print(
        "\nSAFE PLAN"
    )

    print(
        "Status："
        f"{entry.get('safe_plan_status', '')}"
    )

    print(
        "Action："
        f"{entry.get('safe_plan_action', '')}"
    )

    print(
        "Target："
        f"{entry.get('safe_plan_target', '')}"
    )

    print(
        "Allowed："
        + (
            "YES"
            if entry.get(
                "safe_plan_allowed"
            )
            else "NO"
        )
    )

    print(
        "Next Executor："
        f"{entry.get('next_executor', '')}"
    )

    # --------------------------------------------------------
    # Actual Execution Result
    # --------------------------------------------------------

    print(
        "\nEXECUTION RESULT"
    )

    print(
        "Status："
        f"{entry.get('execution_result_status', '')}"
    )

    print(
        "Action："
        f"{entry.get('execution_result_action', '')}"
    )

    print(
        "Target："
        f"{entry.get('execution_result_target', '')}"
    )

    print(
        "Actually Executed："
        + (
            "YES"
            if entry.get(
                "actually_executed"
            )
            else "NO"
        )
    )

    print(
        "Dry Run："
        + (
            "YES"
            if entry.get(
                "execution_dry_run"
            )
            else "NO"
        )
    )

    result_reason = str(
        entry.get(
            "execution_result_reason",
            "",
        )
    ).strip()

    if result_reason:
        print(
            "Reason："
            f"{result_reason}"
        )

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    print()

    if duplicate:
        print(
            "Record：SKIP "
            "(本日の同一判断は記録済み)"
        )
    else:
        print(
            "Record：ADDED"
        )

    print()

    print(
        f"保存先：{HISTORY_FILE}"
    )

if __name__ == "__main__":
    main()