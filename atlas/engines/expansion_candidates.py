import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

DECISIONS_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_decisions.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_candidates.json"
)

NEW_ARTICLE_ACTIONS = {
    "new_article",
    "comparison_article",
}

MIN_PRIORITY = 70


def load_expansion_decisions(
) -> list[dict[str, Any]]:
    """Expansion Plannerの判断を読み込む。"""

    if not DECISIONS_FILE.exists():
        raise FileNotFoundError(
            "expansion_decisions.jsonが"
            "見つかりません："
            f"{DECISIONS_FILE}"
        )

    try:
        data = json.loads(
            DECISIONS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "expansion_decisions.jsonの"
            "JSON形式が不正です。"
        ) from error

    decisions = data.get(
        "decisions",
        [],
    )

    if not isinstance(
        decisions,
        list,
    ):
        raise ValueError(
            "decisionsは配列にしてください。"
        )

    return [
        item
        for item in decisions
        if isinstance(
            item,
            dict,
        )
    ]


def build_expansion_candidates(
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """新規記事として利用可能な候補を抽出する。"""

    candidates: list[
        dict[str, Any]
    ] = []

    for item in decisions:
        action = str(
            item.get(
                "action",
                "",
            )
        ).strip()

        priority = int(
            item.get(
                "priority",
                0,
            )
            or 0
        )

        if action not in NEW_ARTICLE_ACTIONS:
            continue

        if priority < MIN_PRIORITY:
            continue

        candidates.append(
            {
                "topic":
                    str(
                        item.get(
                            "topic",
                            "",
                        )
                    ).strip(),
                "action":
                    action,
                "priority":
                    priority,
                "target_keyword":
                    str(
                        item.get(
                            "target_keyword",
                            "",
                        )
                    ).strip(),
                "suggested_title":
                    str(
                        item.get(
                            "suggested_title",
                            "",
                        )
                    ).strip(),
                "reason":
                    str(
                        item.get(
                            "reason",
                            "",
                        )
                    ).strip(),
                "related_existing_slugs":
                    item.get(
                        "related_existing_slugs",
                        [],
                    ),
                "status":
                    "ready",
            }
        )

    candidates.sort(
        key=lambda item: (
            item["priority"]
        ),
        reverse=True,
    )

    return candidates


def save_candidates(
    candidates: list[dict[str, Any]],
) -> Path:
    """新記事候補を保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "candidate_count":
                    len(candidates),
                "candidates":
                    candidates,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_candidates(
    candidates: list[dict[str, Any]],
) -> None:
    """新記事候補を表示する。"""

    print(
        "\n===== Expansion Candidates =====\n"
    )

    print(
        "記事化候補："
        f"{len(candidates)}件"
    )

    print()

    for item in candidates:
        print(
            f"[{item['priority']}点] "
            f"{item['topic']}"
        )

        print(
            "  action: "
            f"{item['action']}"
        )

        print(
            "  KW: "
            f"{item['target_keyword']}"
        )

        print()


def main() -> None:
    decisions = (
        load_expansion_decisions()
    )

    candidates = (
        build_expansion_candidates(
            decisions
        )
    )

    filepath = (
        save_candidates(
            candidates
        )
    )

    print_candidates(
        candidates
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()