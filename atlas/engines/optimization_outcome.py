import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

OPTIMIZATION_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "optimization_history"
    / "history.json"
)

PERFORMANCE_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "performance_history"
    / "history.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "optimization_outcome"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "optimization_outcomes.json"
)


TRACKABLE_ACTIONS = {
    "TITLE_ONLY",
    "STRENGTHEN",
    "REWRITE",
}


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
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def parse_date(
    value: str,
) -> datetime | None:
    """ISO形式文字列をdatetimeへ変換する。"""

    value = value.strip()

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value
        )
    except ValueError:
        return None


def load_executed_optimizations(
) -> list[dict[str, Any]]:
    """実際に実行された記事最適化だけを取得する。"""

    data = load_json(
        OPTIMIZATION_HISTORY_FILE
    )

    history = data.get(
        "history",
        [],
    )

    if not isinstance(
        history,
        list,
    ):
        return []

    result: list[
        dict[str, Any]
    ] = []

    for item in history:

        if not isinstance(
            item,
            dict,
        ):
            continue

        action = str(
            item.get(
                "execution_result_action",
                "",
            )
        ).strip()

        target = str(
            item.get(
                "execution_result_target",
                "",
            )
        ).strip()

        actually_executed = bool(
            item.get(
                "actually_executed",
                False,
            )
        )

        dry_run = bool(
            item.get(
                "execution_dry_run",
                True,
            )
        )

        if action not in TRACKABLE_ACTIONS:
            continue

        if not actually_executed:
            continue

        if dry_run:
            continue

        if not target:
            continue

        result.append(
            item
        )

    return result


def load_performance_entries(
) -> list[dict[str, Any]]:
    """Performance Historyを日付順で取得する。"""

    data = load_json(
        PERFORMANCE_HISTORY_FILE
    )

    entries = data.get(
        "entries",
        [],
    )

    if not isinstance(
        entries,
        list,
    ):
        return []

    valid_entries = [
        item
        for item in entries
        if isinstance(
            item,
            dict,
        )
    ]

    valid_entries.sort(
        key=lambda item: str(
            item.get(
                "date",
                "",
            )
        )
    )

    return valid_entries


def get_article_metrics(
    entry: dict[str, Any],
    slug: str,
) -> dict[str, float] | None:
    """Performance Historyから記事別SEO指標を取得する。"""

    article_seo = entry.get(
        "article_seo",
        {},
    )

    if not isinstance(
        article_seo,
        dict,
    ):
        return None

    metrics = article_seo.get(
        slug
    )

    if not isinstance(
        metrics,
        dict,
    ):
        return None

    try:
        return {
            "clicks":
                float(
                    metrics.get(
                        "clicks",
                        0,
                    )
                    or 0
                ),
            "impressions":
                float(
                    metrics.get(
                        "impressions",
                        0,
                    )
                    or 0
                ),
            "ctr":
                float(
                    metrics.get(
                        "ctr",
                        0,
                    )
                    or 0
                ),
            "average_position":
                float(
                    metrics.get(
                        "average_position",
                        0,
                    )
                    or 0
                ),
        }
    except (
        TypeError,
        ValueError,
    ):
        return None


def find_before_entry(
    entries: list[dict[str, Any]],
    executed_at: datetime,
    slug: str,
) -> tuple[dict[str, Any], dict[str, float]] | None:
    """実行日前または実行日以前の最新記事データを探す。"""

    candidates: list[
        tuple[
            datetime,
            dict[str, Any],
            dict[str, float],
        ]
    ] = []

    for entry in entries:

        date_text = str(
            entry.get(
                "date",
                "",
            )
        ).strip()

        try:
            entry_date = datetime.fromisoformat(
                date_text
            )
        except ValueError:
            continue

        if entry_date.date() > executed_at.date():
            continue

        metrics = get_article_metrics(
            entry,
            slug,
        )

        if metrics is None:
            continue

        candidates.append(
            (
                entry_date,
                entry,
                metrics,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0]
    )

    _, entry, metrics = (
        candidates[-1]
    )

    return (
        entry,
        metrics,
    )


def find_after_entry(
    entries: list[dict[str, Any]],
    executed_at: datetime,
    slug: str,
    minimum_days: int = 7,
) -> tuple[dict[str, Any], dict[str, float]] | None:
    """実行後一定日数を経過した記事データを探す。"""

    candidates: list[
        tuple[
            datetime,
            dict[str, Any],
            dict[str, float],
        ]
    ] = []

    for entry in entries:

        date_text = str(
            entry.get(
                "date",
                "",
            )
        ).strip()

        try:
            entry_date = datetime.fromisoformat(
                date_text
            )
        except ValueError:
            continue

        elapsed_days = (
            entry_date.date()
            - executed_at.date()
        ).days

        if elapsed_days < minimum_days:
            continue

        metrics = get_article_metrics(
            entry,
            slug,
        )

        if metrics is None:
            continue

        candidates.append(
            (
                entry_date,
                entry,
                metrics,
            )
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0]
    )

    _, entry, metrics = (
        candidates[0]
    )

    return (
        entry,
        metrics,
    )


def calculate_delta(
    before: float,
    after: float,
) -> float:
    """単純差分を計算する。"""

    return (
        after
        - before
    )


def calculate_rate(
    before: float,
    after: float,
) -> float | None:
    """前後の増減率を計算する。"""

    if before == 0:
        return None

    return (
        (
            after
            - before
        )
        / abs(
            before
        )
    )


def classify_outcome(
    before: dict[str, float],
    after: dict[str, float],
) -> tuple[str, str]:
    """SEO指標の変化からOutcomeを判定する。"""

    click_delta = (
        after["clicks"]
        - before["clicks"]
    )

    impression_delta = (
        after["impressions"]
        - before["impressions"]
    )

    ctr_delta = (
        after["ctr"]
        - before["ctr"]
    )

    position_improvement = (
        before["average_position"]
        - after["average_position"]
    )

    positive_score = 0
    negative_score = 0

    if click_delta > 0:
        positive_score += 2
    elif click_delta < 0:
        negative_score += 2

    if impression_delta > 0:
        positive_score += 1
    elif impression_delta < 0:
        negative_score += 1

    if ctr_delta > 0:
        positive_score += 2
    elif ctr_delta < 0:
        negative_score += 2

    if position_improvement > 0:
        positive_score += 2
    elif position_improvement < 0:
        negative_score += 2

    if (
        positive_score >= 3
        and positive_score
        > negative_score
    ):
        return (
            "improved",
            (
                "実行後にSEO指標の"
                "総合的な改善が確認されました。"
            ),
        )

    if (
        negative_score >= 3
        and negative_score
        > positive_score
    ):
        return (
            "declined",
            (
                "実行後にSEO指標の"
                "総合的な悪化が確認されました。"
            ),
        )

    return (
        "neutral",
        (
            "実行前後で明確な改善または"
            "悪化は確認できませんでした。"
        ),
    )


def build_outcome(
    optimization: dict[str, Any],
    performance_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """1施策分のOutcomeを作る。"""

    action = str(
        optimization.get(
            "execution_result_action",
            "",
        )
    ).strip()

    target = str(
        optimization.get(
            "execution_result_target",
            "",
        )
    ).strip()

    recorded_at = str(
        optimization.get(
            "recorded_at",
            "",
        )
    ).strip()

    executed_at = parse_date(
        recorded_at
    )

    base = {
        "optimization_recorded_at":
            recorded_at,
        "action":
            action,
        "target":
            target,
        "priority":
            int(
                optimization.get(
                    "priority",
                    0,
                )
                or 0
            ),
        "source":
            str(
                optimization.get(
                    "source",
                    "",
                )
            ),
    }

    if executed_at is None:
        return {
            **base,
            "status":
                "invalid_date",
            "outcome":
                "unknown",
            "reason":
                "実行日時を解析できません。",
        }

    before_result = (
        find_before_entry(
            performance_entries,
            executed_at,
            target,
        )
    )

    if before_result is None:
        return {
            **base,
            "status":
                "insufficient_data",
            "outcome":
                "unknown",
            "reason":
                (
                    "施策実行前の記事別SEOデータが"
                    "ありません。"
                ),
        }

    before_entry, before_metrics = (
        before_result
    )

    after_result = (
        find_after_entry(
            performance_entries,
            executed_at,
            target,
            minimum_days=7,
        )
    )

    if after_result is None:
        return {
            **base,
            "status":
                "waiting",
            "outcome":
                "pending",
            "reason":
                (
                    "施策実行後7日以上経過した"
                    "記事別SEOデータがまだありません。"
                ),
            "before": {
                "date":
                    str(
                        before_entry.get(
                            "date",
                            "",
                        )
                    ),
                **before_metrics,
            },
        }

    after_entry, after_metrics = (
        after_result
    )

    outcome, reason = (
        classify_outcome(
            before_metrics,
            after_metrics,
        )
    )

    return {
        **base,
        "status":
            "evaluated",
        "outcome":
            outcome,
        "reason":
            reason,
        "before": {
            "date":
                str(
                    before_entry.get(
                        "date",
                        "",
                    )
                ),
            **before_metrics,
        },
        "after": {
            "date":
                str(
                    after_entry.get(
                        "date",
                        "",
                    )
                ),
            **after_metrics,
        },
        "delta": {
            "clicks":
                calculate_delta(
                    before_metrics["clicks"],
                    after_metrics["clicks"],
                ),
            "impressions":
                calculate_delta(
                    before_metrics["impressions"],
                    after_metrics["impressions"],
                ),
            "ctr":
                calculate_delta(
                    before_metrics["ctr"],
                    after_metrics["ctr"],
                ),
            "average_position":
                calculate_delta(
                    before_metrics[
                        "average_position"
                    ],
                    after_metrics[
                        "average_position"
                    ],
                ),
        },
        "rate": {
            "clicks":
                calculate_rate(
                    before_metrics["clicks"],
                    after_metrics["clicks"],
                ),
            "impressions":
                calculate_rate(
                    before_metrics["impressions"],
                    after_metrics["impressions"],
                ),
            "ctr":
                calculate_rate(
                    before_metrics["ctr"],
                    after_metrics["ctr"],
                ),
        },
    }


def build_output(
) -> dict[str, Any]:
    """Optimization Outcome全体を作る。"""

    optimizations = (
        load_executed_optimizations()
    )

    performance_entries = (
        load_performance_entries()
    )

    outcomes = [
        build_outcome(
            optimization,
            performance_entries,
        )
        for optimization
        in optimizations
    ]

    counts = {
        "evaluated": 0,
        "waiting": 0,
        "insufficient_data": 0,
        "improved": 0,
        "neutral": 0,
        "declined": 0,
    }

    for item in outcomes:

        status = str(
            item.get(
                "status",
                "",
            )
        )

        outcome = str(
            item.get(
                "outcome",
                "",
            )
        )

        if status in counts:
            counts[
                status
            ] += 1

        if outcome in counts:
            counts[
                outcome
            ] += 1

    return {
        "generated_at":
            datetime.now().isoformat(),
        "executed_optimizations":
            len(
                optimizations
            ),
        "performance_entries":
            len(
                performance_entries
            ),
        "counts":
            counts,
        "outcomes":
            outcomes,
    }


def save_output(
    output: dict[str, Any],
) -> Path:
    """Outcome結果を保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_summary(
    output: dict[str, Any],
) -> None:
    """Outcome結果をコンソールへ表示する。"""

    print(
        "\n===== Atlas Optimization Outcome =====\n"
    )

    print(
        "Executed Optimizations："
        f"{output.get('executed_optimizations', 0)}"
    )

    print(
        "Performance Entries："
        f"{output.get('performance_entries', 0)}"
    )

    counts = output.get(
        "counts",
        {},
    )

    if not isinstance(
        counts,
        dict,
    ):
        counts = {}

    print(
        "Evaluated："
        f"{counts.get('evaluated', 0)}"
    )

    print(
        "Waiting："
        f"{counts.get('waiting', 0)}"
    )

    print(
        "Improved："
        f"{counts.get('improved', 0)}"
    )

    print(
        "Neutral："
        f"{counts.get('neutral', 0)}"
    )

    print(
        "Declined："
        f"{counts.get('declined', 0)}"
    )

    print()


def main() -> None:
    """Optimization Outcomeを更新する。"""

    output = build_output()

    filepath = save_output(
        output
    )

    print_summary(
        output
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()