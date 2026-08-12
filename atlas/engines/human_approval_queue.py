import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

OPTIMIZATION_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "optimization"
    / "optimization_decision.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "human_approval"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "approval_queue.json"
)


HUMAN_ACTION_MODES = {
    "human_action",
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


def normalize_text(
    value: Any,
) -> str:
    """比較用文字列へ正規化する。"""

    return str(
        value
        if value is not None
        else ""
    ).strip()


def build_identity_key(
    item: dict[str, Any],
) -> tuple[
    str,
    str,
    str,
    str,
]:
    """
    Human Actionの同一案件判定キーを作る。

    action / source / target_type / target
    が一致すれば同一対象とみなす。
    """

    return (
        normalize_text(
            item.get(
                "action",
                "",
            )
        ),
        normalize_text(
            item.get(
                "source",
                "",
            )
        ),
        normalize_text(
            item.get(
                "target_type",
                "",
            )
        ),
        normalize_text(
            item.get(
                "target",
                "",
            )
        ),
    )


def build_decision_fingerprint(
    item: dict[str, Any],
) -> str:
    """
    Human Actionの判断内容を識別するFingerprintを作る。

    rejected案件でも、
    判断内容が変化した場合は再申請できるようにする。
    """

    payload = {
        "action":
            normalize_text(
                item.get(
                    "action",
                    "",
                )
            ),

        "source":
            normalize_text(
                item.get(
                    "source",
                    "",
                )
            ),

        "target_type":
            normalize_text(
                item.get(
                    "target_type",
                    "",
                )
            ),

        "target":
            normalize_text(
                item.get(
                    "target",
                    "",
                )
            ),

        "priority":
            int(
                item.get(
                    "priority",
                    0,
                )
                or 0
            ),

        "execution_mode":
            normalize_text(
                item.get(
                    "execution_mode",
                    "",
                )
            ),

        "reason":
            normalize_text(
                item.get(
                    "reason",
                    "",
                )
            ),

        "recommended_action":
            normalize_text(
                item.get(
                    "recommended_action",
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
    decision: dict[str, Any],
) -> dict[str, Any] | None:
    """Optimization Decisionから承認待ち項目を作る。"""

    selected = decision.get(
        "selected",
        {},
    )

    if not isinstance(
        selected,
        dict,
    ):
        return None

    action = normalize_text(
        selected.get(
            "action",
            "",
        )
    )

    target = normalize_text(
        selected.get(
            "target",
            "",
        )
    )

    execution_mode = normalize_text(
        selected.get(
            "execution_mode",
            "",
        )
    )

    execution_allowed = bool(
        selected.get(
            "execution_allowed",
            False,
        )
    )

    if not action:
        return None

    if execution_mode not in HUMAN_ACTION_MODES:
        return None

    if execution_allowed:
        return None

    item = {
        "approval_id":
            uuid.uuid4().hex[:12],

        "created_at":
            datetime.now().isoformat(),

        "status":
            "pending",

        "action":
            action,

        "source":
            normalize_text(
                selected.get(
                    "source",
                    "",
                )
            ),

        "target_type":
            normalize_text(
                selected.get(
                    "target_type",
                    "",
                )
            ),

        "target":
            target,

        "priority":
            int(
                selected.get(
                    "priority",
                    0,
                )
                or 0
            ),

        "execution_mode":
            execution_mode,

        "execution_allowed":
            execution_allowed,

        "reason":
            normalize_text(
                selected.get(
                    "reason",
                    "",
                )
            ),

        "recommended_action":
            normalize_text(
                selected.get(
                    "recommended_action",
                    "",
                )
            ),

        "approved_at":
            "",

        "rejected_at":
            "",

        "decision_note":
            "",
    }

    item[
        "decision_fingerprint"
    ] = build_decision_fingerprint(
        item
    )

    return item


def load_existing_queue(
) -> list[dict[str, Any]]:
    """既存の承認キューを読み込む。"""

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

    normalized_queue = []

    for item in queue:
        if not isinstance(
            item,
            dict,
        ):
            continue

        normalized_item = dict(
            item
        )

        if not normalize_text(
            normalized_item.get(
                "approval_id",
                "",
            )
        ):
            normalized_item[
                "approval_id"
            ] = uuid.uuid4().hex[:12]

        if not normalize_text(
            normalized_item.get(
                "decision_fingerprint",
                "",
            )
        ):
            normalized_item[
                "decision_fingerprint"
            ] = build_decision_fingerprint(
                normalized_item
            )

        normalized_queue.append(
            normalized_item
        )

    return normalized_queue


def find_existing_match(
    queue: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Candidateと既存Queueを比較する。

    優先順位：
    1. approved
    2. pending
    3. rejected（同一Fingerprintのみ）

    approved済みの同一案件が存在する場合は、
    rejectedやpendingより必ず優先する。
    """

    candidate_identity = (
        build_identity_key(
            candidate
        )
    )

    candidate_fingerprint = (
        normalize_text(
            candidate.get(
                "decision_fingerprint",
                "",
            )
        )
    )

    approved_match: dict[str, Any] | None = None
    pending_match: dict[str, Any] | None = None
    rejected_match: dict[str, Any] | None = None

    for item in queue:

        if (
            build_identity_key(
                item
            )
            != candidate_identity
        ):
            continue

        status = (
            normalize_text(
                item.get(
                    "status",
                    "",
                )
            ).lower()
        )

        if status == "approved":
            approved_match = item
            continue

        if status == "pending":
            pending_match = item
            continue

        if status == "rejected":

            existing_fingerprint = (
                normalize_text(
                    item.get(
                        "decision_fingerprint",
                        "",
                    )
                )
            )

            if not existing_fingerprint:
                existing_fingerprint = (
                    build_decision_fingerprint(
                        item
                    )
                )

            if (
                existing_fingerprint
                == candidate_fingerprint
            ):
                rejected_match = item

    if approved_match is not None:
        return approved_match

    if pending_match is not None:
        return pending_match

    if rejected_match is not None:
        return rejected_match

    return None


def update_queue(
    queue: list[dict[str, Any]],
    candidate: dict[str, Any] | None,
) -> tuple[
    list[dict[str, Any]],
    bool,
    str,
]:
    """承認キューへ新規候補を追加する。"""

    if candidate is None:
        return (
            queue,
            False,
            "NO_CANDIDATE",
        )

    existing = find_existing_match(
        queue,
        candidate,
    )

    if existing is not None:

        existing_status = (
            normalize_text(
                existing.get(
                    "status",
                    "",
                )
            ).lower()
        )

        if existing_status == "pending":
            reason = (
                "DUPLICATE_PENDING"
            )

        elif existing_status == "approved":
            reason = (
                "ALREADY_APPROVED"
            )

        elif existing_status == "rejected":
            reason = (
                "SAME_REJECTED_DECISION"
            )

        else:
            reason = (
                "DUPLICATE"
            )

        return (
            queue,
            False,
            reason,
        )

    queue.append(
        candidate
    )

    queue.sort(
        key=lambda item: (
            int(
                item.get(
                    "priority",
                    0,
                )
                or 0
            ),
            normalize_text(
                item.get(
                    "created_at",
                    "",
                )
            ),
        ),
        reverse=True,
    )

    return (
        queue,
        True,
        "ADDED",
    )


def save_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """承認キューを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pending_count = sum(
        1
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
        == "pending"
    )

    approved_count = sum(
        1
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
        == "approved"
    )

    rejected_count = sum(
        1
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
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
    queue: list[dict[str, Any]],
    added: bool,
    record_reason: str,
) -> None:
    """承認キューの状態を表示する。"""

    pending = [
        item
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
        == "pending"
    ]

    approved = [
        item
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
        == "approved"
    ]

    rejected = [
        item
        for item in queue
        if normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()
        == "rejected"
    ]

    print(
        "\n===== Atlas Human Approval Queue =====\n"
    )

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

    print(
        "Record："
        + (
            "ADDED"
            if added
            else "SKIP"
        )
    )

    if not added:
        print(
            "Reason："
            f"{record_reason}"
        )

    if pending:
        print(
            "\n--- TOP PENDING ---"
        )

        for index, item in enumerate(
            pending[:10],
            start=1,
        ):
            print(
                f"[{index}] "
                f"{item.get('action', '')} / "
                f"{item.get('target', '')} / "
                f"priority="
                f"{item.get('priority', 0)} / "
                f"id="
                f"{item.get('approval_id', '')}"
            )


def main() -> None:
    """Human Approval Queueを更新する。"""

    decision = load_json(
        OPTIMIZATION_DECISION_FILE
    )

    if not decision:
        raise RuntimeError(
            "Optimization Decisionを"
            "読み込めませんでした。"
        )

    candidate = (
        build_approval_item(
            decision
        )
    )

    queue = (
        load_existing_queue()
    )

    (
        queue,
        added,
        record_reason,
    ) = update_queue(
        queue,
        candidate,
    )

    filepath = (
        save_queue(
            queue
        )
    )

    print_summary(
        queue,
        added,
        record_reason,
    )

    print()

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()