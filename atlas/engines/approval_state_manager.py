import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "human_approval"
    / "approval_queue.json"
)


ALLOWED_DECISIONS = {
    "approve",
    "reject",
}


def load_queue_data(
) -> dict[str, Any]:
    """承認キューJSONを読み込む。"""

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            "approval_queue.jsonが"
            "見つかりません："
            f"{QUEUE_FILE}"
        )

    try:
        data = json.loads(
            QUEUE_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "approval_queue.jsonの"
            "JSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "approval_queue.jsonの"
            "最上位はobjectにしてください。"
        )

    queue = data.get(
        "queue",
        [],
    )

    if not isinstance(
        queue,
        list,
    ):
        raise ValueError(
            "queueは配列にしてください。"
        )

    return data


def get_queue(
    data: dict[str, Any],
) -> list[dict[str, Any]]:
    """有効なQueue項目だけ取得する。"""

    raw_queue = data.get(
        "queue",
        [],
    )

    return [
        item
        for item in raw_queue
        if isinstance(
            item,
            dict,
        )
    ]


def find_item(
    queue: list[dict[str, Any]],
    approval_id: str,
) -> dict[str, Any] | None:
    """approval_idから対象案件を取得する。"""

    approval_id = (
        approval_id.strip()
    )

    for item in queue:
        if (
            str(
                item.get(
                    "approval_id",
                    "",
                )
            ).strip()
            == approval_id
        ):
            return item

    return None


def apply_decision(
    item: dict[str, Any],
    decision: str,
    note: str = "",
) -> tuple[bool, str]:
    """pending案件へapprove/rejectを適用する。"""

    decision = (
        decision.strip().lower()
    )

    if decision not in ALLOWED_DECISIONS:
        return (
            False,
            (
                "decisionはapproveまたは"
                "rejectを指定してください。"
            ),
        )

    current_status = str(
        item.get(
            "status",
            "",
        )
    ).strip()

    if current_status != "pending":
        return (
            False,
            (
                "pendingではないため"
                "状態変更できません。"
                f" current={current_status}"
            ),
        )

    now = (
        datetime.now().isoformat()
    )

    if decision == "approve":
        item[
            "status"
        ] = "approved"

        item[
            "approved_at"
        ] = now

        item[
            "rejected_at"
        ] = ""

    else:
        item[
            "status"
        ] = "rejected"

        item[
            "rejected_at"
        ] = now

        item[
            "approved_at"
        ] = ""

    item[
        "decision_note"
    ] = note.strip()

    return (
        True,
        "",
    )


def save_queue_data(
    data: dict[str, Any],
) -> Path:
    """更新した承認キューを保存する。"""

    queue = get_queue(
        data
    )

    pending_count = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "pending"
    )

    approved_count = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "approved"
    )

    rejected_count = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "rejected"
    )

    payload = {
        "updated_at":
            datetime.now().isoformat(),

        "total":
            len(queue),

        "pending":
            pending_count,

        "approved":
            approved_count,

        "rejected":
            rejected_count,

        "queue":
            queue,
    }

    QUEUE_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return QUEUE_FILE


def print_queue(
    queue: list[dict[str, Any]],
) -> None:
    """承認キューを一覧表示する。"""

    print(
        "\n===== Atlas Approval State =====\n"
    )

    if not queue:
        print(
            "承認案件はありません。"
        )
        return

    for index, item in enumerate(
        queue,
        start=1,
    ):
        print(
            f"[{index}] "
            f"{item.get('approval_id', '')} / "
            f"{item.get('status', '')} / "
            f"{item.get('action', '')} / "
            f"{item.get('target', '')} / "
            f"priority={item.get('priority', 0)}"
        )


def main() -> None:
    """Human Approval状態を管理する。"""

    args = sys.argv[
        1:
    ]

    data = (
        load_queue_data()
    )

    queue = (
        get_queue(
            data
        )
    )

    if not args:
        print_queue(
            queue
        )
        return

    command = (
        args[0]
        .strip()
        .lower()
    )

    if command == "list":
        print_queue(
            queue
        )
        return

    if command not in ALLOWED_DECISIONS:
        raise ValueError(
            "使用方法：\n"
            "python -m "
            "engines.approval_state_manager list\n"
            "python -m "
            "engines.approval_state_manager "
            "approve <approval_id> [note]\n"
            "python -m "
            "engines.approval_state_manager "
            "reject <approval_id> [note]"
        )

    if len(args) < 2:
        raise ValueError(
            "approval_idを"
            "指定してください。"
        )

    approval_id = (
        args[1].strip()
    )

    note = (
        " ".join(
            args[2:]
        ).strip()
        if len(args) >= 3
        else ""
    )

    item = find_item(
        queue,
        approval_id,
    )

    if item is None:
        raise ValueError(
            "指定されたapproval_idが"
            "見つかりません："
            f"{approval_id}"
        )

    changed, reason = (
        apply_decision(
            item,
            command,
            note,
        )
    )

    if not changed:
        print(
            "\n===== Atlas Approval State =====\n"
        )

        print(
            "Status：SKIP"
        )

        print(
            "Approval ID："
            f"{approval_id}"
        )

        print(
            "Reason："
            f"{reason}"
        )

        return

    filepath = (
        save_queue_data(
            data
        )
    )

    print(
        "\n===== Atlas Approval State =====\n"
    )

    print(
        "Status：UPDATED"
    )

    print(
        "Approval ID："
        f"{approval_id}"
    )

    print(
        "Decision："
        f"{command.upper()}"
    )

    print(
        "Action："
        f"{item.get('action', '')}"
    )

    print(
        "Target："
        f"{item.get('target', '')}"
    )

    if note:
        print(
            "Note："
            f"{note}"
        )

    print()

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()