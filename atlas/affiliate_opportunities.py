import json
from pathlib import Path

from agents.affiliate_opportunity_editor import (
    evaluate_affiliate_opportunities,
)
from engines.affiliate_opportunity import (
    build_affiliate_opportunities,
    save_affiliate_opportunities,
)


BASE_DIR = Path(__file__).resolve().parent

AI_OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "affiliate_opportunities"
)

AI_OUTPUT_FILE = (
    AI_OUTPUT_DIR
    / "affiliate_opportunity_decisions.json"
)


def save_ai_decisions(
    data: dict,
) -> Path:
    """AIによるAffiliate Opportunity判断を保存する。"""

    AI_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    AI_OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return AI_OUTPUT_FILE


def print_ai_decisions(
    data: dict,
) -> None:
    """AI判断結果を優先度順に表示する。"""

    decisions = data.get(
        "decisions",
        [],
    )

    ranked = sorted(
        decisions,
        key=lambda item: item.get(
            "priority",
            0,
        ),
        reverse=True,
    )

    print(
        "\n===== Affiliate Opportunity AI =====\n"
    )

    for item in ranked:
        print(
            f"[{item['priority']}点] "
            f"{item['slug']}"
        )

        print(
            f"  action: {item['action']}"
        )

        print(
            "  service: "
            + (
                item["service"]
                if item["service"]
                else "なし"
            )
        )

        print(
            f"  reason: {item['reason']}\n"
        )


def main() -> None:
    print(
        "[Affiliate Opportunity] "
        "候補を作成します。"
    )

    opportunities = (
        build_affiliate_opportunities()
    )

    save_affiliate_opportunities(
        opportunities
    )

    decisions = (
        evaluate_affiliate_opportunities(
            opportunities
        )
    )

    filepath = save_ai_decisions(
        decisions
    )

    print_ai_decisions(
        decisions
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()