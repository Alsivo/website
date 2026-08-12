import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

SEO_ACTION_PLAN_FILE = (
    BASE_DIR
    / "data"
    / "seo_feedback"
    / "seo_action_plan.json"
)

REVENUE_ACTION_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_action_queue.json"
)

PORTFOLIO_PLAN_FILE = (
    BASE_DIR
    / "data"
    / "portfolio"
    / "portfolio_plan.json"
)

PERFORMANCE_TREND_FILE = (
    BASE_DIR
    / "data"
    / "performance_history"
    / "trend.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "optimization"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "optimization_decision.json"
)


# ============================================================
# Action priority
# ============================================================

ACTION_BASE_PRIORITY = {
    "MONETIZE": 100,
    "IMPROVE_CTA": 80,
    "REWRITE": 70,
    "STRENGTHEN": 60,
    "TITLE_ONLY": 50,
    "EXPAND_CONTENT": 40,
    "WAIT": 0,
}


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "JSON形式が不正です："
            f"{filepath}"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "JSONの最上位は"
            "オブジェクトにしてください："
            f"{filepath}"
        )

    return data


def get_trend_state(
    trend: dict[str, Any],
) -> str:
    """Performance Trend全体の状態を取得する。"""

    status = str(
        trend.get(
            "status",
            "",
        )
    ).strip()

    if status != "ready":
        return "insufficient_data"

    previous_trend = trend.get(
        "previous_trend",
        {},
    )

    if isinstance(
        previous_trend,
        dict,
    ):
        overall = str(
            previous_trend.get(
                "overall",
                "",
            )
        ).strip()

        if overall in {
            "improving",
            "stable",
            "declining",
        }:
            return overall

    return "insufficient_data"


def build_portfolio_map(
    portfolio: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Portfolio Planをslug単位の辞書に変換する。"""

    articles = portfolio.get(
        "articles",
        [],
    )

    if not isinstance(
        articles,
        list,
    ):
        return {}

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in articles:
        if not isinstance(
            item,
            dict,
        ):
            continue

        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        if not slug:
            continue

        result[
            slug
        ] = item

    return result


def trend_priority_adjustment(
    action: str,
    trend_state: str,
) -> int:
    """Trendに応じてPriorityを補正する。"""

    if trend_state == "declining":
        if action in {
            "REWRITE",
            "STRENGTHEN",
            "TITLE_ONLY",
            "IMPROVE_CTA",
        }:
            return 10

        if action == "EXPAND_CONTENT":
            return -20

    elif trend_state == "improving":
        if action == "REWRITE":
            return -10

        if action == "EXPAND_CONTENT":
            return 5

    elif trend_state == "insufficient_data":
        if action == "REWRITE":
            return -20

        if action == "EXPAND_CONTENT":
            return -20

    return 0


def build_revenue_candidates(
    revenue_queue: dict[str, Any],
    trend_state: str,
) -> list[dict[str, Any]]:
    """Revenue ActionからOptimization候補を作る。"""

    actions = revenue_queue.get(
        "actions",
        [],
    )

    if not isinstance(
        actions,
        list,
    ):
        return []

    candidates: list[
        dict[str, Any]
    ] = []

    for item in actions:
        if not isinstance(
            item,
            dict,
        ):
            continue

        source_action = str(
            item.get(
                "source_action",
                "",
            )
        ).strip()

        destination = str(
            item.get(
                "destination",
                "",
            )
        ).strip()

        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        source_priority = int(
            item.get(
                "priority",
                0,
            )
            or 0
        )

        action = ""

        execution_mode = (
            "human_action"
        )

        execution_allowed = False

        blocked_reason = ""

        if (
            source_action == "MONETIZE"
            and destination == "monetization"
        ):
            action = "MONETIZE"

        elif (
            source_action == "IMPROVE_CTA"
            and destination == "cta"
        ):
            action = "IMPROVE_CTA"

            # CTAは記事単位との対応付けが
            # 現段階では存在しないため、
            # G5までは自動実行しない。
            blocked_reason = (
                "Revenue Actionはservice単位であり、"
                "対象記事slugが確定していないため"
                "自動実行しません。"
            )

        elif (
            source_action == "EXPAND_CONTENT"
            and destination == "content"
        ):
            action = "EXPAND_CONTENT"

            if (
                trend_state
                == "declining"
            ):
                blocked_reason = (
                    "Performance Trendが"
                    "decliningのため、"
                    "記事拡張を抑制します。"
                )

            elif (
                trend_state
                == "insufficient_data"
            ):
                blocked_reason = (
                    "Performance Trendの"
                    "データが不足しているため、"
                    "記事拡張を抑制します。"
                )

        else:
            continue

        base_priority = (
            ACTION_BASE_PRIORITY.get(
                action,
                0,
            )
        )

        trend_adjustment = (
            trend_priority_adjustment(
                action,
                trend_state,
            )
        )

        final_priority = min(
            100,
            max(
                0,
                round(
                    source_priority
                    * 0.7
                    + base_priority
                    * 0.3
                    + trend_adjustment
                ),
            ),
        )

        candidates.append(
            {
                "action":
                    action,
                "source":
                    "revenue",
                "target_type":
                    "service",
                "target":
                    service,
                "priority":
                    final_priority,
                "source_priority":
                    source_priority,
                "base_priority":
                    base_priority,
                "trend_adjustment":
                    trend_adjustment,
                "execution_mode":
                    execution_mode,
                "execution_allowed":
                    execution_allowed,
                "blocked_reason":
                    blocked_reason,
                "reason":
                    str(
                        item.get(
                            "reason",
                            "",
                        )
                    ).strip(),
                "recommended_action":
                    str(
                        item.get(
                            "next",
                            "",
                        )
                    ).strip(),
                "metadata": {
                    "destination":
                        destination,
                    "next_engine":
                        str(
                            item.get(
                                "next_engine",
                                "",
                            )
                        ).strip(),
                    "clicks":
                        int(
                            item.get(
                                "clicks",
                                0,
                            )
                            or 0
                        ),
                    "conversions":
                        int(
                            item.get(
                                "conversions",
                                0,
                            )
                            or 0
                        ),
                    "revenue":
                        float(
                            item.get(
                                "revenue",
                                0,
                            )
                            or 0
                        ),
                    "epc":
                        float(
                            item.get(
                                "epc",
                                0,
                            )
                            or 0
                        ),
                },
            }
        )

    return candidates


def build_seo_candidates(
    seo_plan: dict[str, Any],
    portfolio: dict[str, Any],
    trend_state: str,
) -> list[dict[str, Any]]:
    """SEO Action PlanからOptimization候補を作る。"""

    plans = seo_plan.get(
        "plans",
        [],
    )

    if not isinstance(
        plans,
        list,
    ):
        return []

    portfolio_map = (
        build_portfolio_map(
            portfolio
        )
    )

    candidates: list[
        dict[str, Any]
    ] = []

    action_map = {
        "rewrite":
            "REWRITE",
        "strengthen":
            "STRENGTHEN",
        "title_only":
            "TITLE_ONLY",
    }

    for item in plans:
        if not isinstance(
            item,
            dict,
        ):
            continue

        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        planned_action = str(
            item.get(
                "planned_action",
                "wait",
            )
        ).strip()

        action = action_map.get(
            planned_action
        )

        if not action:
            continue

        portfolio_item = (
            portfolio_map.get(
                slug,
                {},
            )
        )

        execution_allowed = bool(
            portfolio_item.get(
                "execution_allowed",
                False,
            )
        )

        source_priority = int(
            item.get(
                "seo_priority",
                0,
            )
            or 0
        )

        portfolio_score = float(
            portfolio_item.get(
                "portfolio_score",
                0,
            )
            or 0
        )

        base_priority = (
            ACTION_BASE_PRIORITY.get(
                action,
                0,
            )
        )

        trend_adjustment = (
            trend_priority_adjustment(
                action,
                trend_state,
            )
        )

        final_priority = min(
            100,
            max(
                0,
                round(
                    source_priority
                    * 0.5
                    + portfolio_score
                    * 0.2
                    + base_priority
                    * 0.3
                    + trend_adjustment
                ),
            ),
        )

        if (
            action == "REWRITE"
            and trend_state
            == "insufficient_data"
        ):
            execution_allowed = False
            execution_mode = "blocked"
            blocked_reason = (
                "Performance Trendの"
                "データが不足しているため、"
                "rewriteは実行しません。"
            )

        elif execution_allowed:
            execution_mode = "auto_candidate"
            blocked_reason = ""

        else:
            execution_mode = "blocked"
            blocked_reason = str(
                portfolio_item.get(
                    "budget_reason",
                    (
                        "Portfolio Planで"
                        "実行が許可されていません。"
                    ),
                )
            ).strip()

        candidates.append(
            {
                "action":
                    action,
                "source":
                    "seo",
                "target_type":
                    "article",
                "target":
                    slug,
                "priority":
                    final_priority,
                "source_priority":
                    source_priority,
                "base_priority":
                    base_priority,
                "trend_adjustment":
                    trend_adjustment,
                "execution_mode":
                    execution_mode,
                "execution_allowed":
                    execution_allowed,
                "blocked_reason":
                    blocked_reason,
                "reason":
                    str(
                        item.get(
                            "action_reason",
                            "",
                        )
                    ).strip(),
                "recommended_action":
                    planned_action,
                "metadata": {
                    "portfolio_score":
                        portfolio_score,
                    "investment_level":
                        str(
                            portfolio_item.get(
                                "investment_level",
                                "",
                            )
                        ),
                    "impressions":
                        float(
                            item.get(
                                "impressions",
                                0,
                            )
                            or 0
                        ),
                    "clicks":
                        float(
                            item.get(
                                "clicks",
                                0,
                            )
                            or 0
                        ),
                    "ctr":
                        float(
                            item.get(
                                "ctr",
                                0,
                            )
                            or 0
                        ),
                    "position":
                        float(
                            item.get(
                                "position",
                                0,
                            )
                            or 0
                        ),
                },
            }
        )

    return candidates


def candidate_sort_key(
    candidate: dict[str, Any],
) -> tuple[int, int, int, float]:
    """Optimization候補の並び順を作る。"""

    action = str(
        candidate.get(
            "action",
            "WAIT",
        )
    )

    action_rank = {
        "MONETIZE": 7,
        "IMPROVE_CTA": 6,
        "REWRITE": 5,
        "STRENGTHEN": 4,
        "TITLE_ONLY": 3,
        "EXPAND_CONTENT": 2,
        "WAIT": 1,
    }.get(
        action,
        0,
    )

    priority = int(
        candidate.get(
            "priority",
            0,
        )
        or 0
    )

    execution_rank = (
        1
        if candidate.get(
            "execution_allowed"
        )
        else 0
    )

    metadata = candidate.get(
        "metadata",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    demand_score = float(
        metadata.get(
            "clicks",
            0,
        )
        or 0
    )

    return (
        priority,
        action_rank,
        execution_rank,
        demand_score,
    )


def build_wait_decision(
    trend_state: str,
) -> dict[str, Any]:
    """有効候補がない場合のWAIT判断を作る。"""

    return {
        "action":
            "WAIT",
        "source":
            "system",
        "target_type":
            "none",
        "target":
            "",
        "priority":
            0,
        "source_priority":
            0,
        "base_priority":
            0,
        "trend_adjustment":
            0,
        "execution_mode":
            "none",
        "execution_allowed":
            False,
        "blocked_reason":
            "",
        "reason":
            (
                "現在実行すべき"
                "Optimization候補がありません。"
            ),
        "recommended_action":
            (
                "データ蓄積を継続して"
                "次回判断を待つ"
            ),
        "metadata": {},
        "trend_state":
            trend_state,
    }


def build_optimization_decision(
    seo_plan: dict[str, Any],
    revenue_queue: dict[str, Any],
    portfolio: dict[str, Any],
    trend: dict[str, Any],
) -> dict[str, Any]:
    """Optimization Decision全体を生成する。"""

    trend_state = (
        get_trend_state(
            trend
        )
    )

    revenue_candidates = (
        build_revenue_candidates(
            revenue_queue,
            trend_state,
        )
    )

    seo_candidates = (
        build_seo_candidates(
            seo_plan,
            portfolio,
            trend_state,
        )
    )

    candidates = (
        revenue_candidates
        + seo_candidates
    )

    candidates.sort(
        key=candidate_sort_key,
        reverse=True,
    )

    if candidates:
        selected = dict(
            candidates[0]
        )
    else:
        selected = (
            build_wait_decision(
                trend_state
            )
        )

    auto_candidates = [
        item
        for item in candidates
        if bool(
            item.get(
                "execution_allowed",
                False,
            )
        )
        and str(
            item.get(
                "execution_mode",
                "",
            )
        )
        == "auto_candidate"
    ]

    human_actions = [
        item
        for item in candidates
        if str(
            item.get(
                "execution_mode",
                "",
            )
        )
        == "human_action"
    ]

    if auto_candidates:
        auto_candidate = dict(
            auto_candidates[0]
        )
    else:
        auto_candidate = None

    if human_actions:
        human_action = dict(
            human_actions[0]
        )
    else:
        human_action = None

    selected[
        "trend_state"
    ] = trend_state

    if auto_candidate is not None:
        auto_candidate[
            "trend_state"
        ] = trend_state

    if human_action is not None:
        human_action[
            "trend_state"
        ] = trend_state

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status":
            "ready",
        "trend_status":
            str(
                trend.get(
                    "status",
                    "",
                )
            ),
        "trend_state":
            trend_state,
        "candidate_count":
            len(candidates),
        "auto_candidate_count":
            len(auto_candidates),
        "safe_execution_candidate":
            (
                auto_candidate
                if (
                    isinstance(
                        auto_candidate,
                        dict,
                    )
                    and bool(
                        auto_candidate.get(
                            "execution_allowed",
                            False,
                        )
                    )
                    and str(
                        auto_candidate.get(
                            "execution_mode",
                            "",
                        )
                    )
                    == "auto_candidate"
                )
                else None
            ),
        "human_action_count":
            len(human_actions),
        "selected":
            selected,
        "auto_candidate":
            auto_candidate,
        "human_action":
            human_action,
        "candidates":
            candidates,
    }


def save_optimization_decision(
    decision: dict[str, Any],
) -> Path:
    """Optimization Decisionを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            decision,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_optimization_decision(
    decision: dict[str, Any],
) -> None:
    """Optimization Decisionを表示する。"""

    selected = decision.get(
        "selected",
        {},
    )

    if not isinstance(
        selected,
        dict,
    ):
        selected = {}

    print(
        "\n===== Atlas Optimization Decision =====\n"
    )

    print(
        "Status："
        f"{decision.get('status', '')}"
    )

    print(
        "Trend："
        f"{decision.get('trend_state', '')}"
    )

    print(
        "Candidates："
        f"{decision.get('candidate_count', 0)}"
    )

    print(
        "\nDECISION"
    )

    print(
        "Action："
        f"{selected.get('action', '')}"
    )

    print(
        "Source："
        f"{selected.get('source', '')}"
    )

    print(
        "Target Type："
        f"{selected.get('target_type', '')}"
    )

    print(
        "Target："
        f"{selected.get('target', '')}"
    )

    print(
        "Priority："
        f"{selected.get('priority', 0)}"
    )

    print(
        "Execution Mode："
        f"{selected.get('execution_mode', '')}"
    )

    print(
        "Execution Allowed："
        + (
            "YES"
            if selected.get(
                "execution_allowed"
            )
            else "NO"
        )
    )

    blocked_reason = str(
        selected.get(
            "blocked_reason",
            "",
        )
    ).strip()

    if blocked_reason:
        print(
            "Blocked Reason："
            f"{blocked_reason}"
        )

    print(
        "Reason："
        f"{selected.get('reason', '')}"
    )

    print(
        "Next："
        f"{selected.get('recommended_action', '')}"
    )

    auto_candidate = decision.get(
        "auto_candidate"
    )

    if isinstance(
        auto_candidate,
        dict,
    ):
        print(
            "\nAUTO CANDIDATE"
        )

        print(
            "Action："
            f"{auto_candidate.get('action', '')}"
        )

        print(
            "Target："
            f"{auto_candidate.get('target', '')}"
        )

        print(
            "Priority："
            f"{auto_candidate.get('priority', 0)}"
        )

        print(
            "Execution Mode："
            f"{auto_candidate.get('execution_mode', '')}"
        )

    human_action = decision.get(
        "human_action"
    )

    if isinstance(
        human_action,
        dict,
    ):
        print(
            "\nHUMAN ACTION"
        )

        print(
            "Action："
            f"{human_action.get('action', '')}"
        )

        print(
            "Target："
            f"{human_action.get('target', '')}"
        )

        print(
            "Priority："
            f"{human_action.get('priority', 0)}"
        )

        print(
            "Next："
            f"{human_action.get('recommended_action', '')}"
        )

    print()


def main() -> None:
    """Optimization Decisionを更新する。"""

    seo_plan = load_json(
        SEO_ACTION_PLAN_FILE
    )

    revenue_queue = load_json(
        REVENUE_ACTION_QUEUE_FILE
    )

    portfolio = load_json(
        PORTFOLIO_PLAN_FILE
    )

    trend = load_json(
        PERFORMANCE_TREND_FILE
    )

    decision = (
        build_optimization_decision(
            seo_plan,
            revenue_queue,
            portfolio,
            trend,
        )
    )

    filepath = (
        save_optimization_decision(
            decision
        )
    )

    print_optimization_decision(
        decision
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()