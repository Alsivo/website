import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "asp_candidates.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "asp_candidate_ranking.json"
)


def parse_float(
    value: str,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(
    value: str,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def freshness_score(
    value: str,
) -> float:
    try:
        verified = datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        return 0.0

    days = (
        date.today()
        - verified
    ).days

    if days <= 30:
        return 100.0

    if days <= 90:
        return 70.0

    if days <= 180:
        return 40.0

    return 10.0


def load_candidates() -> list[dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"asp_candidates.csvが見つかりません：{INPUT_FILE}"
        )

    result = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            service = str(
                row.get(
                    "service",
                    "",
                )
            ).strip()

            if not service:
                continue

            result.append(
                {
                    "service": service,
                    "network": str(
                        row.get(
                            "network",
                            "",
                        )
                    ).strip(),
                    "program_name": str(
                        row.get(
                            "program_name",
                            "",
                        )
                    ).strip(),
                    "program_url": str(
                        row.get(
                            "program_url",
                            "",
                        )
                    ).strip(),
                    "reward_type": str(
                        row.get(
                            "reward_type",
                            "",
                        )
                    ).strip(),
                    "reward_value": parse_float(
                        row.get(
                            "reward_value",
                            "",
                        )
                    ),
                    "currency": str(
                        row.get(
                            "currency",
                            "",
                        )
                    ).strip(),
                    "conversion_action": str(
                        row.get(
                            "conversion_action",
                            "",
                        )
                    ).strip(),
                    "cookie_days": parse_int(
                        row.get(
                            "cookie_days",
                            "",
                        )
                    ),
                    "approval_score": parse_float(
                        row.get(
                            "approval_score",
                            "",
                        )
                    ),
                    "article_match_score": parse_float(
                        row.get(
                            "article_match_score",
                            "",
                        )
                    ),
                    "status": str(
                        row.get(
                            "status",
                            "",
                        )
                    ).strip(),
                    "last_verified": str(
                        row.get(
                            "last_verified",
                            "",
                        )
                    ).strip(),
                    "notes": str(
                        row.get(
                            "notes",
                            "",
                        )
                    ).strip(),
                }
            )

    return result


def reward_score(
    candidate: dict[str, Any],
) -> float:

    reward_type = candidate[
        "reward_type"
    ]

    reward_value = float(
        candidate[
            "reward_value"
        ]
    )

    if reward_type == "fixed":
        return min(
            100.0,
            reward_value / 20.0,
        )

    if reward_type == "percent":
        return min(
            100.0,
            reward_value * 4.0,
        )

    return 0.0


def calculate_score(
    candidate: dict[str, Any],
) -> float:

    reward = reward_score(
        candidate
    )

    approval = min(
        100.0,
        max(
            0.0,
            candidate[
                "approval_score"
            ],
        ),
    )

    article_match = min(
        100.0,
        max(
            0.0,
            candidate[
                "article_match_score"
            ],
        ),
    )

    cookie = min(
        100.0,
        candidate[
            "cookie_days"
        ] * 3.0,
    )

    freshness = freshness_score(
        candidate[
            "last_verified"
        ]
    )

    total = (
        reward * 0.30
        + approval * 0.25
        + article_match * 0.30
        + cookie * 0.05
        + freshness * 0.10
    )

    return round(
        total,
        2,
    )


def decide_action(
    score: float,
    status: str,
) -> str:

    if status in {
        "rejected",
        "closed",
        "unavailable",
    }:
        return "WAIT"

    if score >= 75:
        return "APPLY"

    if score >= 55:
        return "REVIEW"

    return "WAIT"


def build_ranking(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    ranking = []

    for candidate in candidates:

        score = calculate_score(
            candidate
        )

        ranking.append(
            {
                **candidate,
                "score": score,
                "action": decide_action(
                    score,
                    candidate[
                        "status"
                    ],
                ),
            }
        )

    ranking.sort(
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    return ranking


def save_ranking(
    ranking: list[dict[str, Any]],
) -> Path:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "candidates": ranking,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_ranking(
    ranking: list[dict[str, Any]],
) -> None:

    print(
        "\n===== ASP Opportunity Ranking =====\n"
    )

    if not ranking:
        print(
            "現在、ASP候補案件はありません。"
        )
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):
        print(
            f"{index}. "
            f"{item['service']} "
            f"[{item['score']}点]"
        )

        print(
            "   ASP: "
            + (
                item["network"]
                or "不明"
            )
        )

        print(
            "   program: "
            + (
                item["program_name"]
                or "不明"
            )
        )

        print(
            "   reward: "
            f"{item['reward_value']} "
            f"{item['currency']} "
            f"({item['reward_type']})"
        )

        print(
            "   approval: "
            f"{item['approval_score']}"
        )

        print(
            "   article match: "
            f"{item['article_match_score']}"
        )

        print(
            "   action: "
            f"{item['action']}"
        )

        print()


def main() -> None:

    candidates = load_candidates()

    ranking = build_ranking(
        candidates
    )

    filepath = save_ranking(
        ranking
    )

    print_ranking(
        ranking
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()