import json
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

EDITORIAL_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "editorial"
    / "latest_decision.json"
)

SEO_ACTION_PLAN_FILE = (
    BASE_DIR
    / "data"
    / "seo_feedback"
    / "seo_action_plan.json"
)

REVENUE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_summary.json"
)

PORTFOLIO_PLAN_FILE = (
    BASE_DIR
    / "data"
    / "portfolio"
    / "portfolio_plan.json"
)

LOCK_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "atlas.lock"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "dashboard"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "dashboard.json"
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
) -> dict[str, Any]:
    """Atlas全体の稼働状態をまとめる。"""

    latest_run = load_json(
        LATEST_RUN_FILE
    )

    health = load_json(
        HEALTH_STATUS_FILE
    )

    return {
        "health":
            health.get(
                "health",
                "unknown",
            ),
        "health_reason":
            health.get(
                "reason",
                "",
            ),
        "last_run":
            latest_run.get(
                "finished_at",
                "",
            ),
        "last_status":
            latest_run.get(
                "status",
                "",
            ),
        "last_action":
            latest_run.get(
                "action",
                "",
            ),
        "last_message":
            latest_run.get(
                "message",
                "",
            ),
        "lock_active":
            LOCK_FILE.exists(),
    }


def build_editorial_section(
) -> dict[str, Any]:
    """AI編集長の最新判断をまとめる。"""

    decision = load_json(
        EDITORIAL_DECISION_FILE
    )

    return {
        "action":
            decision.get(
                "action",
                "",
            ),
        "priority_score":
            decision.get(
                "priority_score",
                0,
            ),
        "reason":
            decision.get(
                "reason",
                "",
            ),
        "target_keyword":
            decision.get(
                "target_keyword",
                "",
            ),
        "target_slug":
            decision.get(
                "target_slug",
                "",
            ),
        "target_title":
            decision.get(
                "target_title",
                "",
            ),
        "monetization_opportunity":
            decision.get(
                "monetization_opportunity",
                "",
            ),
        "expected_effect":
            decision.get(
                "expected_effect",
                "",
            ),
    }


def build_seo_section(
) -> dict[str, Any]:
    """SEO Action Planの状態をまとめる。"""

    data = load_json(
        SEO_ACTION_PLAN_FILE
    )

    plans = data.get(
        "plans",
        [],
    )

    if not isinstance(
        plans,
        list,
    ):
        plans = []

    ready_count = 0
    waiting_count = 0

    action_counts: dict[
        str,
        int,
    ] = {}

    for item in plans:
        if not isinstance(
            item,
            dict,
        ):
            continue

        status = str(
            item.get(
                "status",
                "",
            )
        ).strip()

        if status == "ready":
            ready_count += 1
        elif status == "waiting":
            waiting_count += 1

        planned_action = str(
            item.get(
                "planned_action",
                "",
            )
        ).strip()

        if planned_action:
            action_counts[
                planned_action
            ] = (
                action_counts.get(
                    planned_action,
                    0,
                )
                + 1
            )

    return {
        "tracked_articles":
            len(plans),
        "ready_actions":
            ready_count,
        "waiting_actions":
            waiting_count,
        "action_counts":
            action_counts,
    }


def build_revenue_section(
) -> dict[str, Any]:
    """Revenue Summaryをまとめる。"""

    data = load_json(
        REVENUE_SUMMARY_FILE
    )

    by_article = data.get(
        "by_article",
        {},
    )

    if not isinstance(
        by_article,
        dict,
    ):
        by_article = {}

    top_articles = []

    for slug, item in by_article.items():
        if not isinstance(
            item,
            dict,
        ):
            continue

        top_articles.append(
            {
                "slug": slug,
                "clicks": int(
                    item.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
                "conversions": int(
                    item.get(
                        "conversions",
                        0,
                    )
                    or 0
                ),
                "revenue": float(
                    item.get(
                        "revenue",
                        0,
                    )
                    or 0
                ),
            }
        )

    top_articles.sort(
        key=lambda item: (
            item["revenue"],
            item["clicks"],
        ),
        reverse=True,
    )

    return {
        "affiliate_clicks":
            int(
                data.get(
                    "total_clicks",
                    0,
                )
                or 0
            ),
        "conversions":
            int(
                data.get(
                    "total_conversions",
                    0,
                )
                or 0
            ),
        "revenue":
            float(
                data.get(
                    "total_revenue",
                    0,
                )
                or 0
            ),
        "conversion_rate":
            float(
                data.get(
                    "conversion_rate",
                    0,
                )
                or 0
            ),
        "tracked_articles":
            len(by_article),
        "top_articles":
            top_articles[:5],
    }


def build_portfolio_section(
) -> dict[str, Any]:
    """Portfolio Planをまとめる。"""

    data = load_json(
        PORTFOLIO_PLAN_FILE
    )

    summary = data.get(
        "summary",
        {},
    )

    articles = data.get(
        "articles",
        [],
    )

    if not isinstance(
        summary,
        dict,
    ):
        summary = {}

    if not isinstance(
        articles,
        list,
    ):
        articles = []

    investment_counts = {
        "invest": 0,
        "maintain": 0,
        "observe": 0,
        "deprioritize": 0,
    }

    top_articles = []

    for item in articles:
        if not isinstance(
            item,
            dict,
        ):
            continue

        level = str(
            item.get(
                "investment_level",
                "",
            )
        ).strip()

        if level in investment_counts:
            investment_counts[
                level
            ] += 1

        top_articles.append(
            {
                "slug":
                    item.get(
                        "slug",
                        "",
                    ),
                "score":
                    item.get(
                        "portfolio_score",
                        0,
                    ),
                "investment_level":
                    level,
                "planned_action":
                    item.get(
                        "planned_action",
                        "",
                    ),
                "execution_allowed":
                    bool(
                        item.get(
                            "execution_allowed",
                            False,
                        )
                    ),
            }
        )

    top_articles.sort(
        key=lambda item: float(
            item.get(
                "score",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    return {
        "evaluated_articles":
            int(
                summary.get(
                    "article_count",
                    len(articles),
                )
                or 0
            ),
        "executable_count":
            int(
                summary.get(
                    "executable_count",
                    0,
                )
                or 0
            ),
        "investment_counts":
            investment_counts,
        "top_articles":
            top_articles[:5],
        "execution_limits": {
            "total":
                summary.get(
                    "max_total_actions_per_run",
                    0,
                ),
            "rewrite":
                summary.get(
                    "max_rewrites_per_run",
                    0,
                ),
            "strengthen":
                summary.get(
                    "max_strengthens_per_run",
                    0,
                ),
            "title":
                summary.get(
                    "max_title_updates_per_run",
                    0,
                ),
        },
    }


def evaluate_overall_status(
    system: dict[str, Any],
) -> str:
    """Dashboard全体の状態を判定する。"""

    health = str(
        system.get(
            "health",
            "",
        )
    ).strip()

    lock_active = bool(
        system.get(
            "lock_active",
            False,
        )
    )

    if health == "error":
        return "error"

    if health == "warning":
        return "warning"

    if lock_active:
        return "running"

    if health == "healthy":
        return "ok"

    return "unknown"


def build_dashboard(
) -> dict[str, Any]:
    """Atlas Dashboard全体を生成する。"""

    system = (
        build_system_section()
    )

    editorial = (
        build_editorial_section()
    )

    seo = (
        build_seo_section()
    )

    revenue = (
        build_revenue_section()
    )

    portfolio = (
        build_portfolio_section()
    )

    return {
        "overall_status":
            evaluate_overall_status(
                system
            ),
        "system":
            system,
        "editorial":
            editorial,
        "seo":
            seo,
        "revenue":
            revenue,
        "portfolio":
            portfolio,
    }


def save_dashboard(
    data: dict[str, Any],
) -> Path:
    """Dashboard JSONを保存する。"""

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


def print_dashboard(
    data: dict[str, Any],
) -> None:
    """コンソールへDashboardを表示する。"""

    system = data.get(
        "system",
        {},
    )

    editorial = data.get(
        "editorial",
        {},
    )

    seo = data.get(
        "seo",
        {},
    )

    revenue = data.get(
        "revenue",
        {},
    )

    portfolio = data.get(
        "portfolio",
        {},
    )

    print(
        "\n===== Atlas Dashboard =====\n"
    )

    print(
        "OVERALL"
    )

    print(
        "Status："
        f"{data.get('overall_status')}"
    )

    print()

    print(
        "SYSTEM"
    )

    print(
        "Health："
        f"{system.get('health')}"
    )

    print(
        "Last Run："
        f"{system.get('last_run')}"
    )

    print(
        "Last Action："
        f"{system.get('last_action')}"
    )

    print(
        "Lock："
        f"{'ON' if system.get('lock_active') else 'OFF'}"
    )

    print()

    print(
        "EDITORIAL"
    )

    print(
        "Action："
        f"{editorial.get('action')}"
    )

    print(
        "Priority："
        f"{editorial.get('priority_score')}"
    )

    print()

    print(
        "SEO"
    )

    print(
        "Tracked Articles："
        f"{seo.get('tracked_articles')}"
    )

    print(
        "Ready Actions："
        f"{seo.get('ready_actions')}"
    )

    print()

    print(
        "REVENUE"
    )

    print(
        "Affiliate Clicks："
        f"{revenue.get('affiliate_clicks')}"
    )

    print(
        "Conversions："
        f"{revenue.get('conversions')}"
    )

    print(
        "Revenue："
        f"{revenue.get('revenue')}"
    )

    print()

    print(
        "PORTFOLIO"
    )

    print(
        "Evaluated Articles："
        f"{portfolio.get('evaluated_articles')}"
    )

    print(
        "Executable："
        f"{portfolio.get('executable_count')}"
    )

    counts = portfolio.get(
        "investment_counts",
        {},
    )

    print(
        "Invest："
        f"{counts.get('invest', 0)}"
    )

    print(
        "Maintain："
        f"{counts.get('maintain', 0)}"
    )

    print(
        "Observe："
        f"{counts.get('observe', 0)}"
    )

    print(
        "Deprioritize："
        f"{counts.get('deprioritize', 0)}"
    )

    print()


def main() -> None:
    data = (
        build_dashboard()
    )

    filepath = (
        save_dashboard(
            data
        )
    )

    print_dashboard(
        data
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()