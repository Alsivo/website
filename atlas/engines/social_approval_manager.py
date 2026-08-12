import json
import sys
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


VALID_STATUSES = {
    "pending",
    "approved",
    "rejected",
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
    ) as error:
        raise RuntimeError(
            "Social Approval Queueを"
            "読み込めませんでした。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Social Approval Queue形式が不正です。"
        )

    return data


def load_queue(
) -> list[dict[str, Any]]:
    """承認Queueを読み込む。"""

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

    return [
        item
        for item in queue
        if isinstance(
            item,
            dict,
        )
    ]


def save_queue(
    queue: list[dict[str, Any]],
) -> None:
    """承認Queueを保存する。"""

    pending = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "pending"
    )

    approved = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "approved"
    )

    rejected = sum(
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
            pending,

        "approved":
            approved,

        "rejected":
            rejected,

        "queue":
            queue,
    }

    APPROVAL_QUEUE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    APPROVAL_QUEUE_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def find_item(
    queue: list[dict[str, Any]],
    approval_id: str,
) -> dict[str, Any] | None:
    """Approval IDから対象を探す。"""

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


def print_item(
    item: dict[str, Any],
    index: int | None = None,
) -> None:
    """承認候補を表示する。"""

    print(
        "--------------------------------"
    )

    if index is not None:
        print(
            f"[{index}]"
        )

    print(
        "Approval ID："
        f"{item.get('approval_id', '')}"
    )

    print(
        "Status："
        f"{item.get('status', '')}"
    )

    print(
        "Platform："
        f"{item.get('platform', '')}"
    )

    print(
        "Article："
        f"{item.get('article_slug', '')}"
    )

    print(
        "Title："
        f"{item.get('article_title', '')}"
    )

    print()

    print(
        item.get(
            "post_text",
            "",
        )
    )

    print()


def list_queue(
    queue: list[dict[str, Any]],
) -> None:
    """承認Queue一覧を表示する。"""

    print(
        "\n===== Atlas Social Approval =====\n"
    )

    pending = [
        item
        for item in queue
        if item.get(
            "status"
        )
        == "pending"
    ]

    approved = [
        item
        for item in queue
        if item.get(
            "status"
        )
        == "approved"
    ]

    rejected = [
        item
        for item in queue
        if item.get(
            "status"
        )
        == "rejected"
    ]

    print(
        "Total："
        f"{len(queue)}"
    )

    print(
        "Pending："
        f"{len(pending)}"
    )

    print(
        "Approved："
        f"{len(approved)}"
    )

    print(
        "Rejected："
        f"{len(rejected)}"
    )

    if not queue:
        print(
            "\n承認対象はありません。"
        )
        return

    print()

    for index, item in enumerate(
        queue,
        start=1,
    ):
        print_item(
            item,
            index=index,
        )


def approve_item(
    queue: list[dict[str, Any]],
    approval_id: str,
    note: str = "",
) -> None:
    """投稿候補を承認する。"""

    item = find_item(
        queue,
        approval_id,
    )

    if item is None:
        raise RuntimeError(
            "Approval IDが見つかりません："
            f"{approval_id}"
        )

    current_status = str(
        item.get(
            "status",
            "",
        )
    ).strip()

    if current_status == "approved":
        print(
            "この投稿はすでに承認済みです。"
        )
        return

    if current_status == "rejected":
        raise RuntimeError(
            "却下済み投稿はそのまま"
            "承認できません。"
        )

    if (
        current_status
        not in VALID_STATUSES
    ):
        raise RuntimeError(
            "不正なstatusです："
            f"{current_status}"
        )

    now = datetime.now().isoformat()

    item[
        "status"
    ] = "approved"

    item[
        "approved_at"
    ] = now

    item[
        "rejected_at"
    ] = ""

    item[
        "updated_at"
    ] = now

    item[
        "decision_note"
    ] = note

    save_queue(
        queue
    )

    print(
        "\n承認しました。"
    )

    print_item(
        item
    )


def reject_item(
    queue: list[dict[str, Any]],
    approval_id: str,
    note: str = "",
) -> None:
    """投稿候補を却下する。"""

    item = find_item(
        queue,
        approval_id,
    )

    if item is None:
        raise RuntimeError(
            "Approval IDが見つかりません："
            f"{approval_id}"
        )

    current_status = str(
        item.get(
            "status",
            "",
        )
    ).strip()

    if current_status == "rejected":
        print(
            "この投稿はすでに却下済みです。"
        )
        return

    if current_status == "approved":
        raise RuntimeError(
            "承認済み投稿はそのまま"
            "却下できません。"
        )

    if (
        current_status
        not in VALID_STATUSES
    ):
        raise RuntimeError(
            "不正なstatusです："
            f"{current_status}"
        )

    now = datetime.now().isoformat()

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
        "updated_at"
    ] = now

    item[
        "decision_note"
    ] = note

    save_queue(
        queue
    )

    print(
        "\n却下しました。"
    )

    print_item(
        item
    )


def main() -> None:
    """Social Approval Manager。"""

    args = sys.argv[1:]

    if not args:
        raise SystemExit(
            "\n使い方：\n"
            "python -m engines.social_approval_manager list\n"
            "python -m engines.social_approval_manager approve <approval_id>\n"
            "python -m engines.social_approval_manager reject <approval_id>\n"
        )

    command = (
        args[0]
        .strip()
        .lower()
    )

    queue = load_queue()

    if command == "list":

        list_queue(
            queue
        )

        return

    if command not in {
        "approve",
        "reject",
    }:
        raise SystemExit(
            "未対応commandです："
            f"{command}"
        )

    if len(args) < 2:
        raise SystemExit(
            "Approval IDを指定してください。"
        )

    approval_id = (
        args[1]
        .strip()
    )

    note = (
        " ".join(
            args[2:]
        ).strip()
        if len(args) >= 3
        else ""
    )

    if command == "approve":

        approve_item(
            queue,
            approval_id,
            note,
        )

    elif command == "reject":

        reject_item(
            queue,
            approval_id,
            note,
        )


if __name__ == "__main__":
    main()