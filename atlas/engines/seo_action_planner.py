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
    / "seo_action_plan.json"
)


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


def decide_action(
    item: dict[str, Any],
) -> tuple[str, str]:
    """実際に行うSEO施策を安全側に決定する。"""

    seo_action = str(
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

    ctr = float(
        item.get(
            "ctr",
            0,
        )
        or 0
    )

    position = float(
        item.get(
            "position",
            0,
        )
        or 0
    )

    # ----------------------------------------
    # Feedback側ですでに監視判定
    # ----------------------------------------

    if seo_action == "monitor":
        return (
            "wait",
            (
                "SEO Feedbackでmonitor判定です。"
                "検索データが不足しているため、"
                "記事変更は行いません。"
            ),
        )

    # ----------------------------------------
    # 上位記事を保護
    # ----------------------------------------

    if seo_action == "keep":
        return (
            "wait",
            (
                "SEO Feedbackでkeep判定です。"
                "現在の評価を維持するため、"
                "大幅な変更は行いません。"
            ),
        )

    # ----------------------------------------
    # 共通のデータ不足安全弁
    # ----------------------------------------

    if impressions < 20:
        return (
            "wait",
            (
                "表示回数が20未満のため、"
                "大幅な変更は行わず"
                "Search Consoleデータの"
                "蓄積を待ちます。"
            ),
        )

    # ----------------------------------------
    # CTR改善
    # ----------------------------------------

    if (
        seo_action == "improve_ctr"
        and 1 <= position <= 10
        and ctr < 0.02
    ):
        return (
            "title_only",
            (
                "検索順位は良好ですがCTRが低いため、"
                "本文は維持し、タイトルと"
                "descriptionの改善を優先します。"
            ),
        )

    # ----------------------------------------
    # 1ページ目から上位化
    # ----------------------------------------

    if seo_action == "strengthen":
        return (
            "strengthen",
            (
                "1ページ目に表示されているため、"
                "全面リライトは避け、"
                "検索意図への補足・内部リンク・"
                "FAQ等の部分強化を行います。"
            ),
        )

    # ----------------------------------------
    # コンテンツ改善
    # ----------------------------------------

    if seo_action == "improve_content":
        if (
            impressions >= 50
            and position > 10
        ):
            return (
                "rewrite",
                (
                    "十分な検索露出がありながら"
                    "順位が低いため、"
                    "検索意図・構成・本文を"
                    "再設計する候補です。"
                ),
            )

        return (
            "strengthen",
            (
                "改善余地はありますが、"
                "全面リライトにはデータが"
                "まだ十分ではないため、"
                "部分的な強化を優先します。"
            ),
        )

    # ----------------------------------------
    # テーマ再検討
    # ----------------------------------------

    if seo_action == "rethink":
        if impressions >= 50:
            return (
                "rewrite",
                (
                    "十分な検索露出がある一方で"
                    "順位が非常に低いため、"
                    "検索意図から記事全体を"
                    "再設計する候補です。"
                ),
            )

        return (
            "wait",
            (
                "順位は低いものの"
                "検索データがまだ少ないため、"
                "現時点では記事テーマを"
                "変更せず推移を観察します。"
            ),
        )

    return (
        "wait",
        "現時点では変更を行いません。",
    )


def build_action_plan(
    feedback: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """全記事のSEO Action Planを作成する。"""

    plans: list[
        dict[str, Any]
    ] = []

    for item in feedback:
        (
            planned_action,
            action_reason,
        ) = decide_action(
            item
        )

        plans.append(
            {
                "slug": str(
                    item.get(
                        "slug",
                        "",
                    )
                ).strip(),
                "seo_priority": int(
                    item.get(
                        "priority",
                        0,
                    )
                    or 0
                ),
                "seo_action": str(
                    item.get(
                        "action",
                        "",
                    )
                ).strip(),
                "planned_action":
                    planned_action,
                "impressions": float(
                    item.get(
                        "impressions",
                        0,
                    )
                    or 0
                ),
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
                "action_reason":
                    action_reason,
                "top_queries":
                    item.get(
                        "top_queries",
                        [],
                    ),
                "status":
                    (
                        "waiting"
                        if planned_action == "wait"
                        else "ready"
                    ),
            }
        )

    plans.sort(
        key=lambda item: (
            item[
                "planned_action"
            ] != "wait",
            item[
                "seo_priority"
            ],
            item[
                "impressions"
            ],
        ),
        reverse=True,
    )

    return plans


def save_action_plan(
    plans: list[dict[str, Any]],
) -> Path:
    """SEO Action Planを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "plans":
                    plans,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def main() -> None:
    feedback = load_feedback()

    plans = build_action_plan(
        feedback
    )

    filepath = save_action_plan(
        plans
    )

    print(
        "\n===== SEO Action Plan =====\n"
    )

    if not plans:
        print(
            "現在、SEO評価対象はありません。"
        )

        print(
            "\n保存先："
            f"{filepath}"
        )

        return

    for item in plans:
        print(
            f"[{item['seo_priority']}点] "
            f"{item['slug']}"
        )

        print(
            "  SEO判定: "
            f"{item['seo_action']}"
        )

        print(
            "  実行方針: "
            f"{item['planned_action']}"
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
            "  reason: "
            f"{item['action_reason']}"
        )

        print()

    print(
        "保存先："
        f"{filepath}"
    )


if __name__ == "__main__":
    main()