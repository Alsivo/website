import json
from pathlib import Path
from typing import Any

from engines.affiliate_registry import (
    load_affiliate_registry,
)


BASE_DIR = Path(__file__).resolve().parents[1]

REVENUE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_summary.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_feedback.json"
)


MIN_CLICKS_FOR_CVR_JUDGMENT = 20
MIN_CLICKS_FOR_EXPANSION = 10
GOOD_EPC = 50.0


def load_revenue_summary(
) -> dict[str, Any]:
    """Revenue Summaryを読み込む。"""

    if not REVENUE_SUMMARY_FILE.exists():
        raise FileNotFoundError(
            "revenue_summary.jsonが"
            "見つかりません："
            f"{REVENUE_SUMMARY_FILE}"
        )

    try:
        data = json.loads(
            REVENUE_SUMMARY_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "revenue_summary.jsonの"
            "JSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "revenue_summary.jsonの"
            "形式が不正です。"
        )

    return data


def evaluate_service(
    service: str,
    metrics: dict[str, Any],
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """サービス単位で次の行動を判定する。"""

    clicks = int(
        metrics.get(
            "clicks",
            0,
        )
        or 0
    )

    conversions = int(
        metrics.get(
            "conversions",
            0,
        )
        or 0
    )

    revenue = float(
        metrics.get(
            "revenue",
            0.0,
        )
        or 0.0
    )

    epc = float(
        metrics.get(
            "epc",
            0.0,
        )
        or 0.0
    )

    registry_item = registry.get(
        service,
        {},
    )

    affiliate_status = str(
        registry_item.get(
            "affiliate_status",
            "none",
        )
        or "none"
    ).strip()

    affiliate_url = str(
        registry_item.get(
            "affiliate_url",
            "",
        )
        or ""
    ).strip()

    network = str(
        registry_item.get(
            "network",
            "",
        )
        or ""
    ).strip()

    is_active = (
        affiliate_status == "active"
        and bool(affiliate_url)
    )

    if clicks == 0:
        return {
            "service": service,
            "action": "WAIT_DATA",
            "priority": 20,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "epc": epc,
            "affiliate_status": affiliate_status,
            "network": network,
            "reason": (
                "クリックデータがまだないため、"
                "判断材料が不足しています。"
            ),
            "next": (
                "クリックデータの蓄積を待つ"
            ),
        }

    if not is_active:
        if affiliate_status == "pending":
            return {
                "service": service,
                "action": "WAIT_APPROVAL",
                "priority": 85,
                "clicks": clicks,
                "conversions": conversions,
                "revenue": revenue,
                "epc": epc,
                "affiliate_status": affiliate_status,
                "network": network,
                "reason": (
                    "クリック需要は確認できますが、"
                    "案件がまだ審査中です。"
                ),
                "next": (
                    "ASPの承認結果を待つ"
                ),
            }

        return {
            "service": service,
            "action": "MONETIZE",
            "priority": 90,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "epc": epc,
            "affiliate_status": affiliate_status,
            "network": network,
            "reason": (
                "クリック需要がありますが、"
                "収益化可能なAffiliate案件が"
                "有効化されていません。"
            ),
            "next": (
                "国内ASPまたは直接案件を"
                "優先して確認する"
            ),
        }

    if (
        clicks
        >= MIN_CLICKS_FOR_CVR_JUDGMENT
        and conversions == 0
    ):
        return {
            "service": service,
            "action": "IMPROVE_CTA",
            "priority": 80,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "epc": epc,
            "affiliate_status": affiliate_status,
            "network": network,
            "reason": (
                "Affiliateクリックは十分ありますが、"
                "成果が発生していません。"
            ),
            "next": (
                "CTA文言、配置、記事と案件の"
                "適合性を見直す"
            ),
        }

    if (
        conversions > 0
        and epc >= GOOD_EPC
    ):
        return {
            "service": service,
            "action": "EXPAND_CONTENT",
            "priority": 95,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "epc": epc,
            "affiliate_status": affiliate_status,
            "network": network,
            "reason": (
                "成果が発生しており、"
                "EPCも高いため収益性が"
                "確認されています。"
            ),
            "next": (
                "評判・料金・比較など"
                "関連収益記事を追加する"
            ),
        }

    if conversions > 0:
        return {
            "service": service,
            "action": "KEEP",
            "priority": 70,
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "epc": epc,
            "affiliate_status": affiliate_status,
            "network": network,
            "reason": (
                "成果が発生しているため、"
                "現在の導線を維持する価値があります。"
            ),
            "next": (
                "データを継続蓄積する"
            ),
        }

    return {
        "service": service,
        "action": "WAIT_DATA",
        "priority": 40,
        "clicks": clicks,
        "conversions": conversions,
        "revenue": revenue,
        "epc": epc,
        "affiliate_status": affiliate_status,
        "network": network,
        "reason": (
            "Affiliate導線は有効ですが、"
            "まだCVRを判断できるだけの"
            "クリック数がありません。"
        ),
        "next": (
            "データの蓄積を待つ"
        ),
    }


def evaluate_articles(
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """記事単位で注目記事を判定する。"""

    by_article = summary.get(
        "by_article",
        {},
    )

    if not isinstance(
        by_article,
        dict,
    ):
        return []

    results: list[
        dict[str, Any]
    ] = []

    for slug, metrics in by_article.items():
        if not isinstance(
            metrics,
            dict,
        ):
            continue

        clicks = int(
            metrics.get(
                "clicks",
                0,
            )
            or 0
        )

        conversions = int(
            metrics.get(
                "conversions",
                0,
            )
            or 0
        )

        revenue = float(
            metrics.get(
                "revenue",
                0.0,
            )
            or 0.0
        )

        epc = float(
            metrics.get(
                "epc",
                0.0,
            )
            or 0.0
        )

        if clicks >= MIN_CLICKS_FOR_EXPANSION:
            action = "PRIORITY_REVIEW"
            priority = 80
            reason = (
                "Affiliate CTAへのクリックが"
                "比較的多い記事です。"
            )
        elif clicks > 0:
            action = "WATCH"
            priority = 40
            reason = (
                "クリックは発生していますが、"
                "判断にはまだデータが少ない状態です。"
            )
        else:
            action = "WAIT_DATA"
            priority = 20
            reason = (
                "クリックデータがありません。"
            )

        results.append(
            {
                "article_slug": slug,
                "action": action,
                "priority": priority,
                "clicks": clicks,
                "conversions": conversions,
                "revenue": revenue,
                "epc": epc,
                "reason": reason,
            }
        )

    results.sort(
        key=lambda item: (
            item["priority"],
            item["clicks"],
        ),
        reverse=True,
    )

    return results


def build_feedback(
    summary: dict[str, Any],
) -> dict[str, Any]:
    """Revenue Feedback全体を作る。"""

    registry = (
        load_affiliate_registry()
    )

    by_service = summary.get(
        "by_service",
        {},
    )

    service_feedback: list[
        dict[str, Any]
    ] = []

    if isinstance(
        by_service,
        dict,
    ):
        for service, metrics in (
            by_service.items()
        ):
            if not isinstance(
                metrics,
                dict,
            ):
                continue

            service_feedback.append(
                evaluate_service(
                    service=service,
                    metrics=metrics,
                    registry=registry,
                )
            )

    service_feedback.sort(
        key=lambda item: (
            item["priority"],
            item["clicks"],
        ),
        reverse=True,
    )

    article_feedback = (
        evaluate_articles(
            summary
        )
    )

    total_clicks = int(
        summary.get(
            "total_clicks",
            0,
        )
        or 0
    )

    total_conversions = int(
        summary.get(
            "total_conversions",
            0,
        )
        or 0
    )

    total_revenue = float(
        summary.get(
            "total_revenue",
            0.0,
        )
        or 0.0
    )

    overall_epc = float(
        summary.get(
            "epc",
            0.0,
        )
        or 0.0
    )

    return {
        "overview": {
            "total_clicks": (
                total_clicks
            ),
            "total_conversions": (
                total_conversions
            ),
            "total_revenue": (
                total_revenue
            ),
            "epc": (
                overall_epc
            ),
        },
        "service_actions": (
            service_feedback
        ),
        "article_actions": (
            article_feedback
        ),
    }


def save_feedback(
    data: dict[str, Any],
) -> Path:
    """Revenue Feedbackを保存する。"""

    OUTPUT_FILE.parent.mkdir(
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


def print_feedback(
    data: dict[str, Any],
) -> None:
    """Revenue Feedbackを表示する。"""

    print(
        "\n===== Revenue Feedback =====\n"
    )

    actions = data.get(
        "service_actions",
        [],
    )

    for index, item in enumerate(
        actions,
        start=1,
    ):
        print(
            f"[{index}] "
            f"{item['service']}"
        )

        print(
            "    action: "
            f"{item['action']}"
        )

        print(
            "    priority: "
            f"{item['priority']}"
        )

        print(
            "    clicks: "
            f"{item['clicks']}"
        )

        print(
            "    conversions: "
            f"{item['conversions']}"
        )

        print(
            "    revenue: "
            f"{item['revenue']}"
        )

        print(
            "    EPC: "
            f"{item['epc']:.2f}"
        )

        print(
            "    affiliate status: "
            f"{item['affiliate_status']}"
        )

        print(
            "    reason: "
            f"{item['reason']}"
        )

        print(
            "    next: "
            f"{item['next']}"
        )

        print()


def main() -> None:
    summary = (
        load_revenue_summary()
    )

    feedback = (
        build_feedback(
            summary
        )
    )

    filepath = (
        save_feedback(
            feedback
        )
    )

    print_feedback(
        feedback
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()