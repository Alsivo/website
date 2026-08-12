import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "performance_history"
    / "history.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "performance_history"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "trend.json"
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


def parse_date(
    value: Any,
) -> date | None:
    """YYYY-MM-DDの日付を安全に変換する。"""

    try:
        return date.fromisoformat(
            str(value)
        )
    except ValueError:
        return None


def numeric_value(
    section: dict[str, Any],
    key: str,
) -> float:
    """数値を安全にfloatへ変換する。"""

    value = section.get(
        key,
        0,
    )

    try:
        return float(
            value or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0


def get_section(
    entry: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """履歴Entryからdict型のSectionを取得する。"""

    section = entry.get(
        section_name,
        {},
    )

    if not isinstance(
        section,
        dict,
    ):
        return {}

    return section


def build_metric_change(
    current_value: float,
    previous_value: float,
) -> dict[str, Any]:
    """2時点の指標差を作る。"""

    change = (
        current_value
        - previous_value
    )

    if previous_value == 0:
        change_rate = None
    else:
        change_rate = (
            change
            / abs(previous_value)
        )

    return {
        "current": current_value,
        "previous": previous_value,
        "change": change,
        "change_rate": change_rate,
    }


def classify_metric(
    metric: dict[str, Any],
    lower_is_better: bool = False,
    absolute_change: bool = False,
) -> str:
    """指標変化をimproving/stable/decliningで判定する。"""

    change = float(
        metric.get(
            "change",
            0,
        )
        or 0
    )

    change_rate = metric.get(
        "change_rate"
    )

    if absolute_change:
        if change > 0:
            return "improving"

        if change < 0:
            return "declining"

        return "stable"

    if lower_is_better:
        if abs(change) < 1.0:
            return "stable"

        if change < 0:
            return "improving"

        return "declining"

    if change_rate is None:
        if change > 0:
            return "improving"

        if change < 0:
            return "declining"

        return "stable"

    change_rate = float(
        change_rate
    )

    if abs(change_rate) < 0.10:
        return "stable"

    if change_rate > 0:
        return "improving"

    return "declining"


def classify_comparison(
    comparison: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """比較結果全体のTrend判定を作る。"""

    if comparison is None:
        return None

    seo = comparison.get(
        "seo",
        {},
    )

    revenue = comparison.get(
        "revenue",
        {},
    )

    metrics = {
        "seo_impressions":
            classify_metric(
                seo.get(
                    "impressions",
                    {},
                )
            ),
        "seo_clicks":
            classify_metric(
                seo.get(
                    "clicks",
                    {},
                )
            ),
        "seo_ctr":
            classify_metric(
                seo.get(
                    "ctr",
                    {},
                )
            ),
        "average_position":
            classify_metric(
                seo.get(
                    "average_position",
                    {},
                ),
                lower_is_better=True,
            ),
        "affiliate_clicks":
            classify_metric(
                revenue.get(
                    "clicks",
                    {},
                )
            ),
        "conversions":
            classify_metric(
                revenue.get(
                    "conversions",
                    {},
                ),
                absolute_change=True,
            ),
        "revenue":
            classify_metric(
                revenue.get(
                    "revenue",
                    {},
                ),
                absolute_change=True,
            ),
        "epc":
            classify_metric(
                revenue.get(
                    "epc",
                    {},
                )
            ),
    }

    improving_count = sum(
        value == "improving"
        for value in metrics.values()
    )

    declining_count = sum(
        value == "declining"
        for value in metrics.values()
    )

    if improving_count > declining_count:
        overall = "improving"

    elif declining_count > improving_count:
        overall = "declining"

    else:
        overall = "stable"

    return {
        "overall": overall,
        "improving_count":
            improving_count,
        "declining_count":
            declining_count,
        "metrics": metrics,
    }


def compare_entries(
    current: dict[str, Any],
    previous: dict[str, Any],
) -> dict[str, Any]:
    """2つのPerformance Historyを比較する。"""

    current_seo = get_section(
        current,
        "seo",
    )

    previous_seo = get_section(
        previous,
        "seo",
    )

    current_revenue = get_section(
        current,
        "revenue",
    )

    previous_revenue = get_section(
        previous,
        "revenue",
    )

    return {
        "from_date": str(
            previous.get(
                "date",
                "",
            )
        ),
        "to_date": str(
            current.get(
                "date",
                "",
            )
        ),
        "seo": {
            "clicks":
                build_metric_change(
                    numeric_value(
                        current_seo,
                        "clicks",
                    ),
                    numeric_value(
                        previous_seo,
                        "clicks",
                    ),
                ),
            "impressions":
                build_metric_change(
                    numeric_value(
                        current_seo,
                        "impressions",
                    ),
                    numeric_value(
                        previous_seo,
                        "impressions",
                    ),
                ),
            "ctr":
                build_metric_change(
                    numeric_value(
                        current_seo,
                        "ctr",
                    ),
                    numeric_value(
                        previous_seo,
                        "ctr",
                    ),
                ),
            "average_position":
                build_metric_change(
                    numeric_value(
                        current_seo,
                        "average_position",
                    ),
                    numeric_value(
                        previous_seo,
                        "average_position",
                    ),
                ),
        },
        "revenue": {
            "clicks":
                build_metric_change(
                    numeric_value(
                        current_revenue,
                        "clicks",
                    ),
                    numeric_value(
                        previous_revenue,
                        "clicks",
                    ),
                ),
            "conversions":
                build_metric_change(
                    numeric_value(
                        current_revenue,
                        "conversions",
                    ),
                    numeric_value(
                        previous_revenue,
                        "conversions",
                    ),
                ),
            "revenue":
                build_metric_change(
                    numeric_value(
                        current_revenue,
                        "revenue",
                    ),
                    numeric_value(
                        previous_revenue,
                        "revenue",
                    ),
                ),
            "epc":
                build_metric_change(
                    numeric_value(
                        current_revenue,
                        "epc",
                    ),
                    numeric_value(
                        previous_revenue,
                        "epc",
                    ),
                ),
        },
    }


def find_previous_entry(
    entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """最新Entryの直前の履歴を取得する。"""

    if len(entries) < 2:
        return None

    return entries[-2]


def find_week_ago_entry(
    entries: list[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any] | None:
    """最新日から7日前のEntryを取得する。"""

    current_date = parse_date(
        current.get(
            "date"
        )
    )

    if current_date is None:
        return None

    for entry in reversed(
        entries[:-1]
    ):
        entry_date = parse_date(
            entry.get(
                "date"
            )
        )

        if entry_date is None:
            continue

        difference = (
            current_date
            - entry_date
        ).days

        if difference == 7:
            return entry

    return None


def build_trend_report(
    history: dict[str, Any],
) -> dict[str, Any]:
    """Performance Trend Reportを生成する。"""

    raw_entries = history.get(
        "entries",
        [],
    )

    if not isinstance(
        raw_entries,
        list,
    ):
        raw_entries = []

    entries = [
        entry
        for entry in raw_entries
        if isinstance(
            entry,
            dict,
        )
        and parse_date(
            entry.get(
                "date"
            )
        )
        is not None
    ]

    entries.sort(
        key=lambda entry: str(
            entry.get(
                "date",
                "",
            )
        )
    )

    if not entries:
        return {
            "generated_at":
                datetime.now().isoformat(),
            "status":
                "insufficient_data",
            "history_entries": 0,
            "current_date": None,
            "previous_comparison": None,
            "previous_trend": None,
            "week_comparison": None,
            "week_trend": None,
        }

    current = entries[-1]

    previous = find_previous_entry(
        entries
    )

    week_ago = find_week_ago_entry(
        entries,
        current,
    )

    previous_comparison = None

    if previous is not None:
        previous_comparison = (
            compare_entries(
                current,
                previous,
            )
        )

    week_comparison = None

    if week_ago is not None:
        week_comparison = (
            compare_entries(
                current,
                week_ago,
            )
        )

    previous_trend = (
        classify_comparison(
            previous_comparison
        )
    )

    week_trend = (
        classify_comparison(
            week_comparison
        )
    )

    if previous is None:
        status = "insufficient_data"
    else:
        status = "ready"

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status": status,
        "history_entries":
            len(entries),
        "current_date": str(
            current.get(
                "date",
                "",
            )
        ),
        "previous_comparison":
            previous_comparison,
        "previous_trend":
            previous_trend,
        "week_comparison":
            week_comparison,
        "week_trend":
            week_trend,
    }


def save_trend_report(
    report: dict[str, Any],
) -> Path:
    """Trend ReportをJSON保存する。"""

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


def print_metric(
    label: str,
    metric: dict[str, Any],
) -> None:
    """比較指標をコンソール表示する。"""

    print(
        f"{label}："
        f"{metric['current']}"
        " / change "
        f"{metric['change']:+.2f}"
    )


def print_comparison(
    title: str,
    comparison: dict[str, Any] | None,
) -> None:
    """比較結果を表示する。"""

    print(
        f"\n{title}"
    )

    if comparison is None:
        print(
            "比較可能な履歴がありません。"
        )
        return

    print(
        "Period："
        f"{comparison['from_date']}"
        " → "
        f"{comparison['to_date']}"
    )

    seo = comparison[
        "seo"
    ]

    revenue = comparison[
        "revenue"
    ]

    print_metric(
        "SEO Impressions",
        seo["impressions"],
    )

    print_metric(
        "SEO Clicks",
        seo["clicks"],
    )

    print_metric(
        "SEO CTR",
        seo["ctr"],
    )

    print_metric(
        "Average Position",
        seo["average_position"],
    )

    print_metric(
        "Affiliate Clicks",
        revenue["clicks"],
    )

    print_metric(
        "Conversions",
        revenue["conversions"],
    )

    print_metric(
        "Revenue",
        revenue["revenue"],
    )


def print_trend_report(
    report: dict[str, Any],
) -> None:
    """Trend Reportを表示する。"""

    print(
        "\n===== Atlas Performance Trend =====\n"
    )

    print(
        "Status："
        f"{report['status']}"
    )

    print(
        "History Entries："
        f"{report['history_entries']}"
    )

    print(
        "Current Date："
        f"{report['current_date']}"
    )

    print_comparison(
        "PREVIOUS COMPARISON",
        report[
            "previous_comparison"
        ],
    )

    print_comparison(
        "7-DAY COMPARISON",
        report[
            "week_comparison"
        ],
    )

    print()


def main() -> None:
    """Performance Trendを更新する。"""

    history = load_json(
        HISTORY_FILE
    )

    report = build_trend_report(
        history
    )

    filepath = save_trend_report(
        report
    )

    print_trend_report(
        report
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()