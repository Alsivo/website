import json
from pathlib import Path
from typing import Any

from engines.affiliate_registry import (
    load_affiliate_registry,
)
from engines.affiliate_opportunity import (
    build_affiliate_opportunities,
)


BASE_DIR = Path(__file__).resolve().parents[1]

PROGRAM_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

PROGRAM_CANDIDATES_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_registration_candidates.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "monetization"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "monetization_matches.json"
)

def load_program_results(
) -> dict[str, dict[str, Any]]:
    """Phase 34の案件調査結果をサービス別に読み込む。"""

    if not PROGRAM_RESULTS_FILE.exists():
        return {}

    try:
        data = json.loads(
            PROGRAM_RESULTS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "program_research_results.jsonの"
            "JSON形式が不正です。"
        ) from error

    programs = data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        raise ValueError(
            "program_research_results.jsonの"
            "programsは配列にしてください。"
        )

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in programs:
        if not isinstance(
            item,
            dict,
        ):
            continue

        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        result[service] = item

    return result

def load_program_classifications(
) -> dict[str, str]:
    """
    Phase 34の最終分類をサービス別に読み込む。
    """

    if not PROGRAM_CANDIDATES_FILE.exists():
        return {}

    try:
        data = json.loads(
            PROGRAM_CANDIDATES_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "program_registration_candidates.jsonの"
            "JSON形式が不正です。"
        ) from error

    result: dict[str, str] = {}

    section_map = {
        "registration_candidates": (
            "candidate"
        ),
        "needs_review": (
            "needs_review"
        ),
        "not_found": (
            "not_found"
        ),
    }

    for section_name, status in (
        section_map.items()
    ):
        items = data.get(
            section_name,
            [],
        )

        if not isinstance(
            items,
            list,
        ):
            continue

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            service = str(
                item.get(
                    "service",
                    "",
                )
            ).strip()

            if not service:
                continue

            # Gemini (Google) のような
            # 調査時の補足表記をRegistry名へ寄せる
            if service.startswith(
                "Gemini"
            ):
                service = "Gemini"

            result[service] = status

    return result

def get_monetization_status(
    service: str,
    registry: dict[str, dict[str, Any]],
    program_results: dict[
        str,
        dict[str, Any],
    ],
    program_classifications: dict[
        str,
        str,
    ],
) -> str:
    """サービスの現在の収益化状態を判定する。"""

    registry_item = registry.get(
        service,
        {},
    )

    affiliate_status = str(
        registry_item.get(
            "affiliate_status",
            "none",
        )
    ).strip()

    affiliate_url = str(
        registry_item.get(
            "affiliate_url",
            "",
        )
    ).strip()

    # 実際に承認済み案件が登録されている
    if (
        affiliate_status == "active"
        and affiliate_url
    ):
        return "active"

    # Phase 34の最終分類を最優先
    classified_status = (
        program_classifications.get(
            service
        )
    )

    if classified_status:
        return classified_status

    # 最終分類されていない場合だけ、
    # Web調査実施済みか確認
    research = program_results.get(
        service
    )

    if research is None:
        return "unresearched"

    # 調査済みだがSelector結果がない場合は
    # 安全側へ倒して要確認
    return "needs_review"
    """サービスの現在の収益化状態を判定する。"""

    registry_item = registry.get(
        service,
        {},
    )

    affiliate_status = str(
        registry_item.get(
            "affiliate_status",
            "none",
        )
    ).strip()

    affiliate_url = str(
        registry_item.get(
            "affiliate_url",
            "",
        )
    ).strip()

    # 既に実案件が登録済み
    if (
        affiliate_status == "active"
        and affiliate_url
    ):
        return "active"

    research = program_results.get(
        service
    )

    # まだWeb調査していない
    if research is None:
        return "unresearched"

    program_found = research.get(
        "program_found"
    )

    commission = str(
        research.get(
            "commission",
            "",
        )
    ).strip()

    # 成果報酬または報酬条件まで確認済み
    if (
        program_found is True
        and commission
    ):
        return "candidate"

    # 何らかの制度はあるが
    # 収益化可否が確定していない
    if program_found is True:
        return "needs_review"

    return "not_found"

def calculate_match_score(
    article: dict[str, Any],
    service: str,
    monetization_status: str,
) -> int:
    """記事とサービスの収益化マッチ度を0〜100で計算する。"""

    score = 0

    title = str(
        article.get(
            "title",
            "",
        )
    )

    services = article.get(
        "services",
        [],
    )

    search_console = article.get(
        "search_console"
    )

    # 記事内でサービスが検出されている
    if service in services:
        score += 30

    # タイトルにサービス名が直接入っている
    if (
        service.lower()
        in title.lower()
    ):
        score += 20

    commercial_terms = [
        "料金",
        "価格",
        "比較",
        "おすすめ",
        "プラン",
        "選び方",
    ]

    if any(
        term in title
        for term in commercial_terms
    ):
        score += 15

    # 実案件が既にある
    if monetization_status == "active":
        score += 25

    elif monetization_status == "candidate":
        score += 20

    elif monetization_status == "needs_review":
        score += 8

    elif monetization_status == "not_found":
        score -= 10

    # Search Console評価
    if isinstance(
        search_console,
        dict,
    ):
        impressions = float(
            search_console.get(
                "impressions",
                0,
            )
            or 0
        )

        clicks = float(
            search_console.get(
                "clicks",
                0,
            )
            or 0
        )

        position = float(
            search_console.get(
                "position",
                0,
            )
            or 0
        )

        if impressions >= 100:
            score += 10
        elif impressions >= 20:
            score += 7
        elif impressions > 0:
            score += 3

        if clicks > 0:
            score += 5

        if (
            position > 0
            and position <= 20
        ):
            score += 5

    return max(
        0,
        min(
            score,
            100,
        ),
    )

def build_monetization_matches(
) -> dict[str, Any]:
    """既存記事とサービスの収益化マッチを作る。"""

    registry = (
        load_affiliate_registry()
    )

    program_results = (
        load_program_results()
    )

    program_classifications = (
        load_program_classifications()
    )

    article_opportunities = (
        build_affiliate_opportunities()
    )

    matches: list[
        dict[str, Any]
    ] = []

    for slug, article in (
        article_opportunities.items()
    ):
        services = article.get(
            "services",
            [],
        )

        if not isinstance(
            services,
            list,
        ):
            continue

        for service in services:
            if service not in registry:
                continue

            status = (
                get_monetization_status(
                    service,
                    registry,
                    program_results,
                    program_classifications,
                )
            )

            score = (
                calculate_match_score(
                    article,
                    service,
                    status,
                )
            )

            matches.append(
                {
                    "slug": slug,
                    "title": article.get(
                        "title",
                        "",
                    ),
                    "service": service,
                    "match_score": score,
                    "monetization_status": (
                        status
                    ),
                    "search_console": (
                        article.get(
                            "search_console"
                        )
                    ),
                }
            )

    matches.sort(
        key=lambda item: item[
            "match_score"
        ],
        reverse=True,
    )

    return {
        "matches": matches,
    }

def save_monetization_matches(
    data: dict[str, Any],
) -> Path:
    """マッチ結果をJSON保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE

def print_monetization_matches(
    data: dict[str, Any],
) -> None:
    """収益化マッチ候補を表示する。"""

    matches = data.get(
        "matches",
        [],
    )

    print(
        "\n===== Monetization Match Report =====\n"
    )

    if not matches:
        print(
            "収益化マッチ候補はありません。"
        )
        return

    for item in matches:
        print(
            f"[{item['match_score']}点] "
            f"{item['title']}"
        )

        print(
            f"  service: "
            f"{item['service']}"
        )

        print(
            "  monetization: "
            f"{item['monetization_status']}"
        )

        print(
            f"  slug: {item['slug']}"
        )

        print()

def main() -> None:
    data = (
        build_monetization_matches()
    )

    filepath = (
        save_monetization_matches(
            data
        )
    )

    print_monetization_matches(
        data
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()