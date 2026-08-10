import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

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

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "portfolio"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "portfolio_plan.json"
)


# ============================================================
# Phase 48 safety / budget settings
# ============================================================

MAX_REWRITES_PER_RUN = 1
MAX_STRENGTHENS_PER_RUN = 2
MAX_TITLE_UPDATES_PER_RUN = 2

MAX_TOTAL_ACTIONS_PER_RUN = 3


def load_seo_action_plan(
) -> list[dict[str, Any]]:
    """SEO Action Planを読み込む。"""

    if not SEO_ACTION_PLAN_FILE.exists():
        return []

    try:
        data = json.loads(
            SEO_ACTION_PLAN_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "seo_action_plan.jsonの"
            "JSON形式が不正です。"
        ) from error

    plans = data.get(
        "plans",
        [],
    )

    if not isinstance(
        plans,
        list,
    ):
        raise ValueError(
            "plansは配列にしてください。"
        )

    return [
        item
        for item in plans
        if isinstance(
            item,
            dict,
        )
    ]


def load_revenue_summary(
) -> dict[str, Any]:
    """Revenue Summaryを読み込む。"""

    if not REVENUE_SUMMARY_FILE.exists():
        return {
            "by_article": {},
        }

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

    by_article = data.get(
        "by_article",
        {},
    )

    if not isinstance(
        by_article,
        dict,
    ):
        by_article = {}

    return {
        **data,
        "by_article": by_article,
    }


def normalize_score(
    value: float,
    maximum: float,
) -> float:
    """0～100へ正規化する。"""

    if maximum <= 0:
        return 0.0

    score = (
        value
        / maximum
        * 100.0
    )

    return min(
        max(
            score,
            0.0,
        ),
        100.0,
    )


def calculate_seo_score(
    item: dict[str, Any],
) -> float:
    """SEO側の投資価値を0～100で評価する。"""

    seo_priority = float(
        item.get(
            "seo_priority",
            0,
        )
        or 0
    )

    impressions = float(
        item.get(
            "impressions",
            0,
        )
        or 0
    )

    clicks = float(
        item.get(
            "clicks",
            0,
        )
        or 0
    )

    position = float(
        item.get(
            "position",
            0,
        )
        or 0
    )

    planned_action = str(
        item.get(
            "planned_action",
            "",
        )
    ).strip()

    score = 0.0

    # SEO Feedback由来のpriority
    score += min(
        seo_priority,
        100.0,
    ) * 0.40

    # 表示回数
    impression_score = (
        normalize_score(
            impressions,
            100.0,
        )
    )

    score += (
        impression_score
        * 0.20
    )

    # Search Consoleクリック
    click_score = (
        normalize_score(
            clicks,
            10.0,
        )
    )

    score += (
        click_score
        * 0.15
    )

    # 順位による成長余地
    position_score = 0.0

    if 1 <= position <= 3:
        position_score = 45.0
    elif position <= 10:
        position_score = 100.0
    elif position <= 20:
        position_score = 90.0
    elif position <= 50:
        position_score = 60.0
    elif position > 50:
        position_score = 30.0

    score += (
        position_score
        * 0.15
    )

    # すでにSEO側が実行可能判定なら加点
    if planned_action in {
        "title_only",
        "strengthen",
        "rewrite",
    }:
        score += 10.0

    return min(
        score,
        100.0,
    )


def calculate_revenue_score(
    revenue_item: dict[str, Any],
) -> float:
    """Revenue側の投資価値を0～100で評価する。"""

    clicks = float(
        revenue_item.get(
            "clicks",
            0,
        )
        or 0
    )

    conversions = float(
        revenue_item.get(
            "conversions",
            0,
        )
        or 0
    )

    revenue = float(
        revenue_item.get(
            "revenue",
            0,
        )
        or 0
    )

    conversion_rate = float(
        revenue_item.get(
            "conversion_rate",
            0,
        )
        or 0
    )

    score = 0.0

    # Affiliate CTAクリック
    score += (
        normalize_score(
            clicks,
            10.0,
        )
        * 0.35
    )

    # 成果件数
    score += (
        normalize_score(
            conversions,
            3.0,
        )
        * 0.30
    )

    # 収益
    score += (
        normalize_score(
            revenue,
            5000.0,
        )
        * 0.25
    )

    # CVR
    score += (
        normalize_score(
            conversion_rate,
            0.10,
        )
        * 0.10
    )

    return min(
        score,
        100.0,
    )


def calculate_portfolio_score(
    seo_score: float,
    revenue_score: float,
) -> float:
    """SEOと収益を統合したPortfolio Scoreを算出する。"""

    # 現段階ではSEOデータがまだ少ないため
    # Revenueシグナルも強めに評価する。
    score = (
        seo_score
        * 0.60
        + revenue_score
        * 0.40
    )

    return round(
        score,
        2,
    )


def decide_investment_level(
    portfolio_score: float,
    planned_action: str,
    affiliate_clicks: int,
) -> str:
    """記事への投資レベルを決定する。"""

    if (
        portfolio_score >= 65
        and planned_action != "wait"
    ):
        return "invest"

    if portfolio_score >= 40:
        return "maintain"

    # SEOデータが少なくても
    # Affiliate Clickがある記事は捨てない
    if affiliate_clicks > 0:
        return "observe"

    if portfolio_score >= 20:
        return "observe"

    return "deprioritize"


def build_portfolio_candidates(
    seo_plans: list[dict[str, Any]],
    revenue_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """SEOとRevenueを統合して記事候補を生成する。"""

    revenue_by_article = (
        revenue_summary.get(
            "by_article",
            {},
        )
    )

    seo_by_slug: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in seo_plans:
        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        if slug:
            seo_by_slug[
                slug
            ] = item

    all_slugs = set(
        seo_by_slug.keys()
    )

    all_slugs.update(
        str(slug)
        for slug
        in revenue_by_article.keys()
    )

    candidates: list[
        dict[str, Any]
    ] = []

    for slug in sorted(
        all_slugs
    ):
        seo_item = (
            seo_by_slug.get(
                slug,
                {},
            )
        )

        revenue_item = (
            revenue_by_article.get(
                slug,
                {},
            )
        )

        seo_score = (
            calculate_seo_score(
                seo_item
            )
        )

        revenue_score = (
            calculate_revenue_score(
                revenue_item
            )
        )

        portfolio_score = (
            calculate_portfolio_score(
                seo_score,
                revenue_score,
            )
        )

        planned_action = str(
            seo_item.get(
                "planned_action",
                "wait",
            )
        ).strip()

        affiliate_clicks = int(
            revenue_item.get(
                "clicks",
                0,
            )
            or 0
        )

        investment_level = (
            decide_investment_level(
                portfolio_score,
                planned_action,
                affiliate_clicks,
            )
        )

        candidates.append(
            {
                "slug": slug,
                "portfolio_score":
                    portfolio_score,
                "seo_score": round(
                    seo_score,
                    2,
                ),
                "revenue_score": round(
                    revenue_score,
                    2,
                ),
                "investment_level":
                    investment_level,
                "planned_action":
                    planned_action,
                "seo_priority": int(
                    seo_item.get(
                        "seo_priority",
                        0,
                    )
                    or 0
                ),
                "impressions": float(
                    seo_item.get(
                        "impressions",
                        0,
                    )
                    or 0
                ),
                "search_clicks": float(
                    seo_item.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
                "position": float(
                    seo_item.get(
                        "position",
                        0,
                    )
                    or 0
                ),
                "affiliate_clicks":
                    affiliate_clicks,
                "conversions": int(
                    revenue_item.get(
                        "conversions",
                        0,
                    )
                    or 0
                ),
                "revenue": float(
                    revenue_item.get(
                        "revenue",
                        0,
                    )
                    or 0
                ),
                "conversion_rate":
                    float(
                        revenue_item.get(
                            "conversion_rate",
                            0,
                        )
                        or 0
                    ),
            }
        )

    candidates.sort(
        key=lambda item: (
            float(
                item.get(
                    "portfolio_score",
                    0,
                )
            )
        ),
        reverse=True,
    )

    return candidates


def apply_execution_budget(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """1回のAtlas実行で許可する処理数を制限する。"""

    rewrite_count = 0
    strengthen_count = 0
    title_count = 0
    total_actions = 0

    results: list[
        dict[str, Any]
    ] = []

    for item in candidates:
        planned_action = str(
            item.get(
                "planned_action",
                "wait",
            )
        )

        investment_level = str(
            item.get(
                "investment_level",
                "observe",
            )
        )

        allowed = False
        budget_reason = ""

        if planned_action == "wait":
            budget_reason = (
                "SEO Action Planがwaitのため"
                "実行しません。"
            )

        elif investment_level not in {
            "invest",
            "maintain",
        }:
            budget_reason = (
                "Portfolio評価が"
                "実行基準未満です。"
            )

        elif (
            total_actions
            >= MAX_TOTAL_ACTIONS_PER_RUN
        ):
            budget_reason = (
                "1回あたりの総実行上限に"
                "達しました。"
            )

        elif planned_action == "rewrite":
            if (
                rewrite_count
                < MAX_REWRITES_PER_RUN
            ):
                allowed = True
                rewrite_count += 1
            else:
                budget_reason = (
                    "rewrite上限に"
                    "達しました。"
                )

        elif planned_action == "strengthen":
            if (
                strengthen_count
                < MAX_STRENGTHENS_PER_RUN
            ):
                allowed = True
                strengthen_count += 1
            else:
                budget_reason = (
                    "strengthen上限に"
                    "達しました。"
                )

        elif planned_action == "title_only":
            if (
                title_count
                < MAX_TITLE_UPDATES_PER_RUN
            ):
                allowed = True
                title_count += 1
            else:
                budget_reason = (
                    "title更新上限に"
                    "達しました。"
                )

        else:
            budget_reason = (
                "安全のため未対応の"
                "actionは実行しません。"
            )

        if allowed:
            total_actions += 1

            budget_reason = (
                "Portfolio評価と"
                "実行予算の範囲内です。"
            )

        result = dict(
            item
        )

        result[
            "execution_allowed"
        ] = allowed

        result[
            "budget_reason"
        ] = budget_reason

        results.append(
            result
        )

    return results


def build_portfolio_plan(
) -> dict[str, Any]:
    """Portfolio Plan全体を作成する。"""

    seo_plans = (
        load_seo_action_plan()
    )

    revenue_summary = (
        load_revenue_summary()
    )

    candidates = (
        build_portfolio_candidates(
            seo_plans,
            revenue_summary,
        )
    )

    candidates = (
        apply_execution_budget(
            candidates
        )
    )

    executable = [
        item
        for item in candidates
        if item.get(
            "execution_allowed"
        )
    ]

    return {
        "summary": {
            "article_count":
                len(candidates),
            "executable_count":
                len(executable),
            "max_total_actions_per_run":
                MAX_TOTAL_ACTIONS_PER_RUN,
            "max_rewrites_per_run":
                MAX_REWRITES_PER_RUN,
            "max_strengthens_per_run":
                MAX_STRENGTHENS_PER_RUN,
            "max_title_updates_per_run":
                MAX_TITLE_UPDATES_PER_RUN,
        },
        "articles": candidates,
    }


def save_portfolio_plan(
    data: dict[str, Any],
) -> Path:
    """Portfolio Planを保存する。"""

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


def print_portfolio_plan(
    data: dict[str, Any],
) -> None:
    """Portfolio Planを表示する。"""

    print(
        "\n===== Portfolio Optimizer =====\n"
    )

    summary = data.get(
        "summary",
        {},
    )

    print(
        "評価記事数："
        f"{summary.get('article_count', 0)}"
    )

    print(
        "今回実行可能："
        f"{summary.get('executable_count', 0)}"
    )

    print()

    articles = data.get(
        "articles",
        [],
    )

    for item in articles:
        status = (
            "EXECUTE"
            if item.get(
                "execution_allowed"
            )
            else "SKIP"
        )

        print(
            f"{status} / "
            f"{item.get('slug', '')} / "
            f"score="
            f"{item.get('portfolio_score', 0)} / "
            f"{item.get('investment_level', '')} / "
            f"{item.get('planned_action', '')}"
        )


def main() -> None:
    data = (
        build_portfolio_plan()
    )

    filepath = (
        save_portfolio_plan(
            data
        )
    )

    print_portfolio_plan(
        data
    )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()