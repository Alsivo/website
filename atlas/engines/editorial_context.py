import csv
import json
from pathlib import Path
from typing import Any

from config import (
    EDITORIAL_MAX_EXISTING_ARTICLES,
    EDITORIAL_MAX_KEYWORDS,
)


BASE_DIR = Path(__file__).resolve().parents[1]

WEBSITE_DIR = BASE_DIR.parent

BLOG_DIR = (
    WEBSITE_DIR
    / "content"
    / "blog"
)

SEARCH_CONSOLE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "search_console"
    / "summary.json"
)

SEARCH_CONSOLE_PAGE_QUERY_FILE = (
    BASE_DIR
    / "data"
    / "search_console"
    / "page_query_performance.csv"
)

KEYWORDS_FILE = (
    WEBSITE_DIR.parent
    / "data-content-engine"
    / "keywords.csv"
)

AFFILIATE_PROGRAMS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs.csv"
)


def load_search_console_summary() -> dict[str, Any]:
    """Search Consoleの集計結果を読み込む。"""

    if not SEARCH_CONSOLE_SUMMARY_FILE.exists():
        return {
            "available": False,
            "reason": "summary.jsonがありません。",
        }

    try:
        data = json.loads(
            SEARCH_CONSOLE_SUMMARY_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return {
            "available": False,
            "reason": "summary.jsonが壊れています。",
        }

    return {
        "available": True,
        "data": data,
    }


def load_page_query_data() -> list[dict[str, Any]]:
    """ページ×検索語のSearch Consoleデータを読む。"""

    if not SEARCH_CONSOLE_PAGE_QUERY_FILE.exists():
        return []

    rows: list[dict[str, Any]] = []

    with SEARCH_CONSOLE_PAGE_QUERY_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                rows.append(
                    {
                        "page": row.get(
                            "page",
                            "",
                        ),
                        "query": row.get(
                            "query",
                            "",
                        ),
                        "clicks": float(
                            row.get(
                                "clicks",
                                0,
                            )
                        ),
                        "impressions": float(
                            row.get(
                                "impressions",
                                0,
                            )
                        ),
                        "ctr": float(
                            row.get(
                                "ctr",
                                0,
                            )
                        ),
                        "position": float(
                            row.get(
                                "position",
                                0,
                            )
                        ),
                    }
                )
            except (TypeError, ValueError):
                continue

    return rows


def extract_frontmatter_value(
    text: str,
    key: str,
) -> str:
    """MDX frontmatterから簡易的に値を取得する。"""

    prefix = f"{key}:"

    for line in text.splitlines():
        if line.startswith(prefix):
            value = line[
                len(prefix):
            ].strip()

            return value.strip(
                "\"'"
            )

    return ""


def load_existing_articles() -> list[dict[str, str]]:
    """公開済み記事の基本情報を取得する。"""

    if not BLOG_DIR.exists():
        return []

    articles: list[dict[str, str]] = []

    for filepath in sorted(
        BLOG_DIR.glob("*.mdx")
    ):
        try:
            text = filepath.read_text(
                encoding="utf-8",
            )
        except OSError:
            continue

        articles.append(
            {
                "slug": filepath.stem,
                "title": extract_frontmatter_value(
                    text,
                    "title",
                ),
                "description":
                    extract_frontmatter_value(
                        text,
                        "description",
                    ),
                "category":
                    extract_frontmatter_value(
                        text,
                        "category",
                    ),
                "date": extract_frontmatter_value(
                    text,
                    "date",
                ),
            }
        )

    return articles[
        :EDITORIAL_MAX_EXISTING_ARTICLES
    ]


def load_unprocessed_keywords() -> list[dict[str, str]]:
    """未処理キーワードを取得する。"""

    if not KEYWORDS_FILE.exists():
        return []

    keywords: list[dict[str, str]] = []

    with KEYWORDS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            processed = str(
                row.get(
                    "processed",
                    "",
                )
            ).strip().lower()

            if processed in {
                "true",
                "1",
                "yes",
                "done",
            }:
                continue

            keyword = str(
                row.get(
                    "keyword",
                    "",
                )
            ).strip()

            if not keyword:
                continue

            keywords.append(
                {
                    "keyword": keyword,
                    "target_length": str(
                        row.get(
                            "target_length",
                            "",
                        )
                    ),
                    "related_keywords": str(
                        row.get(
                            "related_keywords",
                            "",
                        )
                    ),
                    "search_intent": str(
                        row.get(
                            "search_intent",
                            "",
                        )
                    ),
                }
            )

            if (
                len(keywords)
                >= EDITORIAL_MAX_KEYWORDS
            ):
                break

    return keywords


def load_active_affiliate_programs() -> list[dict[str, str]]:
    """activeなアフィリエイト案件だけ取得する。"""

    if not AFFILIATE_PROGRAMS_FILE.exists():
        return []

    programs: list[dict[str, str]] = []

    with AFFILIATE_PROGRAMS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if (
                str(
                    row.get(
                        "status",
                        "",
                    )
                ).strip()
                != "active"
            ):
                continue

            programs.append(
                {
                    "tool_name": str(
                        row.get(
                            "tool_name",
                            "",
                        )
                    ).strip(),
                    "network": str(
                        row.get(
                            "network",
                            "",
                        )
                    ).strip(),
                    "program_name": str(
                        row.get(
                            "program_name",
                            "",
                        )
                    ).strip(),
                    "reward_value": str(
                        row.get(
                            "reward_value",
                            "",
                        )
                    ).strip(),
                    "currency": str(
                        row.get(
                            "currency",
                            "",
                        )
                    ).strip(),
                    "conversion_action": str(
                        row.get(
                            "conversion_action",
                            "",
                        )
                    ).strip(),
                }
            )

    return programs


def build_editorial_context() -> dict[str, Any]:
    """AI編集長が判断するための全材料をまとめる。"""

    return {
        "search_console":
            load_search_console_summary(),
        "page_query_data":
            load_page_query_data(),
        "existing_articles":
            load_existing_articles(),
        "unprocessed_keywords":
            load_unprocessed_keywords(),
        "active_affiliate_programs":
            load_active_affiliate_programs(),
    }

def get_queries_for_slug(
    slug: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """特定記事に流入している検索語を取得する。"""

    rows = load_page_query_data()

    slug_path = (
        f"/blog/{slug}"
    )

    matched_rows = [
        row
        for row in rows
        if slug_path
        in str(
            row.get(
                "page",
                "",
            )
        )
    ]

    matched_rows.sort(
        key=lambda row: (
            row.get(
                "impressions",
                0,
            )
        ),
        reverse=True,
    )

    return matched_rows[:limit]