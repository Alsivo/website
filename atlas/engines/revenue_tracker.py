import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

REVENUE_DIR = (
    BASE_DIR
    / "data"
    / "revenue"
)

CONVERSIONS_FILE = (
    REVENUE_DIR
    / "manual_conversions.json"
)

OUTPUT_FILE = (
    REVENUE_DIR
    / "revenue_summary.json"
)

CLICKS_FILE = (
    REVENUE_DIR
    / "affiliate_clicks.json"
)

def load_conversion_data(
) -> list[dict[str, Any]]:
    """収益・成果データを読み込む。"""

    if not CONVERSIONS_FILE.exists():
        return []

    try:
        data = json.loads(
            CONVERSIONS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "manual_conversions.jsonの"
            "JSON形式が不正です。"
        ) from error

    conversions = data.get(
        "conversions",
        [],
    )

    if not isinstance(
        conversions,
        list,
    ):
        raise ValueError(
            "conversionsは配列にしてください。"
        )

    return [
        item
        for item in conversions
        if isinstance(
            item,
            dict,
        )
    ]

def load_click_data(
) -> list[dict[str, Any]]:
    """GA4由来のAffiliate Clickデータを読み込む。"""

    if not CLICKS_FILE.exists():
        return []

    try:
        data = json.loads(
            CLICKS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "affiliate_clicks.jsonの"
            "JSON形式が不正です。"
        ) from error

    clicks = data.get(
        "clicks",
        [],
    )

    if not isinstance(
        clicks,
        list,
    ):
        raise ValueError(
            "clicksは配列にしてください。"
        )

    return [
        item
        for item in clicks
        if isinstance(
            item,
            dict,
        )
    ]

def summarize_clicks_by_service(
    clicks: list[dict[str, Any]],
) -> dict[str, int]:
    """Affiliate Clickをサービス別に集計する。"""

    result: dict[str, int] = {}

    for item in clicks:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        count = int(
            item.get(
                "clicks",
                0,
            )
            or 0
        )

        result[service] = (
            result.get(
                service,
                0,
            )
            + count
        )

    return result


def summarize_clicks_by_article(
    clicks: list[dict[str, Any]],
) -> dict[str, int]:
    """Affiliate Clickを記事別に集計する。"""

    result: dict[str, int] = {}

    for item in clicks:
        slug = str(
            item.get(
                "article_slug",
                "",
            )
        ).strip()

        if not slug:
            continue

        count = int(
            item.get(
                "clicks",
                0,
            )
            or 0
        )

        result[slug] = (
            result.get(
                slug,
                0,
            )
            + count
        )

    return result

def summarize_by_service(
    conversions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """サービス別に成果を集計する。"""

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in conversions:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        clicks = int(
            item.get(
                "clicks",
                0,
            )
            or 0
        )

        conversions_count = int(
            item.get(
                "conversions",
                0,
            )
            or 0
        )

        revenue = float(
            item.get(
                "revenue",
                0,
            )
            or 0
        )

        if service not in result:
            result[service] = {
                "clicks": 0,
                "conversions": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
            }

        result[
            service
        ]["clicks"] += clicks

        result[
            service
        ]["conversions"] += (
            conversions_count
        )

        result[
            service
        ]["revenue"] += revenue

    for item in result.values():
        clicks = item[
            "clicks"
        ]

        conversions_count = item[
            "conversions"
        ]

        if clicks > 0:
            item[
                "conversion_rate"
            ] = (
                conversions_count
                / clicks
            )

    return result

def summarize_by_article(
    conversions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """記事別に成果を集計する。"""

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in conversions:
        slug = str(
            item.get(
                "article_slug",
                "",
            )
        ).strip()

        if not slug:
            continue

        clicks = int(
            item.get(
                "clicks",
                0,
            )
            or 0
        )

        conversions_count = int(
            item.get(
                "conversions",
                0,
            )
            or 0
        )

        revenue = float(
            item.get(
                "revenue",
                0,
            )
            or 0
        )

        if slug not in result:
            result[slug] = {
                "clicks": 0,
                "conversions": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
            }

        result[
            slug
        ]["clicks"] += clicks

        result[
            slug
        ]["conversions"] += (
            conversions_count
        )

        result[
            slug
        ]["revenue"] += revenue

    for item in result.values():
        clicks = item[
            "clicks"
        ]

        conversions_count = item[
            "conversions"
        ]

        if clicks > 0:
            item[
                "conversion_rate"
            ] = (
                conversions_count
                / clicks
            )

    return result

def build_revenue_summary(
    conversions: list[dict[str, Any]],
    clicks: list[dict[str, Any]],
) -> dict[str, Any]:
    """収益データ全体を集計する。"""

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

    total_conversions = sum(
        int(
            item.get(
                "conversions",
                0,
            )
            or 0
        )
        for item in conversions
    )

    total_revenue = sum(
        float(
            item.get(
                "revenue",
                0,
            )
            or 0
        )
        for item in conversions
    )

    overall_conversion_rate = (
        total_conversions
        / total_clicks
        if total_clicks > 0
        else 0.0
    )

    by_service = (
        summarize_by_service(
            conversions
        )
    )

    by_article = (
        summarize_by_article(
            conversions
        )
    )

    service_clicks = (
        summarize_clicks_by_service(
            clicks
        )
    )

    article_clicks = (
        summarize_clicks_by_article(
            clicks
        )
    )

    # GA4由来のクリック数をサービス別集計へ反映する
    for service, click_count in (
        service_clicks.items()
    ):
        if service not in by_service:
            by_service[service] = {
                "clicks": 0,
                "conversions": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
            }

        by_service[
            service
        ]["clicks"] = click_count

        conversions_count = int(
            by_service[
                service
            ].get(
                "conversions",
                0,
            )
            or 0
        )

        by_service[
            service
        ]["conversion_rate"] = (
            conversions_count
            / click_count
            if click_count > 0
            else 0.0
        )

    # GA4由来のクリック数を記事別集計へ反映する
    for slug, click_count in (
        article_clicks.items()
    ):
        if slug not in by_article:
            by_article[slug] = {
                "clicks": 0,
                "conversions": 0,
                "revenue": 0.0,
                "conversion_rate": 0.0,
            }

        by_article[
            slug
        ]["clicks"] = click_count

        conversions_count = int(
            by_article[
                slug
            ].get(
                "conversions",
                0,
            )
            or 0
        )

        by_article[
            slug
        ]["conversion_rate"] = (
            conversions_count
            / click_count
            if click_count > 0
            else 0.0
        )

    return {
        "total_clicks": total_clicks,
        "total_conversions": (
            total_conversions
        ),
        "total_revenue": (
            total_revenue
        ),
        "conversion_rate": (
            overall_conversion_rate
        ),
        "by_service": (
            by_service
        ),
        "by_article": (
            by_article
        ),
    }

def save_revenue_summary(
    data: dict[str, Any],
) -> Path:
    """収益集計結果を保存する。"""

    REVENUE_DIR.mkdir(
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


def print_revenue_summary(
    data: dict[str, Any],
) -> None:
    """収益サマリーを表示する。"""

    print(
        "\n===== Revenue Summary =====\n"
    )

    print(
        "クリック数："
        f"{data['total_clicks']}"
    )

    print(
        "成果件数："
        f"{data['total_conversions']}"
    )

    print(
        "収益："
        f"{data['total_revenue']}"
    )

    print(
        "成約率："
        f"{data['conversion_rate']:.2%}"
    )

    print()

def main() -> None:
    conversions = (
        load_conversion_data()
    )

    clicks = (
        load_click_data()
    )

    summary = (
        build_revenue_summary(
            conversions,
            clicks,
        )
    )

    filepath = (
        save_revenue_summary(
            summary
        )
    )

    print_revenue_summary(
        summary
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()