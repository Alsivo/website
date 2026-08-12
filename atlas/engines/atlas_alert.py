import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

DAILY_REPORT_FILE = (
    BASE_DIR
    / "data"
    / "daily_report"
    / "daily_report.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "alerts"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "latest_alert.json"
)


LEVEL_PRIORITY = {
    "INFO": 0,
    "ACTION": 1,
    "WARNING": 2,
    "CRITICAL": 3,
}


def load_daily_report() -> dict[str, Any]:
    """Atlas Daily Reportを読み込む。"""

    if not DAILY_REPORT_FILE.exists():
        return {}

    try:
        data = json.loads(
            DAILY_REPORT_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def create_alert(
    level: str,
    category: str,
    title: str,
    reason: str,
    recommended_action: str,
) -> dict[str, Any]:
    """Alertを1件作成する。"""

    return {
        "level": level,
        "category": category,
        "title": title,
        "reason": reason,
        "recommended_action":
            recommended_action,
    }


def evaluate_system(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Atlas本体の異常を判定する。"""

    alerts = []

    system = report.get(
        "system",
        {},
    )

    if not isinstance(
        system,
        dict,
    ):
        system = {}

    status = str(
        system.get(
            "status",
            "",
        )
    )

    health = str(
        system.get(
            "health",
            "",
        )
    )

    health_reason = str(
        system.get(
            "health_reason",
            "",
        )
    )

    lock_active = bool(
        system.get(
            "lock_active",
            False,
        )
    )

    if not status:
        alerts.append(
            create_alert(
                level="CRITICAL",
                category="system",
                title=(
                    "Atlas実行状態を"
                    "取得できません"
                ),
                reason=(
                    "Daily Reportに"
                    "system.statusがありません。"
                ),
                recommended_action=(
                    "latest_run.jsonと"
                    "Daily Report生成処理を"
                    "確認してください。"
                ),
            )
        )

    elif status != "success":
        alerts.append(
            create_alert(
                level="CRITICAL",
                category="system",
                title=(
                    "Atlasの最新実行が"
                    "正常終了していません"
                ),
                reason=(
                    f"status={status}"
                ),
                recommended_action=(
                    "Atlasの実行ログを確認し、"
                    "失敗したEngineを"
                    "特定してください。"
                ),
            )
        )

    if not health:
        alerts.append(
            create_alert(
                level="WARNING",
                category="system",
                title=(
                    "Atlas Healthを"
                    "取得できません"
                ),
                reason=(
                    "Daily Reportに"
                    "system.healthがありません。"
                ),
                recommended_action=(
                    "health_status.jsonと"
                    "Atlas Health処理を"
                    "確認してください。"
                ),
            )
        )

    elif health == "error":
        alerts.append(
            create_alert(
                level="CRITICAL",
                category="system",
                title="Atlas Health異常",
                reason=(
                    health_reason
                    or
                    "Atlas Healthが"
                    "errorです。"
                ),
                recommended_action=(
                    "health_status.jsonと"
                    "自動運転ログを"
                    "確認してください。"
                ),
            )
        )

    elif health != "healthy":
        alerts.append(
            create_alert(
                level="WARNING",
                category="system",
                title="Atlas Health警告",
                reason=(
                    health_reason
                    or
                    f"health={health}"
                ),
                recommended_action=(
                    "Atlasの前回実行時刻と"
                    "自動運転ログを"
                    "確認してください。"
                ),
            )
        )

    if lock_active:
        alerts.append(
            create_alert(
                level="WARNING",
                category="system",
                title=(
                    "Atlas Lockが"
                    "残っています"
                ),
                reason=(
                    "Daily Reportで"
                    "lock_active=trueです。"
                ),
                recommended_action=(
                    "Atlasが現在実行中でないことを"
                    "確認してから、"
                    "lock状態を調査してください。"
                ),
            )
        )

    return alerts


def evaluate_editorial(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """AI編集長の人間対応事項を判定する。"""

    alerts = []

    editorial = report.get(
        "editorial",
        {},
    )

    if not isinstance(
        editorial,
        dict,
    ):
        return alerts

    action = str(
        editorial.get(
            "action",
            "",
        )
    )

    priority = int(
        editorial.get(
            "priority_score",
            0,
        )
        or 0
    )

    target_title = str(
        editorial.get(
            "target_title",
            "",
        )
    )

    target_slug = str(
        editorial.get(
            "target_slug",
            "",
        )
    )

    if action in {
        "new_article",
        "rewrite_article",
    }:
        target = (
            target_title
            or target_slug
            or "対象記事"
        )

        alerts.append(
            create_alert(
                level="ACTION",
                category="editorial",
                title=(
                    "AI編集長から"
                    "編集Actionがあります"
                ),
                reason=(
                    f"{target} に対して "
                    f"{action} が選択されています。"
                    f" priority={priority}"
                ),
                recommended_action=(
                    "AI編集長の判断内容を確認し、"
                    "必要に応じて"
                    "記事生成・リライトを"
                    "承認してください。"
                ),
            )
        )

    return alerts


def evaluate_seo(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """SEO改善候補を判定する。"""

    alerts = []

    seo = report.get(
        "seo",
        {},
    )

    if not isinstance(
        seo,
        dict,
    ):
        return alerts

    ready_actions = int(
        seo.get(
            "ready_actions",
            0,
        )
        or 0
    )

    opportunity_pages = int(
        seo.get(
            "opportunity_pages",
            0,
        )
        or 0
    )

    low_ctr_pages = int(
        seo.get(
            "low_ctr_pages",
            0,
        )
        or 0
    )

    if ready_actions > 0:
        alerts.append(
            create_alert(
                level="ACTION",
                category="seo",
                title="SEO改善Actionがあります",
                reason=(
                    f"{ready_actions}件の"
                    "SEO Actionが"
                    "実行候補です。"
                ),
                recommended_action=(
                    "SEO Action Planを確認し、"
                    "改善対象記事を"
                    "確認してください。"
                ),
            )
        )

    if opportunity_pages > 0:
        alerts.append(
            create_alert(
                level="ACTION",
                category="seo",
                title=(
                    "SEO Opportunity Pageが"
                    "見つかりました"
                ),
                reason=(
                    f"{opportunity_pages}件の"
                    "改善機会があります。"
                ),
                recommended_action=(
                    "Search Consoleの"
                    "Opportunity Pageを確認し、"
                    "部分改善候補を"
                    "検討してください。"
                ),
            )
        )

    if low_ctr_pages > 0:
        alerts.append(
            create_alert(
                level="ACTION",
                category="seo",
                title="低CTRページがあります",
                reason=(
                    f"{low_ctr_pages}件の"
                    "低CTRページがあります。"
                ),
                recommended_action=(
                    "タイトル・description・"
                    "検索意図との一致を"
                    "確認してください。"
                ),
            )
        )

    return alerts


def evaluate_revenue(
    report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Revenue Actionを判定する。"""

    alerts = []

    revenue = report.get(
        "revenue",
        {},
    )

    if not isinstance(
        revenue,
        dict,
    ):
        return alerts

    conversions = int(
        revenue.get(
            "conversions",
            0,
        )
        or 0
    )

    revenue_amount = float(
        revenue.get(
            "revenue",
            0,
        )
        or 0
    )

    top_action = revenue.get(
        "top_action",
        {},
    )

    if isinstance(
        top_action,
        dict,
    ) and top_action:

        destination = str(
            top_action.get(
                "destination",
                "",
            )
        )

        if destination in {
            "monetization",
            "cta",
            "content",
        }:
            service = str(
                top_action.get(
                    "service",
                    "",
                )
            )

            source_action = str(
                top_action.get(
                    "source_action",
                    "",
                )
            )

            clicks = int(
                top_action.get(
                    "clicks",
                    0,
                )
                or 0
            )

            priority = int(
                top_action.get(
                    "priority",
                    0,
                )
                or 0
            )

            reason = str(
                top_action.get(
                    "reason",
                    "",
                )
            )

            next_action = str(
                top_action.get(
                    "next",
                    "",
                )
            )

            alerts.append(
                create_alert(
                    level="ACTION",
                    category="revenue",
                    title=(
                        f"{service}の"
                        "収益化対応があります"
                    ),
                    reason=(
                        reason
                        or
                        (
                            f"{source_action} / "
                            f"clicks={clicks} / "
                            f"priority={priority}"
                        )
                    ),
                    recommended_action=(
                        next_action
                        or
                        "Revenue Action Queueを"
                        "確認してください。"
                    ),
                )
            )

    if conversions > 0:
        alerts.append(
            create_alert(
                level="INFO",
                category="revenue",
                title="Affiliate成果が発生しました",
                reason=(
                    f"成果件数={conversions}、"
                    f"収益={revenue_amount:.0f}円"
                ),
                recommended_action=(
                    "Revenue Summaryで"
                    "成果元の記事・サービスを"
                    "確認してください。"
                ),
            )
        )

    return alerts


def get_overall_level(
    alerts: list[dict[str, Any]],
) -> str:
    """Alert一覧から最高重要度を返す。"""

    if not alerts:
        return "INFO"

    return max(
        (
            str(
                alert.get(
                    "level",
                    "INFO",
                )
            )
            for alert in alerts
        ),
        key=lambda level:
            LEVEL_PRIORITY.get(
                level,
                0,
            ),
    )


def build_alert_report(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Alert Report全体を作る。"""

    alerts = []

    if not report:
        alerts.append(
            create_alert(
                level="CRITICAL",
                category="system",
                title=(
                    "Atlas Daily Reportを"
                    "読み込めません"
                ),
                reason=(
                    "daily_report.jsonが"
                    "存在しないか、"
                    "JSON形式が不正です。"
                ),
                recommended_action=(
                    "Atlas Daily Reportを"
                    "再生成してください。"
                ),
            )
        )

    else:
        alerts.extend(
            evaluate_system(
                report
            )
        )

        alerts.extend(
            evaluate_editorial(
                report
            )
        )

        alerts.extend(
            evaluate_seo(
                report
            )
        )

        alerts.extend(
            evaluate_revenue(
                report
            )
        )

    alerts.sort(
        key=lambda alert:
            LEVEL_PRIORITY.get(
                str(
                    alert.get(
                        "level",
                        "INFO",
                    )
                ),
                0,
            ),
        reverse=True,
    )

    overall_level = (
        get_overall_level(
            alerts
        )
    )

    requires_attention = any(
        str(
            alert.get(
                "level",
                "",
            )
        )
        in {
            "ACTION",
            "WARNING",
            "CRITICAL",
        }
        for alert in alerts
    )

    counts = {
        "CRITICAL": 0,
        "WARNING": 0,
        "ACTION": 0,
        "INFO": 0,
    }

    for alert in alerts:
        level = str(
            alert.get(
                "level",
                "INFO",
            )
        )

        if level in counts:
            counts[level] += 1

    return {
        "generated_at":
            datetime.now().isoformat(),
        "overall_level":
            overall_level,
        "requires_attention":
            requires_attention,
        "alert_count":
            len(alerts),
        "counts":
            counts,
        "alerts":
            alerts,
    }


def save_alert_report(
    alert_report: dict[str, Any],
) -> Path:
    """Alert ReportをJSON保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            alert_report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_alert_report(
    alert_report: dict[str, Any],
) -> None:
    """Alert Reportをコンソール表示する。"""

    print(
        "\n===== Atlas Alert =====\n"
    )

    print(
        "Overall Level："
        f"{alert_report['overall_level']}"
    )

    print(
        "Requires Attention："
        + (
            "YES"
            if alert_report[
                "requires_attention"
            ]
            else "NO"
        )
    )

    print(
        "Alert Count："
        f"{alert_report['alert_count']}"
    )

    counts = alert_report[
        "counts"
    ]

    print(
        "CRITICAL："
        f"{counts['CRITICAL']}"
    )

    print(
        "WARNING："
        f"{counts['WARNING']}"
    )

    print(
        "ACTION："
        f"{counts['ACTION']}"
    )

    print(
        "INFO："
        f"{counts['INFO']}"
    )

    alerts = alert_report[
        "alerts"
    ]

    if not alerts:
        print(
            "\n対応が必要なAlertは"
            "ありません。"
        )

    for index, alert in enumerate(
        alerts,
        start=1,
    ):
        print(
            f"\n[{index}] "
            f"{alert['level']} / "
            f"{alert['category']}"
        )

        print(
            "Title："
            f"{alert['title']}"
        )

        print(
            "Reason："
            f"{alert['reason']}"
        )

        print(
            "Next："
            f"{alert['recommended_action']}"
        )

    print()


def main() -> None:
    report = (
        load_daily_report()
    )

    alert_report = (
        build_alert_report(
            report
        )
    )

    filepath = (
        save_alert_report(
            alert_report
        )
    )

    print_alert_report(
        alert_report
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()