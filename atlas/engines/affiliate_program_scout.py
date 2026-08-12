import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from agents.affiliate_program_researcher import (
    research_affiliate_program,
)
from engines.affiliate_registry import (
    load_affiliate_registry,
)


BASE_DIR = Path(__file__).resolve().parents[1]

RESULT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

MAX_SERVICES_PER_RUN = 5
RESEARCH_COOLDOWN_DAYS = 30


def load_previous_results() -> dict[str, dict[str, Any]]:
    if not RESULT_FILE.exists():
        return {}

    try:
        data = json.loads(
            RESULT_FILE.read_text(
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

    result: dict[str, dict[str, Any]] = {}

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

        result[service] = item

    return result


def is_recent(
    item: dict[str, Any],
) -> bool:
    verified_at_text = str(
        item.get(
            "verified_at",
            "",
        )
    ).strip()

    if not verified_at_text:
        return False

    try:
        verified_at = datetime.fromisoformat(
            verified_at_text
        ).date()
    except ValueError:
        return False

    elapsed_days = (
        date.today()
        - verified_at
    ).days

    return (
        0
        <= elapsed_days
        < RESEARCH_COOLDOWN_DAYS
    )


def build_scout_queue() -> list[dict[str, Any]]:
    registry = load_affiliate_registry()
    previous_results = load_previous_results()

    queue = []

    for service, item in registry.items():

        affiliate_status = str(
            item.get(
                "affiliate_status",
                "none",
            )
        ).strip()

        if affiliate_status == "active":
            continue

        previous = previous_results.get(
            service
        )

        if (
            previous is not None
            and is_recent(previous)
        ):
            continue

        official_url = str(
            item.get(
                "official_url",
                "",
            )
        ).strip()

        queue.append(
            {
                "service": service,
                "official_url": official_url,
                "affiliate_status": affiliate_status,
            }
        )

    return queue[
        :MAX_SERVICES_PER_RUN
    ]


def research_queue(
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results = []

    for item in queue:
        service = item[
            "service"
        ]

        official_url = item[
            "official_url"
        ]

        context = (
            "Alsivoで紹介候補となっている"
            "AI・SaaSサービス。"
            "日本向け収益化案件を優先して調査。"
        )

        research = (
            research_affiliate_program(
                service=service,
                official_url=official_url,
                context=context,
            )
        )

        research[
            "verified_at"
        ] = date.today().isoformat()

        results.append(
            research
        )

    return results


def merge_results(
    new_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    previous = load_previous_results()

    for item in new_results:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        previous[
            service
        ] = item

    merged = list(
        previous.values()
    )

    merged.sort(
        key=lambda item: str(
            item.get(
                "service",
                "",
            )
        ).lower()
    )

    return merged


def save_results(
    programs: list[dict[str, Any]],
) -> Path:
    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    RESULT_FILE.write_text(
        json.dumps(
            {
                "programs": programs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return RESULT_FILE


def print_summary(
    queue: list[dict[str, Any]],
    new_results: list[dict[str, Any]],
) -> None:
    print(
        "\n===== Affiliate Program Scout =====\n"
    )

    if not queue:
        print(
            "今回の調査対象はありません。"
        )
        return

    print(
        f"調査対象：{len(queue)}件\n"
    )

    for index, item in enumerate(
        new_results,
        start=1,
    ):
        print(
            f"{index}. "
            f"{item.get('service', '')}"
        )

        print(
            "   program_found: "
            f"{item.get('program_found')}"
        )

        print(
            "   type: "
            f"{item.get('program_type')}"
        )

        print(
            "   network: "
            + (
                str(
                    item.get(
                        "network",
                        "",
                    )
                )
                or "不明"
            )
        )

        print(
            "   commission: "
            + (
                str(
                    item.get(
                        "commission",
                        "",
                    )
                )
                or "不明"
            )
        )

        print(
            "   URL: "
            + (
                str(
                    item.get(
                        "program_url",
                        "",
                    )
                )
                or "なし"
            )
        )

        print()


def main() -> None:
    queue = build_scout_queue()

    if not queue:
        print(
            "\n===== Affiliate Program Scout =====\n"
        )
        print(
            "今回の調査対象はありません。"
        )
        return

    print(
        "\n===== Affiliate Scout Queue =====\n"
    )

    for index, item in enumerate(
        queue,
        start=1,
    ):
        print(
            f"{index}. "
            f"{item['service']}"
        )

    new_results = (
        research_queue(
            queue
        )
    )

    merged = (
        merge_results(
            new_results
        )
    )

    filepath = (
        save_results(
            merged
        )
    )

    print_summary(
        queue,
        new_results,
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()