import json
from pathlib import Path
from typing import Any

from agents.expansion_planner import (
    plan_content_expansion,
)
from engines.content_expansion import (
    load_existing_articles,
)


BASE_DIR = Path(__file__).resolve().parent

QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_queue.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_decisions.json"
)


def load_expansion_queue(
) -> list[dict[str, Any]]:
    """Expansion Queueを読み込む。"""

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            "expansion_queue.jsonが"
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
            "expansion_queue.jsonの"
            "JSON形式が不正です。"
        ) from error

    candidates = data.get(
        "candidates",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        raise ValueError(
            "candidatesは配列にしてください。"
        )

    return [
        item
        for item in candidates
        if isinstance(
            item,
            dict,
        )
    ]


def save_expansion_decisions(
    data: dict[str, Any],
) -> Path:
    """AI記事拡張判断を保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_expansion_decisions(
    data: dict[str, Any],
) -> None:
    """AI判断を表示する。"""

    decisions = data.get(
        "decisions",
        [],
    )

    decisions = sorted(
        decisions,
        key=lambda item: int(
            item.get(
                "priority",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    print(
        "\n===== Expansion Decisions =====\n"
    )

    for item in decisions:
        print(
            f"[{item.get('priority', 0)}点] "
            f"{item.get('topic', '')}"
        )

        print(
            "  action: "
            f"{item.get('action', '')}"
        )

        print(
            "  KW: "
            f"{item.get('target_keyword', '')}"
        )

        print(
            "  reason: "
            f"{item.get('reason', '')}"
        )

        print()


def main() -> None:
    queue = (
        load_expansion_queue()
    )

    existing_articles = (
        load_existing_articles()
    )

    result = (
        plan_content_expansion(
            queue,
            existing_articles,
        )
    )

    filepath = (
        save_expansion_decisions(
            result
        )
    )

    print_expansion_decisions(
        result
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()