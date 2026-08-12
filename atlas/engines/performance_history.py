import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]

DAILY_REPORT_FILE = (
    BASE_DIR
    / "data"
    / "daily_report"
    / "daily_report.json"
)

PAGE_PERFORMANCE_FILE = (
    BASE_DIR
    / "data"
    / "search_console"
    / "page_performance.csv"
)

PAGE_QUERY_PERFORMANCE_FILE = (
    BASE_DIR
    / "data"
    / "search_console"
    / "page_query_performance.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "performance_history"
)

HISTORY_FILE = (
    OUTPUT_DIR
    / "history.json"
)

SNAPSHOT_DIR = (
    OUTPUT_DIR
    / "snapshots"
)


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONファイルを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """値を安全にfloatへ変換する。"""

    try:
        return float(
            value
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def url_to_slug(
    url: str,
) -> str:
    """
    Search ConsoleのURLから記事slugを取得する。

    /blog/<slug> のURLだけを記事として扱う。
    www有無は無視される。
    """

    try:
        parsed = urlparse(
            url.strip()
        )
    except ValueError:
        return ""

    path = parsed.path.strip("/")

    if not path.startswith(
        "blog/"
    ):
        return ""

    slug = path[
        len("blog/"):
    ].strip("/")

    if not slug:
        return ""

    if "/" in slug:
        return ""

    return slug


def load_csv_rows(
    filepath: Path,
) -> list[dict[str, str]]:
    """CSVファイルを安全に読み込む。"""

    if not filepath.exists():
        return []

    try:
        with filepath.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(
                file
            )

            return [
                dict(row)
                for row in reader
            ]

    except OSError:
        return []


def load_article_seo(
) -> dict[str, dict[str, Any]]:
    """
    page_performance.csvから記事別SEOデータを作る。

    同じslugが複数URLで存在する場合は統合する。
    """

    rows = load_csv_rows(
        PAGE_PERFORMANCE_FILE
    )

    aggregated: dict[
        str,
        dict[str, Any],
    ] = {}

    for row in rows:

        page = str(
            row.get(
                "page",
                "",
            )
        ).strip()

        slug = url_to_slug(
            page
        )

        if not slug:
            continue

        clicks = safe_float(
            row.get(
                "clicks",
                0,
            )
        )

        impressions = safe_float(
            row.get(
                "impressions",
                0,
            )
        )

        position = safe_float(
            row.get(
                "position",
                0,
            )
        )

        if slug not in aggregated:
            aggregated[slug] = {
                "clicks": 0.0,
                "impressions": 0.0,
                "position_weighted_sum": 0.0,
                "position_weight": 0.0,
                "urls": [],
            }

        item = aggregated[
            slug
        ]

        item["clicks"] += clicks
        item["impressions"] += impressions

        if impressions > 0:
            item[
                "position_weighted_sum"
            ] += (
                position
                * impressions
            )

            item[
                "position_weight"
            ] += impressions

        urls = item.get(
            "urls",
            [],
        )

        if (
            isinstance(
                urls,
                list,
            )
            and page
            and page not in urls
        ):
            urls.append(
                page
            )

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for slug, item in aggregated.items():

        clicks = safe_float(
            item.get(
                "clicks",
                0,
            )
        )

        impressions = safe_float(
            item.get(
                "impressions",
                0,
            )
        )

        position_weighted_sum = (
            safe_float(
                item.get(
                    "position_weighted_sum",
                    0,
                )
            )
        )

        position_weight = (
            safe_float(
                item.get(
                    "position_weight",
                    0,
                )
            )
        )

        ctr = (
            clicks / impressions
            if impressions > 0
            else 0.0
        )

        average_position = (
            position_weighted_sum
            / position_weight
            if position_weight > 0
            else 0.0
        )

        result[slug] = {
            "clicks":
                clicks,
            "impressions":
                impressions,
            "ctr":
                ctr,
            "average_position":
                average_position,
            "urls":
                item.get(
                    "urls",
                    [],
                ),
        }

    return result


def load_article_queries(
) -> dict[str, list[dict[str, Any]]]:
    """
    page_query_performance.csvから
    記事別の検索クエリを取得する。
    """

    rows = load_csv_rows(
        PAGE_QUERY_PERFORMANCE_FILE
    )

    result: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for row in rows:

        page = str(
            row.get(
                "page",
                "",
            )
        ).strip()

        slug = url_to_slug(
            page
        )

        if not slug:
            continue

        query = str(
            row.get(
                "query",
                "",
            )
        ).strip()

        if not query:
            continue

        item = {
            "query":
                query,
            "clicks":
                safe_float(
                    row.get(
                        "clicks",
                        0,
                    )
                ),
            "impressions":
                safe_float(
                    row.get(
                        "impressions",
                        0,
                    )
                ),
            "ctr":
                safe_float(
                    row.get(
                        "ctr",
                        0,
                    )
                ),
            "position":
                safe_float(
                    row.get(
                        "position",
                        0,
                    )
                ),
        }

        result.setdefault(
            slug,
            [],
        ).append(
            item
        )

    for slug in result:

        result[slug].sort(
            key=lambda item: (
                -safe_float(
                    item.get(
                        "impressions",
                        0,
                    )
                ),
                safe_float(
                    item.get(
                        "position",
                        999,
                    )
                ),
            )
        )

    return result


def build_history_entry(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Daily Reportから履歴データを作る。"""

    generated_at = str(
        report.get(
            "generated_at",
            "",
        )
    )

    try:
        date = (
            datetime.fromisoformat(
                generated_at
            )
            .date()
            .isoformat()
        )
    except ValueError:
        date = (
            datetime.now()
            .date()
            .isoformat()
        )

    system = report.get(
        "system",
        {},
    )

    if not isinstance(
        system,
        dict,
    ):
        system = {}

    editorial = report.get(
        "editorial",
        {},
    )

    if not isinstance(
        editorial,
        dict,
    ):
        editorial = {}

    seo = report.get(
        "seo",
        {},
    )

    if not isinstance(
        seo,
        dict,
    ):
        seo = {}

    revenue = report.get(
        "revenue",
        {},
    )

    if not isinstance(
        revenue,
        dict,
    ):
        revenue = {}

    portfolio = report.get(
        "portfolio",
        {},
    )

    if not isinstance(
        portfolio,
        dict,
    ):
        portfolio = {}

    investment_counts = (
        portfolio.get(
            "investment_counts",
            {},
        )
    )

    if not isinstance(
        investment_counts,
        dict,
    ):
        investment_counts = {}

    top_queries = seo.get(
        "top_queries",
        [],
    )

    if not isinstance(
        top_queries,
        list,
    ):
        top_queries = []

    top_action = revenue.get(
        "top_action",
        {},
    )

    if not isinstance(
        top_action,
        dict,
    ):
        top_action = {}

    article_seo = (
        load_article_seo()
    )

    article_queries = (
        load_article_queries()
    )

    for (
        slug,
        metrics,
    ) in article_seo.items():

        metrics[
            "top_queries"
        ] = article_queries.get(
            slug,
            [],
        )[:10]

    return {
        "date":
            date,
        "generated_at":
            generated_at,

        "system": {
            "status":
                str(
                    system.get(
                        "status",
                        "",
                    )
                ),
            "health":
                str(
                    system.get(
                        "health",
                        "",
                    )
                ),
        },

        "seo": {
            "clicks":
                safe_float(
                    seo.get(
                        "clicks",
                        0,
                    )
                ),
            "impressions":
                safe_float(
                    seo.get(
                        "impressions",
                        0,
                    )
                ),
            "ctr":
                safe_float(
                    seo.get(
                        "ctr",
                        0,
                    )
                ),
            "average_position":
                safe_float(
                    seo.get(
                        "average_position",
                        0,
                    )
                ),
            "ready_actions":
                int(
                    seo.get(
                        "ready_actions",
                        0,
                    )
                    or 0
                ),
        },

        "article_seo":
            article_seo,

        "revenue": {
            "clicks":
                int(
                    revenue.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
            "conversions":
                int(
                    revenue.get(
                        "conversions",
                        0,
                    )
                    or 0
                ),
            "revenue":
                safe_float(
                    revenue.get(
                        "revenue",
                        0,
                    )
                ),
            "conversion_rate":
                safe_float(
                    revenue.get(
                        "conversion_rate",
                        0,
                    )
                ),
            "epc":
                safe_float(
                    revenue.get(
                        "epc",
                        0,
                    )
                ),
        },

        "editorial": {
            "action":
                str(
                    editorial.get(
                        "action",
                        "",
                    )
                ),
            "priority_score":
                int(
                    editorial.get(
                        "priority_score",
                        0,
                    )
                    or 0
                ),
        },

        "portfolio": {
            "executable_count":
                int(
                    portfolio.get(
                        "executable_count",
                        0,
                    )
                    or 0
                ),
            "investment_counts":
                investment_counts,
        },

        "top_queries":
            top_queries[:5],

        "top_revenue_action":
            top_action,
    }


def load_history(
) -> dict[str, Any]:
    """既存のPerformance Historyを読み込む。"""

    if not HISTORY_FILE.exists():
        return {
            "updated_at": "",
            "entries": [],
        }

    history = load_json(
        HISTORY_FILE
    )

    entries = history.get(
        "entries",
        [],
    )

    if not isinstance(
        entries,
        list,
    ):
        entries = []

    return {
        "updated_at":
            str(
                history.get(
                    "updated_at",
                    "",
                )
            ),
        "entries":
            entries,
    }


def update_history(
    history: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any]:
    """
    履歴を更新する。

    同じ日付が存在する場合は
    最新データで置き換える。
    """

    entries = history.get(
        "entries",
        [],
    )

    if not isinstance(
        entries,
        list,
    ):
        entries = []

    target_date = entry[
        "date"
    ]

    updated_entries = []
    replaced = False

    for old_entry in entries:

        if not isinstance(
            old_entry,
            dict,
        ):
            continue

        if (
            old_entry.get(
                "date"
            )
            == target_date
        ):
            updated_entries.append(
                entry
            )
            replaced = True
        else:
            updated_entries.append(
                old_entry
            )

    if not replaced:
        updated_entries.append(
            entry
        )

    updated_entries.sort(
        key=lambda item: str(
            item.get(
                "date",
                "",
            )
        )
    )

    return {
        "updated_at":
            datetime.now().isoformat(),
        "entries":
            updated_entries,
    }


def save_history(
    history: dict[str, Any],
) -> Path:
    """Performance Historyを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    HISTORY_FILE.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return HISTORY_FILE


def save_snapshot(
    report: dict[str, Any],
    date: str,
) -> Path:
    """Daily Reportの詳細Snapshotを日付別保存する。"""

    SNAPSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot_file = (
        SNAPSHOT_DIR
        / f"{date}.json"
    )

    snapshot_file.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return snapshot_file


def print_summary(
    history: dict[str, Any],
    entry: dict[str, Any],
    snapshot_file: Path,
) -> None:
    """Performance History更新結果を表示する。"""

    entries = history.get(
        "entries",
        [],
    )

    article_seo = entry.get(
        "article_seo",
        {},
    )

    if not isinstance(
        article_seo,
        dict,
    ):
        article_seo = {}

    print(
        "\n===== Atlas Performance History =====\n"
    )

    print(
        "Date："
        f"{entry['date']}"
    )

    print(
        "History Entries："
        f"{len(entries)}"
    )

    print(
        "SEO Impressions："
        f"{entry['seo']['impressions']:.0f}"
    )

    print(
        "SEO Clicks："
        f"{entry['seo']['clicks']:.0f}"
    )

    print(
        "Tracked Articles："
        f"{len(article_seo)}"
    )

    print(
        "Affiliate Clicks："
        f"{entry['revenue']['clicks']}"
    )

    print(
        "Conversions："
        f"{entry['revenue']['conversions']}"
    )

    print(
        "Revenue："
        f"{entry['revenue']['revenue']}"
    )

    print(
        "Snapshot："
        f"{snapshot_file}"
    )

    print()


def main() -> None:
    """Performance Historyを更新する。"""

    report = load_json(
        DAILY_REPORT_FILE
    )

    if not report:
        raise RuntimeError(
            "daily_report.jsonを"
            "読み込めませんでした。"
        )

    entry = build_history_entry(
        report
    )

    history = load_history()

    history = update_history(
        history,
        entry,
    )

    history_file = save_history(
        history
    )

    snapshot_file = save_snapshot(
        report,
        entry["date"],
    )

    print_summary(
        history,
        entry,
        snapshot_file,
    )

    print(
        f"履歴保存先：{history_file}"
    )


if __name__ == "__main__":
    main()