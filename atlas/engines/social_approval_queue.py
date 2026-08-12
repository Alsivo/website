import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

SOCIAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_queue.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_approval_queue.json"
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


def normalize_text(
    value: Any,
) -> str:
    return str(
        value
        if value is not None
        else ""
    ).strip()


def build_post_hash(
    item: dict[str, Any],
) -> str:
    """
    承認対象の投稿内容を識別するHashを作る。

    投稿文が変更された場合は、
    別の承認対象として扱う。
    """

    payload = {
        "platform":
            normalize_text(
                item.get(
                    "platform",
                    "",
                )
            ),

        "article_slug":
            normalize_text(
                item.get(
                    "article_slug",
                    "",
                )
            ),

        "article_url":
            normalize_text(
                item.get(
                    "article_url",
                    "",
                )
            ),

        "post_text":
            normalize_text(
                item.get(
                    "post_text",
                    "",
                )
            ),
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    return hashlib.sha256(
        serialized.encode(
            "utf-8"
        )
    ).hexdigest()[:16]


def build_approval_item(
    item: dict[str, Any],
) -> dict[str, Any] | None:
    """Social Queueから承認対象を作る。"""

    platform = normalize_text(
        item.get(
            "platform",
            "",
        )
    )

    post_text = normalize_text(
        item.get(
            "post_text",
            "",
        )
    )

    if not platform:
        return None

    if not post_text:
        return None

    approval_item = {
        "approval_id":
            uuid.uuid4().hex[:12],

        "created_at":
            datetime.now().isoformat(),

        "updated_at":
            datetime.now().isoformat(),

        "status":
            "pending",

        "platform":
            platform,

        "article_slug":
            normalize_text(
                item.get(
                    "article_slug",
                    "",
                )
            ),

        "article_title":
            normalize_text(
                item.get(
                    "article_title",
                    "",
                )
            ),

        "article_url":
            normalize_text(
                item.get(
                    "article_url",
                    "",
                )
            ),

        "post_text":
            post_text,

        "approved_at":
            "",

        "rejected_at":
            "",

        "decision_note":
            "",
    }

    approval_item[
        "post_hash"
    ] = build_post_hash(
        approval_item
    )

    return approval_item


def load_existing_queue(
) -> list[dict[str, Any]]:
    """既存の承認Queueを読み込む。"""

    data = load_json(
        OUTPUT_FILE
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
        if isinstance(
            item,
            dict,
        )
    ]


def already_exists(
    queue: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> bool:
    """
    同じ投稿内容がすでに承認Queueに存在するか確認する。
    """

    candidate_hash = normalize_text(
        candidate.get(
            "post_hash",
            "",
        )
    )

    for item in queue:

        existing_hash = normalize_text(
            item.get(
                "post_hash",
                "",
            )
        )

        if (
            existing_hash
            == candidate_hash
        ):
            return True

    return False


def build_approval_queue(
) -> tuple[
    list[dict[str, Any]],
    int,
]:
    """Social Queueから承認候補を追加する。"""

    social_data = load_json(
        SOCIAL_QUEUE_FILE
    )

    social_queue = social_data.get(
        "queue",
        [],
    )

    if not isinstance(
        social_queue,
        list,
    ):
        raise RuntimeError(
            "Social Queue形式が不正です。"
        )

    approval_queue = (
        load_existing_queue()
    )

    added = 0

    for item in social_queue:

        if not isinstance(
            item,
            dict,
        ):
            continue

        candidate = (
            build_approval_item(
                item
            )
        )

        if candidate is None:
            continue

        if already_exists(
            approval_queue,
            candidate,
        ):
            continue

        approval_queue.append(
            candidate
        )

        added += 1

    return (
        approval_queue,
        added,
    )


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

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def print_summary(
    queue: list[dict[str, Any]],
    added: int,
) -> None:
    """承認Queueの状態を表示する。"""

    print(
        "\n===== Atlas Social Approval Queue =====\n"
    )

    print(
        "Added："
        f"{added}"
    )

    print(
        "Queue Total："
        f"{len(queue)}"
    )

    print()

    for item in queue:

        if (
            item.get(
                "status"
            )
            != "pending"
        ):
            continue

        print(
            "--------------------------------"
        )

        print(
            "Approval ID："
            f"{item.get('approval_id', '')}"
        )

        print(
            "Platform："
            f"{item.get('platform', '')}"
        )

        print(
            "Article："
            f"{item.get('article_slug', '')}"
        )

        print()

        print(
            item.get(
                "post_text",
                "",
            )
        )

        print()


def main() -> None:
    """Social Approval Queueを更新する。"""

    queue, added = (
        build_approval_queue()
    )

    save_queue(
        queue
    )

    print_summary(
        queue,
        added,
    )


if __name__ == "__main__":
    main()