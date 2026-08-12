import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "related_affiliate_opportunities.json"
)


def calculate_existing_article_fit(
    source_service: str,
    offer_name: str,
    offer_category: str,
) -> int:

    text = (
        f"{source_service} "
        f"{offer_name} "
        f"{offer_category}"
    ).lower()

    score = 30

    if source_service.lower() in text:
        score += 10

    if any(
        keyword in text
        for keyword in [
            "スクール",
            "講座",
            "camp",
            "学習",
            "教育",
        ]
    ):
        score -= 10

    return max(
        0,
        min(
            100,
            score,
        ),
    )


def calculate_new_article_fit(
    reward_value: float,
    offer_category: str,
) -> int:

    score = 50

    if reward_value >= 5000:
        score += 25

    elif reward_value >= 2000:
        score += 15

    elif reward_value >= 1000:
        score += 10

    category = offer_category.lower()

    if any(
        keyword in category
        for keyword in [
            "ai",
            "生成ai",
            "スクール",
            "saas",
            "プログラミング",
            "動画",
            "デザイン",
        ]
    ):
        score += 15

    return min(
        100,
        score,
    )


def decide_action(
    direct_match: bool,
    existing_article_fit: int,
    new_article_fit: int,
) -> str:

    if direct_match:
        if existing_article_fit >= 60:
            return "APPLY_EXISTING"

        return "REVIEW_EXISTING"

    if new_article_fit >= 75:
        return "CREATE_ARTICLE"

    if existing_article_fit >= 60:
        return "REVIEW_EXISTING"

    return "WAIT"


def build_opportunity(
    source_service: str,
    network: str,
    program_name: str,
    program_url: str,
    reward_value: float,
    currency: str,
    conversion_action: str,
    offer_category: str,
    direct_match: bool,
    notes: str = "",
) -> dict[str, Any]:

    existing_article_fit = (
        calculate_existing_article_fit(
            source_service,
            program_name,
            offer_category,
        )
    )

    new_article_fit = (
        calculate_new_article_fit(
            reward_value,
            offer_category,
        )
    )

    action = decide_action(
        direct_match,
        existing_article_fit,
        new_article_fit,
    )

    return {
        "source_service": source_service,
        "network": network,
        "program_name": program_name,
        "program_url": program_url,
        "reward_value": reward_value,
        "currency": currency,
        "conversion_action": conversion_action,
        "offer_category": offer_category,
        "direct_match": direct_match,
        "existing_article_fit_score": (
            existing_article_fit
        ),
        "new_article_fit_score": (
            new_article_fit
        ),
        "recommended_action": action,
        "notes": notes,
    }


def save_opportunities(
    opportunities: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "opportunities": opportunities,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_opportunities(
    opportunities: list[dict[str, Any]],
) -> None:

    print(
        "\n===== Related Affiliate Opportunities =====\n"
    )

    if not opportunities:
        print(
            "関連案件候補はありません。"
        )
        return

    for index, item in enumerate(
        opportunities,
        start=1,
    ):

        print(
            f"[{index}] "
            f"{item['program_name']}"
        )

        print(
            "    source service: "
            f"{item['source_service']}"
        )

        print(
            "    ASP: "
            f"{item['network']}"
        )

        print(
            "    reward: "
            f"{item['reward_value']} "
            f"{item['currency']}"
        )

        print(
            "    direct_match: "
            f"{item['direct_match']}"
        )

        print(
            "    existing article fit: "
            f"{item['existing_article_fit_score']}"
        )

        print(
            "    new article fit: "
            f"{item['new_article_fit_score']}"
        )

        print(
            "    action: "
            f"{item['recommended_action']}"
        )

        print()


def main() -> None:

    # Phase E4-3 動作確認用。
    # A8.netでChatGPT検索時に見つかった
    # DMM生成AI CAMPを関連案件として登録する。
    opportunities = [
        build_opportunity(
            source_service="ChatGPT",
            network="A8.net",
            program_name="DMM 生成AI CAMP",
            program_url="",
            reward_value=7519,
            currency="JPY",
            conversion_action="新規入会申込",
            offer_category="生成AIスクール",
            direct_match=False,
            notes=(
                "A8.netでChatGPT検索時に発見。"
                "ChatGPT本体の案件ではなく、"
                "生成AI学習サービスの関連案件。"
                "無料セミナー予約報酬も別途あり。"
            ),
        )
    ]

    filepath = (
        save_opportunities(
            opportunities
        )
    )

    print_opportunities(
        opportunities
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()