import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

SEO_FEEDBACK_FILE = (
    BASE_DIR
    / "data"
    / "seo_feedback"
    / "seo_feedback.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "seo_feedback"
    / "seo_improvement_queue.json"
)


ACTION_SCORE_BONUS = {
    "improve_ctr": 25,
    "improve_content": 20,
    "strengthen": 15,
    "rethink": 10,
}


def load_feedback(
) -> list[dict[str, Any]]:
    """SEO Feedbackを読み込む。"""

    if not SEO_FEEDBACK_FILE.exists():
        return []

    try:
        data = json.loads(
            SEO_FEEDBACK_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "seo_feedback.jsonの"
            "JSON形式が不正です。"
        ) from error

    feedback = data.get(
        "feedback",
        [],
    )

    if not isinstance(
        feedback,
        list,
    ):
        raise ValueError(
            "feedbackは配列にしてください。"
        )

    return [
        item
        for item in feedback
        if isinstance(
            item,
            dict,
        )
    ]


def calculate_queue_score(
    item: dict[str, Any],
) -> int:
    """改善Queue用の優先度を計算する。"""

    base_priority = int(
        item.get(
            "priority",
            0,
        )
        or 0
    )

    action = str(
        item.get(
            "action",
            "",
        )
    ).strip()

    impressions = float(
        item.get(
            "impressions",
            0,
        )
        or 0
    )

    clicks = float(
        item.get(
            "clicks",
            0,
        )
        or 0
    )

    score = base_priority

    score += ACTION_SCORE_BONUS.get(
        action,
        0,
    )

    if impressions >= 100:
        score += 20
    elif impressions >= 50:
        score += 15
    elif impressions >= 20:
        score += 10
    elif impressions >= 10:
        score += 5

    if clicks > 0:
        score += 5

    return min(
        score,
        100,
    )


def build_improvement_queue(
    feedback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """実際に改善検討する記事だけ抽出する。"""

    queue: list[
        dict[str, Any]
    ] = []

    allowed_actions = {
        "improve_ctr",
        "improve_content",
        "strengthen",
        "rethink",
    }

    for item in feedback:
        action = str(
            item.get(
                "action",
                "",
            )
        ).strip()

        if action not in (
            allowed_actions
        ):
            continue

        impressions = float(
            item.get(
                "impressions",
                0,
            )
            or 0
        )

        # データ不足の記事は
        # 改善Queueへ入れない
        if impressions < 5:
            continue

        queue_score = (
            calculate_queue_score(
                item
            )
        )

        queue.append(
            {
                "slug": str(
                    item.get(
                        "slug",
                        "",
                    )
                ).strip(),
                "action":
                    action,
                "queue_score":
                    queue_score,
                "seo_priority": int(
                    item.get(
                        "priority",
                        0,
                    )
                    or 0
                ),
                "impressions":
                    impressions,
                "clicks": float(
                    item.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
                "ctr": float(
                    item.get(
                        "ctr",
                        0,
                    )
                    or 0
                ),
                "position": float(
                    item.get(
                        "position",
                        0,
                    )
                    or 0
                ),
                "reason": str(
                    item.get(
                        "reason",
                        "",
                    )
                ).strip(),
                "pages":
                    item.get(
                        "pages",
                        [],
                    ),
                "top_queries":
                    item.get(
                        "top_queries",
                        [],
                    ),
                "status":
                    "ready",
            }
        )

    queue.sort(
        key=lambda item: (
            item[
                "queue_score"
            ],
            item[
                "impressions"
            ],
        ),
        reverse=True,
    )

    return queue


def save_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """SEO Improvement Queueを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "queue":
                    queue,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def main() -> None:
    feedback = (
        load_feedback()
    )

    queue = (
        build_improvement_queue(
            feedback
        )
    )

    filepath = save_queue(
        queue
    )

    print(
        "\n===== SEO Improvement Queue =====\n"
    )

    if not queue:
        print(
            "現在、SEO改善対象はありません。"
        )

        print(
            "\n保存先："
            f"{filepath}"
        )

        return

    print(
        f"改善候補：{len(queue)}件\n"
    )

    for item in queue:
        print(
            f"[{item['queue_score']}点] "
            f"{item['slug']}"
        )

        print(
            "  action: "
            f"{item['action']}"
        )

        print(
            "  impressions: "
            f"{item['impressions']}"
        )

        print(
            "  position: "
            f"{item['position']:.2f}"
        )

        print(
            "  CTR: "
            f"{item['ctr']:.2%}"
        )

        print(
            "  reason: "
            f"{item['reason']}"
        )

        queries = item.get(
            "top_queries",
            [],
        )

        if queries:
            print(
                "  queries:"
            )

            for query in queries[:5]:
                print(
                    "    - "
                    f"{query.get('query', '')} "
                    "(順位 "
                    f"{float(query.get('position', 0)):.1f}"
                    ")"
                )

        print()

    print(
        "保存先："
        f"{filepath}"
    )


if __name__ == "__main__":
    main()