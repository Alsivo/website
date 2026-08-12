import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

RELATED_OPPORTUNITIES_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "related_affiliate_opportunities.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_article_candidates.json"
)


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{filepath.name} のJSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{filepath.name} の最上位は"
            "オブジェクトにしてください。"
        )

    return data


def build_keyword_candidates(
    program_name: str,
    category: str,
) -> list[str]:

    keywords = [
        f"{program_name} 評判",
        f"{program_name} 料金",
        f"{program_name} 口コミ",
        f"{category} おすすめ",
        f"{category} 比較",
    ]

    return list(
        dict.fromkeys(
            keyword.strip()
            for keyword in keywords
            if keyword.strip()
        )
    )


def calculate_article_priority(
    opportunity: dict[str, Any],
) -> int:

    new_fit = int(
        opportunity.get(
            "new_article_fit_score",
            0,
        )
        or 0
    )

    reward = float(
        opportunity.get(
            "reward_value",
            0,
        )
        or 0
    )

    reward_score = min(
        20,
        round(
            reward / 500
        ),
    )

    total = (
        new_fit * 0.8
        + reward_score
    )

    return min(
        100,
        round(total),
    )


def build_candidates() -> list[dict[str, Any]]:

    data = load_json(
        RELATED_OPPORTUNITIES_FILE
    )

    opportunities = data.get(
        "opportunities",
        [],
    )

    if not isinstance(
        opportunities,
        list,
    ):
        return []

    candidates = []

    for item in opportunities:

        if not isinstance(
            item,
            dict,
        ):
            continue

        if (
            item.get(
                "recommended_action"
            )
            != "CREATE_ARTICLE"
        ):
            continue

        program_name = str(
            item.get(
                "program_name",
                "",
            )
        ).strip()

        category = str(
            item.get(
                "offer_category",
                "",
            )
        ).strip()

        if not program_name:
            continue

        priority = (
            calculate_article_priority(
                item
            )
        )

        keyword_candidates = (
            build_keyword_candidates(
                program_name,
                category,
            )
        )

        candidates.append(
            {
                "program_name": program_name,
                "network": str(
                    item.get(
                        "network",
                        "",
                    )
                ),
                "source_service": str(
                    item.get(
                        "source_service",
                        "",
                    )
                ),
                "offer_category": category,
                "reward_value": float(
                    item.get(
                        "reward_value",
                        0,
                    )
                    or 0
                ),
                "currency": str(
                    item.get(
                        "currency",
                        "JPY",
                    )
                ),
                "conversion_action": str(
                    item.get(
                        "conversion_action",
                        "",
                    )
                ),
                "new_article_fit_score": int(
                    item.get(
                        "new_article_fit_score",
                        0,
                    )
                    or 0
                ),
                "article_priority": priority,
                "keyword_candidates": (
                    keyword_candidates
                ),
                "recommended_action": (
                    "EVALUATE_KEYWORDS"
                ),
            }
        )

    candidates.sort(
        key=lambda item: (
            item[
                "article_priority"
            ],
            item[
                "reward_value"
            ],
        ),
        reverse=True,
    )

    return candidates


def save_candidates(
    candidates: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "candidates": candidates,
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

    print(
        "\n===== Affiliate Article Candidates =====\n"
    )

    if not candidates:
        print(
            "現在、新規記事化候補はありません。"
        )
        return

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        print(
            f"[{index}] "
            f"{item['program_name']}"
        )

        print(
            "    category: "
            f"{item['offer_category']}"
        )

        print(
            "    network: "
            f"{item['network']}"
        )

        print(
            "    reward: "
            f"{item['reward_value']} "
            f"{item['currency']}"
        )

        print(
            "    article priority: "
            f"{item['article_priority']}"
        )

        print(
            "    keyword candidates:"
        )

        for keyword in item[
            "keyword_candidates"
        ]:
            print(
                f"      - {keyword}"
            )

        print(
            "    next: "
            "検索需要・競合性を評価"
        )

        print()


def main() -> None:

    candidates = (
        build_candidates()
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