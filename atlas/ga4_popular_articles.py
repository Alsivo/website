"""GA4の記事閲覧数からALSIVOの人気記事ランキングを作成する。"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)

from ga4_affiliate_report import (
    GA4_PROPERTY_ID,
    get_date_range,
    get_ga4_credentials,
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR.parent / "src" / "data" / "popular_articles.json"


def article_slug_from_path(raw_path: str) -> str:
    path = urlsplit(raw_path).path.rstrip("/")
    prefix = "/blog/"
    if not path.startswith(prefix):
        return ""
    slug = path[len(prefix):].strip("/")
    if not slug or "/" in slug:
        return ""
    return slug


def fetch_popular_articles(
    days: int = 28,
    force_reauthorize: bool = False,
) -> tuple[list[dict[str, int | str]], str, str]:
    credentials = get_ga4_credentials(force_reauthorize=force_reauthorize)
    client = BetaAnalyticsDataClient(credentials=credentials)
    start_date, end_date = get_date_range(days)
    response = client.run_report(
        RunReportRequest(
            property=f"properties/{GA4_PROPERTY_ID}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="pagePath",
                    string_filter=Filter.StringFilter(
                        value="/blog/",
                        match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                    ),
                )
            ),
            limit=10000,
        )
    )

    views_by_slug: dict[str, int] = defaultdict(int)
    for row in response.rows:
        slug = article_slug_from_path(row.dimension_values[0].value)
        if slug:
            views_by_slug[slug] += int(row.metric_values[0].value or 0)

    articles = [
        {"slug": slug, "views": views}
        for slug, views in sorted(
            views_by_slug.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
    return articles, start_date, end_date


def save_ranking(
    articles: list[dict[str, int | str]],
    start_date: str,
    end_date: str,
) -> Path:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "generatedAt": datetime.now().isoformat(),
                "period": {"start": start_date, "end": end_date, "days": 28},
                "articles": articles,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return OUTPUT_FILE


def main(force_reauthorize: bool = False) -> None:
    articles, start_date, end_date = fetch_popular_articles(
        force_reauthorize=force_reauthorize,
    )
    output = save_ranking(articles, start_date, end_date)
    print("\n===== GA4 Popular Articles =====\n")
    print(f"Period: {start_date} - {end_date}")
    print(f"Articles: {len(articles)}")
    for index, article in enumerate(articles[:5], start=1):
        print(f"{index}. {article['slug']} / {article['views']} views")
    print(f"Saved: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GA4人気記事ランキングを更新します。")
    parser.add_argument(
        "--authorize",
        action="store_true",
        help="ブラウザでGA4へのアクセスを再認証します。",
    )
    args = parser.parse_args()
    main(force_reauthorize=args.authorize)
