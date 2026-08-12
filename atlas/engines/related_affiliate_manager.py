import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from engines.related_affiliate_opportunity import (
    build_opportunity,
)


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "related_affiliate_opportunities.json"
)


def load_opportunities() -> list[dict[str, Any]]:
    if not OUTPUT_FILE.exists():
        return []

    try:
        data = json.loads(
            OUTPUT_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "related_affiliate_opportunities.json "
            "のJSON形式が不正です。"
        ) from error

    opportunities = data.get(
        "opportunities",
        [],
    )

    if not isinstance(
        opportunities,
        list,
    ):
        raise RuntimeError(
            "opportunities は配列である必要があります。"
        )

    return [
        item
        for item in opportunities
        if isinstance(item, dict)
    ]


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


def find_existing_index(
    opportunities: list[dict[str, Any]],
    network: str,
    program_name: str,
) -> int | None:

    for index, item in enumerate(
        opportunities
    ):
        existing_network = str(
            item.get(
                "network",
                "",
            )
        ).strip()

        existing_program = str(
            item.get(
                "program_name",
                "",
            )
        ).strip()

        if (
            existing_network.lower()
            == network.lower()
            and existing_program.lower()
            == program_name.lower()
        ):
            return index

    return None


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "国内ASP等で発見した関連案件を"
            "Atlasへ登録します。"
        )
    )

    parser.add_argument(
        "--source-service",
        required=True,
        help=(
            "案件探索の起点となったサービス名。"
            "例: ChatGPT"
        ),
    )

    parser.add_argument(
        "--network",
        required=True,
        help=(
            "ASP・ネットワーク名。"
            "例: A8.net"
        ),
    )

    parser.add_argument(
        "--program-name",
        required=True,
        help="案件名",
    )

    parser.add_argument(
        "--program-url",
        default="",
        help="案件URL",
    )

    parser.add_argument(
        "--reward-value",
        type=float,
        default=0.0,
        help="成果報酬額",
    )

    parser.add_argument(
        "--currency",
        default="JPY",
        help="通貨",
    )

    parser.add_argument(
        "--conversion-action",
        default="",
        help=(
            "成果条件。例: 新規入会申込"
        ),
    )

    parser.add_argument(
        "--category",
        required=True,
        help=(
            "案件カテゴリ。"
            "例: 生成AIスクール"
        ),
    )

    parser.add_argument(
        "--direct-match",
        action="store_true",
        help=(
            "対象サービスそのものの案件の場合に指定。"
            "通常の関連案件では指定しません。"
        ),
    )

    parser.add_argument(
        "--notes",
        default="",
        help="メモ",
    )

    args = parser.parse_args()

    opportunity = build_opportunity(
        source_service=(
            args.source_service.strip()
        ),
        network=(
            args.network.strip()
        ),
        program_name=(
            args.program_name.strip()
        ),
        program_url=(
            args.program_url.strip()
        ),
        reward_value=(
            args.reward_value
        ),
        currency=(
            args.currency.strip()
        ),
        conversion_action=(
            args.conversion_action.strip()
        ),
        offer_category=(
            args.category.strip()
        ),
        direct_match=(
            args.direct_match
        ),
        notes=(
            args.notes.strip()
        ),
    )

    opportunity[
        "registered_at"
    ] = date.today().isoformat()

    opportunities = (
        load_opportunities()
    )

    existing_index = (
        find_existing_index(
            opportunities,
            args.network.strip(),
            args.program_name.strip(),
        )
    )

    if existing_index is None:
        opportunities.append(
            opportunity
        )
        operation = "新規登録"

    else:
        opportunities[
            existing_index
        ] = opportunity

        operation = "更新"

    opportunities.sort(
        key=lambda item: (
            int(
                item.get(
                    "new_article_fit_score",
                    0,
                )
            ),
            float(
                item.get(
                    "reward_value",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    filepath = save_opportunities(
        opportunities
    )

    print(
        "\n===== Related Affiliate Manager =====\n"
    )

    print(
        f"operation: {operation}"
    )

    print(
        "source service: "
        f"{opportunity['source_service']}"
    )

    print(
        "program: "
        f"{opportunity['program_name']}"
    )

    print(
        "network: "
        f"{opportunity['network']}"
    )

    print(
        "reward: "
        f"{opportunity['reward_value']} "
        f"{opportunity['currency']}"
    )

    print(
        "direct match: "
        f"{opportunity['direct_match']}"
    )

    print(
        "existing article fit: "
        f"{opportunity['existing_article_fit_score']}"
    )

    print(
        "new article fit: "
        f"{opportunity['new_article_fit_score']}"
    )

    print(
        "recommended action: "
        f"{opportunity['recommended_action']}"
    )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()