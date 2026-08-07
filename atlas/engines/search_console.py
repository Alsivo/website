import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from google.auth.transport.requests import (
    Request,
)
from google.oauth2.credentials import (
    Credentials,
)
from google_auth_oauthlib.flow import (
    InstalledAppFlow,
)
from googleapiclient.discovery import (
    build,
)

from config import (
    SEARCH_CONSOLE_LOOKBACK_DAYS,
    SEARCH_CONSOLE_ROW_LIMIT,
    SEARCH_CONSOLE_SITE_URL,
)


BASE_DIR = Path(__file__).resolve().parents[1]

CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials"
    / "search_console_client_secret.json"
)

TOKEN_FILE = (
    BASE_DIR
    / "token.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "search_console"
)

SCOPES = [
    "https://www.googleapis.com/auth/"
    "webmasters.readonly"
]


def get_search_console_service():
    """Search Console APIの認証済みサービスを作る。"""

    credentials = None

    if TOKEN_FILE.exists():
        credentials = (
            Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES,
            )
        )

    if (
        credentials
        and credentials.expired
        and credentials.refresh_token
    ):
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Search Console APIの認証ファイルが"
                "見つかりません："
                f"{CREDENTIALS_FILE}"
            )

        flow = (
            InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES,
            )
        )

        credentials = flow.run_local_server(
            port=0,
        )

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return build(
        "searchconsole",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )


def get_date_range() -> tuple[str, str]:
    """
    Search Consoleから取得する日付範囲を返す。

    データ確定を考慮して、終了日は3日前にする。
    """

    end_date = (
        date.today()
        - timedelta(days=3)
    )

    start_date = (
        end_date
        - timedelta(
            days=(
                SEARCH_CONSOLE_LOOKBACK_DAYS
                - 1
            )
        )
    )

    return (
        start_date.isoformat(),
        end_date.isoformat(),
    )


def query_search_analytics(
    dimensions: list[str],
) -> list[dict[str, Any]]:
    """指定ディメンションで検索実績を取得する。"""

    service = get_search_console_service()

    start_date, end_date = get_date_range()

    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "type": "web",
        "aggregationType": "auto",
        "rowLimit": SEARCH_CONSOLE_ROW_LIMIT,
        "startRow": 0,
        "dataState": "final",
    }

    response = (
        service.searchanalytics()
        .query(
            siteUrl=SEARCH_CONSOLE_SITE_URL,
            body=request_body,
        )
        .execute()
    )

    rows = response.get(
        "rows",
        [],
    )

    results: list[dict[str, Any]] = []

    for row in rows:
        keys = row.get("keys", [])

        item: dict[str, Any] = {
            "clicks": float(
                row.get("clicks", 0)
            ),
            "impressions": float(
                row.get("impressions", 0)
            ),
            "ctr": float(
                row.get("ctr", 0)
            ),
            "position": float(
                row.get("position", 0)
            ),
        }

        for index, dimension in enumerate(
            dimensions
        ):
            item[dimension] = (
                keys[index]
                if index < len(keys)
                else ""
            )

        results.append(item)

    return results


def save_csv(
    filename: str,
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> Path:
    """取得結果をCSVへ保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filepath = OUTPUT_DIR / filename

    with filepath.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)

    return filepath


def create_summary(
    page_rows: list[dict[str, Any]],
    query_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Search Consoleデータの概要を作る。"""

    total_clicks = sum(
        row["clicks"]
        for row in page_rows
    )

    total_impressions = sum(
        row["impressions"]
        for row in page_rows
    )

    overall_ctr = (
        total_clicks / total_impressions
        if total_impressions
        else 0.0
    )

    weighted_position = (
        sum(
            row["position"]
            * row["impressions"]
            for row in page_rows
        )
        / total_impressions
        if total_impressions
        else 0.0
    )

    opportunity_pages = [
        row
        for row in page_rows
        if (
            row["impressions"] >= 10
            and 4 <= row["position"] <= 20
        )
    ]

    low_ctr_pages = [
        row
        for row in page_rows
        if (
            row["impressions"] >= 20
            and row["ctr"] < 0.02
        )
    ]

    top_queries = sorted(
        query_rows,
        key=lambda row: (
            row["impressions"]
        ),
        reverse=True,
    )[:20]

    return {
        "site_url":
            SEARCH_CONSOLE_SITE_URL,
        "generated_at":
            date.today().isoformat(),
        "period": {
            "start_date":
                get_date_range()[0],
            "end_date":
                get_date_range()[1],
        },
        "totals": {
            "clicks":
                round(total_clicks, 2),
            "impressions":
                round(total_impressions, 2),
            "ctr":
                round(overall_ctr, 4),
            "average_position":
                round(weighted_position, 2),
        },
        "opportunity_pages":
            opportunity_pages,
        "low_ctr_pages":
            low_ctr_pages,
        "top_queries":
            top_queries,
    }


def fetch_search_console_data() -> dict[str, Any]:
    """主要なSearch Consoleデータを取得して保存する。"""

    print(
        "[Search Console] "
        "ページ別データを取得中..."
    )

    page_rows = query_search_analytics(
        ["page"]
    )

    print(
        "[Search Console] "
        "検索語別データを取得中..."
    )

    query_rows = query_search_analytics(
        ["query"]
    )

    print(
        "[Search Console] "
        "ページ×検索語データを取得中..."
    )

    page_query_rows = (
        query_search_analytics(
            [
                "page",
                "query",
            ]
        )
    )

    page_file = save_csv(
        "page_performance.csv",
        page_rows,
        [
            "page",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ],
    )

    query_file = save_csv(
        "query_performance.csv",
        query_rows,
        [
            "query",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ],
    )

    page_query_file = save_csv(
        "page_query_performance.csv",
        page_query_rows,
        [
            "page",
            "query",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ],
    )

    summary = create_summary(
        page_rows,
        query_rows,
    )

    summary_file = (
        OUTPUT_DIR
        / "summary.json"
    )

    summary_file.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "page_file": page_file,
        "query_file": query_file,
        "page_query_file":
            page_query_file,
        "summary_file":
            summary_file,
        "summary": summary,
    }


def print_search_console_report() -> None:
    """取得結果の概要をコンソールへ表示する。"""

    result = fetch_search_console_data()

    summary = result["summary"]
    totals = summary["totals"]

    print(
        "\n===== Search Console Report ====="
    )

    print(
        "期間："
        f"{summary['period']['start_date']}"
        " ～ "
        f"{summary['period']['end_date']}"
    )

    print(
        f"クリック数：{totals['clicks']}"
    )

    print(
        f"表示回数：{totals['impressions']}"
    )

    print(
        "CTR："
        f"{totals['ctr'] * 100:.2f}%"
    )

    print(
        "平均掲載順位："
        f"{totals['average_position']:.2f}"
    )

    print(
        "改善候補ページ："
        f"{len(summary['opportunity_pages'])}件"
    )

    print(
        "低CTRページ："
        f"{len(summary['low_ctr_pages'])}件"
    )

    print(
        "\n保存先："
        f"{OUTPUT_DIR}"
    )