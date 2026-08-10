import json
from pathlib import Path
from typing import Any
from datetime import date, datetime


BASE_DIR = Path(__file__).resolve().parents[1]

PROGRAM_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

PROGRAM_RESEARCH_COOLDOWN_DAYS = 30

DECISIONS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_opportunities"
    / "affiliate_opportunity_decisions.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "program_discovery_queue.json"
)


def load_opportunity_decisions() -> list[dict[str, Any]]:
    """Phase 33のAI判断結果を読み込む。"""

    if not DECISIONS_FILE.exists():
        raise FileNotFoundError(
            "affiliate_opportunity_decisions.jsonが"
            "見つかりません："
            f"{DECISIONS_FILE}"
        )

    try:
        data = json.loads(
            DECISIONS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "affiliate_opportunity_decisions.jsonの"
            "JSON形式が不正です。"
        ) from error

    decisions = data.get(
        "decisions",
        [],
    )

    if not isinstance(
        decisions,
        list,
    ):
        raise ValueError(
            "decisionsは配列にしてください。"
        )

    return decisions

def load_recent_program_research(
) -> dict[str, dict[str, Any]]:
    """過去のAffiliate Program調査結果をサービス別に読む。"""

    if not PROGRAM_RESULTS_FILE.exists():
        return {}

    try:
        data = json.loads(
            PROGRAM_RESULTS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return {}

    programs = data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        return {}

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in programs:
        if not isinstance(
            item,
            dict,
        ):
            continue

        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        result[
            service
        ] = item

    return result

def program_research_is_recent(
    item: dict[str, Any],
) -> bool:
    """Affiliate Program調査がクールダウン期間内か判定する。"""

    verified_at_text = str(
        item.get(
            "verified_at",
            "",
        )
    ).strip()

    if not verified_at_text:
        return False

    try:
        verified_at = (
            datetime.fromisoformat(
                verified_at_text
            ).date()
        )
    except ValueError:
        return False

    elapsed_days = (
        date.today()
        - verified_at
    ).days

    return (
        0
        <= elapsed_days
        < PROGRAM_RESEARCH_COOLDOWN_DAYS
    )

def build_program_discovery_queue(
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """案件探索対象サービスを作成する。"""

    researched_programs = (
        load_recent_program_research()
    )

    service_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for decision in decisions:
        if (
            decision.get("action")
            != "find_program"
        ):
            continue

        service = decision.get(
            "service"
        )

        if (
            not isinstance(
                service,
                str,
            )
            or not service.strip()
        ):
            continue

        service = service.strip()

        previous_research = (
            researched_programs.get(
                service
            )
        )

        if (
            previous_research
            is not None
            and program_research_is_recent(
                previous_research
            )
        ):
            continue

        priority = int(
            decision.get(
                "priority",
                0,
            )
        )

        slug = str(
            decision.get(
                "slug",
                "",
            )
        ).strip()

        if service not in service_map:
            service_map[service] = {
                "service": service,
                "priority": priority,
                "source_articles": [],
                "status": "pending_research",
            }

        service_map[service][
            "priority"
        ] = max(
            service_map[service][
                "priority"
            ],
            priority,
        )

        if slug:
            service_map[service][
                "source_articles"
            ].append(
                slug
            )

    queue = list(
        service_map.values()
    )

    queue.sort(
        key=lambda item: item[
            "priority"
        ],
        reverse=True,
    )

    return queue

def enrich_discovery_queue(
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """案件調査で確認するフィールドを追加する。"""

    result = []

    for item in queue:
        result.append(
            {
                **item,
                "program_found": None,
                "program_type": None,
                "program_name": "",
                "network": "",
                "program_url": "",
                "commission": "",
                "cookie_duration": "",
                "target_country": "",
                "application_required": None,
                "research_notes": "",
                "verified_at": None,
            }
        )

    return result

def save_discovery_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """案件探索Queueを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "programs": queue,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE

def print_discovery_queue(
    queue: list[dict[str, Any]],
) -> None:
    """案件探索対象を表示する。"""

    print(
        "\n===== Affiliate Program Discovery =====\n"
    )

    if not queue:
        print(
            "現在、案件探索対象はありません。"
        )
        return

    for index, item in enumerate(
        queue,
        start=1,
    ):
        print(
            f"{index}. "
            f"{item['service']} "
            f"({item['priority']}点)"
        )

        print(
            "   status: "
            f"{item['status']}"
        )

        print(
            "   対象記事: "
            + ", ".join(
                item[
                    "source_articles"
                ]
            )
        )

        print()

def main() -> None:
    decisions = (
        load_opportunity_decisions()
    )

    queue = (
        build_program_discovery_queue(
            decisions
        )
    )

    queue = (
        enrich_discovery_queue(
            queue
        )
    )

    filepath = (
        save_discovery_queue(
            queue
        )
    )

    print_discovery_queue(
        queue
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()