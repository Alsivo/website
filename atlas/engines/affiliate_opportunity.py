import json
from pathlib import Path
from typing import Any

from engines.affiliate_registry import (
    load_affiliate_registry,
)


BASE_DIR = Path(__file__).resolve().parents[1]

BLOG_DIR = (
    BASE_DIR.parent
    / "content"
    / "blog"
)

SEARCH_CONSOLE_DIR = (
    BASE_DIR
    / "data"
    / "search_console"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "affiliate_opportunities"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "affiliate_opportunities.json"
)

def load_article_metadata() -> list[dict[str, Any]]:
    """公開済みMDX記事のfrontmatterを簡易取得する。"""

    articles: list[dict[str, Any]] = []

    if not BLOG_DIR.exists():
        return articles

    for filepath in BLOG_DIR.glob("*.mdx"):
        text = filepath.read_text(
            encoding="utf-8",
        )

        if not text.startswith("---"):
            continue

        parts = text.split(
            "---",
            2,
        )

        if len(parts) < 3:
            continue

        frontmatter = parts[1]

        article = {
            "slug": filepath.stem,
            "title": "",
            "category": "",
            "tags": [],
            "content": parts[2],
        }

        for line in frontmatter.splitlines():
            stripped = line.strip()

            if stripped.startswith(
                "title:"
            ):
                article["title"] = (
                    stripped
                    .split(":", 1)[1]
                    .strip()
                    .strip('"')
                )

            elif stripped.startswith(
                "category:"
            ):
                article["category"] = (
                    stripped
                    .split(":", 1)[1]
                    .strip()
                    .strip('"')
                )

        articles.append(
            article
        )

    return articles

def load_search_console_data() -> dict[str, dict[str, float]]:
    """ページ別Search Consoleデータを読む。"""

    filepath = (
        SEARCH_CONSOLE_DIR
        / "page_performance.csv"
    )

    if not filepath.exists():
        return {}

    import csv

    result: dict[
        str,
        dict[str, float]
    ] = {}

    with filepath.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        for row in reader:
            page = str(
                row.get(
                    "page",
                    "",
                )
            ).strip()

            if not page:
                continue

            result[page] = {
                "clicks": float(
                    row.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
                "impressions": float(
                    row.get(
                        "impressions",
                        0,
                    )
                    or 0
                ),
                "ctr": float(
                    row.get(
                        "ctr",
                        0,
                    )
                    or 0
                ),
                "position": float(
                    row.get(
                        "position",
                        0,
                    )
                    or 0
                ),
            }

    return result

def detect_services_for_article(
    article: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> list[str]:
    """記事タイトルと本文から関係する登録サービスを抽出する。"""

    title = str(
        article.get(
            "title",
            "",
        )
    )

    content = str(
        article.get(
            "content",
            "",
        )
    )

    searchable_text = (
        title
        + "\n"
        + content
    ).lower()

    matched: list[str] = []

    for service_name, item in registry.items():
        candidates = [
            service_name,
            *item.get(
                "aliases",
                [],
            ),
        ]

        for candidate in candidates:
            candidate_text = str(
                candidate
            ).strip().lower()

            if (
                candidate_text
                and candidate_text
                in searchable_text
            ):
                matched.append(
                    service_name
                )
                break

    return list(
        dict.fromkeys(
            matched
        )
    )

def calculate_opportunity_score(
    article: dict[str, Any],
    services: list[str],
    search_data: dict[str, float] | None,
) -> int:
    """収益化候補としての優先度を0〜100で計算する。"""

    score = 0

    title = str(
        article.get(
            "title",
            "",
        )
    )

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
        score += 35

    if services:
        score += 30

    if search_data:
        impressions = search_data.get(
            "impressions",
            0,
        )

        clicks = search_data.get(
            "clicks",
            0,
        )

        position = search_data.get(
            "position",
            0,
        )

        if impressions >= 100:
            score += 15
        elif impressions >= 20:
            score += 10
        elif impressions > 0:
            score += 5

        if clicks > 0:
            score += 10

        if (
            position > 0
            and position <= 20
        ):
            score += 10

    return min(
        score,
        100,
    )

def find_search_data_for_slug(
    slug: str,
    search_console_data: dict[
        str,
        dict[str, float],
    ],
) -> dict[str, float] | None:
    """slugに対応するSearch Consoleデータを探す。"""

    target_suffix = (
        f"/blog/{slug}"
    )

    for page, data in (
        search_console_data.items()
    ):
        normalized_page = (
            page.rstrip("/")
        )

        if normalized_page.endswith(
            target_suffix
        ):
            return data

    return None

def build_affiliate_opportunities(
) -> dict[str, Any]:
    """全記事のアフィリエイト機会を評価する。"""

    registry = (
        load_affiliate_registry()
    )

    articles = (
        load_article_metadata()
    )

    search_console_data = (
        load_search_console_data()
    )

    result: dict[str, Any] = {}

    for article in articles:
        slug = article["slug"]

        services = (
            detect_services_for_article(
                article,
                registry,
            )
        )

        search_data = (
            find_search_data_for_slug(
                slug,
                search_console_data,
            )
        )

        score = (
            calculate_opportunity_score(
                article,
                services,
                search_data,
            )
        )

        program_candidates = []

        for service_name in services:
            item = registry[
                service_name
            ]

            program_candidates.append(
                {
                    "service": (
                        service_name
                    ),
                    "affiliate_status": (
                        item.get(
                            "affiliate_status",
                            "none",
                        )
                    ),
                    "network": (
                        item.get(
                            "network",
                            "",
                        )
                    ),
                    "program_name": (
                        item.get(
                            "program_name",
                            "",
                        )
                    ),
                }
            )

        result[slug] = {
            "title": article.get(
                "title",
                "",
            ),
            "priority": score,
            "services": services,
            "program_candidates": (
                program_candidates
            ),
            "search_console": (
                search_data
            ),
        }

    return result

def save_affiliate_opportunities(
    data: dict[str, Any],
) -> Path:
    """Affiliate Opportunity結果を保存する。"""

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

def print_affiliate_opportunities(
    data: dict[str, Any],
) -> None:
    """優先度順に候補を表示する。"""

    ranked = sorted(
        data.items(),
        key=lambda item: item[1].get(
            "priority",
            0,
        ),
        reverse=True,
    )

    print(
        "\n===== Affiliate Opportunity Report =====\n"
    )

    for slug, item in ranked:
        print(
            f"[{item['priority']}点] "
            f"{item['title']}"
        )

        services = item.get(
            "services",
            [],
        )

        print(
            "  対象サービス："
            + (
                ", ".join(services)
                if services
                else "なし"
            )
        )

        for program in item.get(
            "program_candidates",
            [],
        ):
            print(
                "  - "
                f"{program['service']} / "
                f"{program['affiliate_status']}"
            )

        print(
            f"  slug: {slug}\n"
        )

def main() -> None:
    data = (
        build_affiliate_opportunities()
    )

    filepath = (
        save_affiliate_opportunities(
            data
        )
    )

    print_affiliate_opportunities(
        data
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()