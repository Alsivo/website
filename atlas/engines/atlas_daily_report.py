import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

LATEST_RUN_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "latest_run.json"
)

HEALTH_STATUS_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "health_status.json"
)

DASHBOARD_FILE = (
    BASE_DIR
    / "data"
    / "dashboard"
    / "dashboard.json"
)

EDITORIAL_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "editorial"
    / "latest_decision.json"
)

REVENUE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_summary.json"
)

SEARCH_CONSOLE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "search_console"
    / "summary.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "daily_report"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "daily_report.json"
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
    except json.JSONDecodeError:
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def build_system_section(
    latest_run: dict[str, Any],
    health: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    """Atlasのシステム状態をまとめる。"""

    dashboard_system = dashboard.get(
        "system",
        {},
    )

    if not isinstance(
        dashboard_system,
        dict,
    ):
        dashboard_system = {}

    return {
        "status": str(
            latest_run.get(
                "status",
                "",
            )
        ),
        "action": str(
            latest_run.get(
                "action",
                "",
            )
        ),
        "message": str(
            latest_run.get(
                "message",
                "",
            )
        ),
        "finished_at": str(
            latest_run.get(
                "finished_at",
                "",
            )
        ),
        "health": str(
            health.get(
                "health",
                "",
            )
        ),
        "health_reason": str(
            health.get(
                "reason",
                "",
            )
        ),
        "lock_active": bool(
            dashboard_system.get(
                "lock_active",
                False,
            )
        ),
    }


def build_editorial_section(
    editorial: dict[str, Any],
) -> dict[str, Any]:
    """AI編集長の判断をまとめる。"""

    return {
        "action": str(
            editorial.get(
                "action",
                "",
            )
        ),
        "priority_score": int(
            editorial.get(
                "priority_score",
                0,
            )
            or 0
        ),
        "reason": str(
            editorial.get(
                "reason",
                "",
            )
        ),
        "target_keyword": str(
            editorial.get(
                "target_keyword",
                "",
            )
        ),
        "target_slug": str(
            editorial.get(
                "target_slug",
                "",
            )
        ),
        "target_title": str(
            editorial.get(
                "target_title",
                "",
            )
        ),
        "recommended_focus": (
            editorial.get(
                "recommended_focus",
                [],
            )
            if isinstance(
                editorial.get(
                    "recommended_focus",
                    [],
                ),
                list,
            )
            else []
        ),
        "target_queries": (
            editorial.get(
                "target_queries",
                [],
            )
            if isinstance(
                editorial.get(
                    "target_queries",
                    [],
                ),
                list,
            )
            else []
        ),
    }


def build_seo_section(
    search_console: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    """Search ConsoleとSEO状態をまとめる。"""

    totals = search_console.get(
        "totals",
        {},
    )

    if not isinstance(
        totals,
        dict,
    ):
        totals = {}

    period = search_console.get(
        "period",
        {},
    )

    if not isinstance(
        period,
        dict,
    ):
        period = {}

    dashboard_seo = dashboard.get(
        "seo",
        {},
    )

    if not isinstance(
        dashboard_seo,
        dict,
    ):
        dashboard_seo = {}

    top_queries = search_console.get(
        "top_queries",
        [],
    )

    if not isinstance(
        top_queries,
        list,
    ):
        top_queries = []

    opportunity_pages = (
        search_console.get(
            "opportunity_pages",
            [],
        )
    )

    if not isinstance(
        opportunity_pages,
        list,
    ):
        opportunity_pages = []

    low_ctr_pages = (
        search_console.get(
            "low_ctr_pages",
            [],
        )
    )

    if not isinstance(
        low_ctr_pages,
        list,
    ):
        low_ctr_pages = []

    return {
        "period": {
            "start_date": str(
                period.get(
                    "start_date",
                    "",
                )
            ),
            "end_date": str(
                period.get(
                    "end_date",
                    "",
                )
            ),
        },
        "clicks": float(
            totals.get(
                "clicks",
                0,
            )
            or 0
        ),
        "impressions": float(
            totals.get(
                "impressions",
                0,
            )
            or 0
        ),
        "ctr": float(
            totals.get(
                "ctr",
                0,
            )
            or 0
        ),
        "average_position": float(
            totals.get(
                "average_position",
                0,
            )
            or 0
        ),
        "tracked_articles": int(
            dashboard_seo.get(
                "tracked_articles",
                0,
            )
            or 0
        ),
        "ready_actions": int(
            dashboard_seo.get(
                "ready_actions",
                0,
            )
            or 0
        ),
        "opportunity_pages": len(
            opportunity_pages
        ),
        "low_ctr_pages": len(
            low_ctr_pages
        ),
        "top_queries": (
            top_queries[:5]
        ),
    }


def build_revenue_section(
    revenue: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    """収益状態をまとめる。"""

    dashboard_revenue = dashboard.get(
        "revenue",
        {},
    )

    if not isinstance(
        dashboard_revenue,
        dict,
    ):
        dashboard_revenue = {}

    top_action = (
        dashboard_revenue.get(
            "top_revenue_action",
            {},
        )
    )

    if not isinstance(
        top_action,
        dict,
    ):
        top_action = {}

    return {
        "clicks": int(
            revenue.get(
                "total_clicks",
                0,
            )
            or 0
        ),
        "conversions": int(
            revenue.get(
                "total_conversions",
                0,
            )
            or 0
        ),
        "revenue": float(
            revenue.get(
                "total_revenue",
                0,
            )
            or 0
        ),
        "conversion_rate": float(
            revenue.get(
                "conversion_rate",
                0,
            )
            or 0
        ),
        "epc": float(
            revenue.get(
                "epc",
                0,
            )
            or 0
        ),
        "action_counts": (
            dashboard_revenue.get(
                "action_counts",
                {},
            )
            if isinstance(
                dashboard_revenue.get(
                    "action_counts",
                    {},
                ),
                dict,
            )
            else {}
        ),
        "top_action": top_action,
    }


def build_portfolio_section(
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    """Portfolio状態をまとめる。"""

    portfolio = dashboard.get(
        "portfolio",
        {},
    )

    if not isinstance(
        portfolio,
        dict,
    ):
        portfolio = {}

    return {
        "evaluated_articles": int(
            portfolio.get(
                "evaluated_articles",
                0,
            )
            or 0
        ),
        "executable_count": int(
            portfolio.get(
                "executable_count",
                0,
            )
            or 0
        ),
        "investment_counts": (
            portfolio.get(
                "investment_counts",
                {},
            )
            if isinstance(
                portfolio.get(
                    "investment_counts",
                    {},
                ),
                dict,
            )
            else {}
        ),
        "top_articles": (
            portfolio.get(
                "top_articles",
                [],
            )[:5]
            if isinstance(
                portfolio.get(
                    "top_articles",
                    [],
                ),
                list,
            )
            else []
        ),
    }


def build_summary(
    system: dict[str, Any],
    editorial: dict[str, Any],
    seo: dict[str, Any],
    revenue: dict[str, Any],
) -> dict[str, Any]:
    """Daily Report全体の短い要約を作る。"""

    status = "normal"
    requires_attention = False
    messages = []

    if (
        system.get(
            "status"
        )
        != "success"
    ):
        status = "error"
        requires_attention = True
        messages.append(
            "Atlasの最新実行が"
            "successではありません。"
        )

    elif (
        system.get(
            "health"
        )
        != "healthy"
    ):
        status = "warning"
        requires_attention = True
        messages.append(
            "Atlas Healthが"
            "healthyではありません。"
        )

    elif system.get(
        "lock_active"
    ):
        status = "warning"
        requires_attention = True
        messages.append(
            "Atlas Lockが残っています。"
        )

    if (
        editorial.get(
            "action"
        )
        in {
            "new_article",
            "rewrite_article",
        }
    ):
        requires_attention = True
        messages.append(
            "AI編集長が"
            f"{editorial.get('action')} "
            "を選択しました。"
        )

    top_action = revenue.get(
        "top_action",
        {},
    )

    if isinstance(
        top_action,
        dict,
    ):
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
            requires_attention = True

            messages.append(
                "Revenue Actionがあります："
                + str(
                    top_action.get(
                        "service",
                        "",
                    )
                )
            )

    if (
        revenue.get(
            "conversions",
            0,
        )
        > 0
    ):
        requires_attention = True

        messages.append(
            "Affiliate成果が発生しています。"
        )

    if not messages:
        messages.append(
            "Atlasは正常終了し、"
            "緊急対応はありません。"
        )

    return {
        "status": status,
        "requires_attention":
            requires_attention,
        "messages": messages,
    }


def build_daily_report(
) -> dict[str, Any]:
    """Atlas Daily Report全体を生成する。"""

    latest_run = load_json(
        LATEST_RUN_FILE
    )

    health = load_json(
        HEALTH_STATUS_FILE
    )

    dashboard = load_json(
        DASHBOARD_FILE
    )

    editorial_data = load_json(
        EDITORIAL_DECISION_FILE
    )

    revenue_data = load_json(
        REVENUE_SUMMARY_FILE
    )

    search_console = load_json(
        SEARCH_CONSOLE_SUMMARY_FILE
    )

    system = build_system_section(
        latest_run,
        health,
        dashboard,
    )

    editorial = (
        build_editorial_section(
            editorial_data
        )
    )

    seo = build_seo_section(
        search_console,
        dashboard,
    )

    revenue = build_revenue_section(
        revenue_data,
        dashboard,
    )

    portfolio = (
        build_portfolio_section(
            dashboard
        )
    )

    summary = build_summary(
        system,
        editorial,
        seo,
        revenue,
    )

    return {
        "generated_at":
            datetime.now().isoformat(),
        "system": system,
        "editorial": editorial,
        "seo": seo,
        "revenue": revenue,
        "portfolio": portfolio,
        "summary": summary,
    }


def save_daily_report(
    report: dict[str, Any],
) -> Path:
    """Daily ReportをJSON保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_daily_report(
    report: dict[str, Any],
) -> None:
    """Daily Reportをコンソール表示する。"""

    system = report[
        "system"
    ]

    editorial = report[
        "editorial"
    ]

    seo = report[
        "seo"
    ]

    revenue = report[
        "revenue"
    ]

    summary = report[
        "summary"
    ]

    print(
        "\n===== Atlas Daily Report =====\n"
    )

    print("SYSTEM")
    print(
        "Status："
        f"{system['status']}"
    )
    print(
        "Health："
        f"{system['health']}"
    )
    print(
        "Action："
        f"{system['action']}"
    )
    print(
        "Lock："
        + (
            "ON"
            if system["lock_active"]
            else "OFF"
        )
    )

    print(
        "\nEDITORIAL"
    )
    print(
        "Action："
        f"{editorial['action']}"
    )
    print(
        "Priority："
        f"{editorial['priority_score']}"
    )

    print(
        "\nSEO"
    )
    print(
        "Clicks："
        f"{seo['clicks']:.0f}"
    )
    print(
        "Impressions："
        f"{seo['impressions']:.0f}"
    )
    print(
        "CTR："
        f"{seo['ctr']:.2%}"
    )
    print(
        "Average Position："
        f"{seo['average_position']:.2f}"
    )
    print(
        "Ready Actions："
        f"{seo['ready_actions']}"
    )

    print(
        "\nREVENUE"
    )
    print(
        "Affiliate Clicks："
        f"{revenue['clicks']}"
    )
    print(
        "Conversions："
        f"{revenue['conversions']}"
    )
    print(
        "Revenue："
        f"{revenue['revenue']}"
    )
    print(
        "CVR："
        f"{revenue['conversion_rate']:.2%}"
    )
    print(
        "EPC："
        f"{revenue['epc']:.2f}"
    )

    top_action = revenue.get(
        "top_action",
        {},
    )

    if isinstance(
        top_action,
        dict,
    ) and top_action:

        print(
            "\nTOP REVENUE ACTION"
        )

        print(
            "Service："
            f"{top_action.get('service', '')}"
        )

        print(
            "Action："
            f"{top_action.get('source_action', '')}"
        )

        print(
            "Priority："
            f"{top_action.get('priority', 0)}"
        )

        print(
            "Next："
            f"{top_action.get('next', '')}"
        )

    print(
        "\nSUMMARY"
    )

    print(
        "Status："
        f"{summary['status']}"
    )

    print(
        "Requires Attention："
        + (
            "YES"
            if summary[
                "requires_attention"
            ]
            else "NO"
        )
    )

    for message in summary[
        "messages"
    ]:
        print(
            f"- {message}"
        )

    print()


def main() -> None:
    report = (
        build_daily_report()
    )

    filepath = (
        save_daily_report(
            report
        )
    )

    print_daily_report(
        report
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()