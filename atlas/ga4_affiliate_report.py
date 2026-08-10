import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from google.analytics.data_v1beta import (
    BetaAnalyticsDataClient,
)
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import (
    InstalledAppFlow,
)

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "revenue"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "affiliate_clicks.json"
)

# あとで自分のGA4 Property IDへ変更する
GA4_PROPERTY_ID = "547702412"

CLIENT_SECRET_FILE = (
    BASE_DIR
    / "credentials"
    / "search_console_client_secret.json"
)

GA4_TOKEN_FILE = (
    BASE_DIR
    / "credentials"
    / "ga4_token.json"
)

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
]

def get_ga4_credentials() -> Credentials:
    """GA4 Data API用OAuth認証情報を取得する。"""

    credentials = None

    if GA4_TOKEN_FILE.exists():
        credentials = (
            Credentials.from_authorized_user_file(
                str(GA4_TOKEN_FILE),
                SCOPES,
            )
        )

    if (
        credentials is not None
        and credentials.expired
        and credentials.refresh_token
    ):
        credentials.refresh(
            Request()
        )

    if (
        credentials is None
        or not credentials.valid
    ):
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                "OAuthクライアントファイルが"
                "見つかりません："
                f"{CLIENT_SECRET_FILE}"
            )

        flow = (
            InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE),
                SCOPES,
            )
        )

        credentials = (
            flow.run_local_server(
                port=0,
            )
        )

    GA4_TOKEN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    GA4_TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return credentials

def get_date_range(
    days: int = 28,
) -> tuple[str, str]:
    """GA4取得期間を返す。"""

    end_date = (
        date.today()
        - timedelta(days=1)
    )

    start_date = (
        end_date
        - timedelta(
            days=days - 1,
        )
    )

    return (
        start_date.isoformat(),
        end_date.isoformat(),
    )

def fetch_affiliate_clicks(
) -> list[dict[str, Any]]:
    """GA4からaffiliate_clickイベントを取得する。"""

    if not GA4_PROPERTY_ID.strip():
        raise ValueError(
            "GA4_PROPERTY_IDが未設定です。"
        )

    credentials = (
        get_ga4_credentials()
    )

    client = (
        BetaAnalyticsDataClient(
            credentials=credentials,
        )
    )

    start_date, end_date = (
        get_date_range()
    )

    request = RunReportRequest(
        property=(
            f"properties/"
            f"{GA4_PROPERTY_ID}"
        ),
        dimensions=[
            Dimension(
                name="date",
            ),
            Dimension(
                name="customEvent:service_name",
            ),
            Dimension(
                name="customEvent:cta_type",
            ),
            Dimension(
                name="customEvent:cta_placement",
            ),
            Dimension(
                name="customEvent:link_type",
            ),
            Dimension(
                name="customEvent:affiliate_network",
            ),
            Dimension(
                name="pagePath",
            ),
        ],
        metrics=[
            Metric(
                name="eventCount",
            ),
        ],
        date_ranges=[
            DateRange(
                start_date=start_date,
                end_date=end_date,
            )
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    value="affiliate_click",
                    match_type=(
                        Filter.StringFilter.MatchType.EXACT
                    ),
                ),
            )
        ),
    )

    response = client.run_report(
        request
    )

    results: list[
        dict[str, Any]
    ] = []

    for row in response.rows:
        dimensions = [
            value.value
            for value
            in row.dimension_values
        ]

        metrics = [
            value.value
            for value
            in row.metric_values
        ]

        (
            raw_date,
            service,
            cta_type,
            cta_placement,
            link_type,
            network,
            page_path,
        ) = dimensions

        click_count = int(
            metrics[0]
            or 0
        )

        article_slug = ""

        prefix = "/blog/"

        if page_path.startswith(
            prefix
        ):
            article_slug = (
                page_path[
                    len(prefix):
                ]
                .strip("/")
            )

        formatted_date = raw_date

        if len(raw_date) == 8:
            formatted_date = (
                f"{raw_date[0:4]}-"
                f"{raw_date[4:6]}-"
                f"{raw_date[6:8]}"
            )

        # 旧計測形式の affiliate_click を除外する
        if (
            not service
            or service == "(not set)"
        ):
            continue

        results.append(
            {
                "date": formatted_date,
                "service": service,
                "article_slug": (
                    article_slug
                ),
                "cta_type": cta_type,
                "cta_placement": (
                    cta_placement
                ),
                "link_type": link_type,
                "network": network,
                "clicks": (
                    click_count
                ),
                "page_path": page_path,
            }
        )

    return results

def save_affiliate_clicks(
    clicks: list[dict[str, Any]],
) -> Path:
    """GA4 Affiliate ClickをJSON保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "clicks": clicks,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE

def print_affiliate_clicks(
    clicks: list[dict[str, Any]],
) -> None:
    """取得結果を表示する。"""

    print(
        "\n===== GA4 Affiliate Click Report =====\n"
    )

    if not clicks:
        print(
            "affiliate_clickは"
            "まだありません。"
        )
        return

    total_clicks = sum(
        int(
            item.get(
                "clicks",
                0,
            )
            or 0
        )
        for item in clicks
    )

    print(
        f"取得行数：{len(clicks)}"
    )

    print(
        f"合計クリック数：{total_clicks}"
    )

    print()

    for item in clicks:
        print(
            f"{item['date']} / "
            f"{item['service']} / "
            f"{item['article_slug']} / "
            f"{item['cta_type']} / "
            f"{item['cta_placement']} / "
            f"{item['clicks']}クリック"
        )

def main() -> None:
    clicks = (
        fetch_affiliate_clicks()
    )

    filepath = (
        save_affiliate_clicks(
            clicks
        )
    )

    print_affiliate_clicks(
        clicks
    )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()