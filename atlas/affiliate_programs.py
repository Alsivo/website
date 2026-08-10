import json
from datetime import date
from pathlib import Path
from typing import Any

from agents.affiliate_program_researcher import (
    research_affiliate_program,
)

from engines.affiliate_registry import (
    load_affiliate_registry,
)

BASE_DIR = Path(__file__).resolve().parent

QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_discovery_queue.json"
)

RESULT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)


def load_discovery_queue(
) -> list[dict[str, Any]]:
    """案件探索Queueを読み込む。"""

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            "program_discovery_queue.jsonが"
            "見つかりません："
            f"{QUEUE_FILE}"
        )

    data = json.loads(
        QUEUE_FILE.read_text(
            encoding="utf-8",
        )
    )

    programs = data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        raise ValueError(
            "programsは配列にしてください。"
        )

    return programs


def research_programs(
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Queue内サービスを順番に調査する。"""

    registry = load_affiliate_registry()

    results: list[
        dict[str, Any]
    ] = []

    for item in queue:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        registry_item = registry.get(
            service,
            {},
        )

        official_url = str(
            registry_item.get(
                "official_url",
                "",
            )
        ).strip()

        source_articles = item.get(
            "source_articles",
            [],
        )

        context = (
            "Alsivo上の記事："
            + ", ".join(
                str(slug)
                for slug in source_articles
            )
        )

        research = (
            research_affiliate_program(
                service=service,
                official_url=official_url,
                context=context,
            )
        )

        research[
            "priority"
        ] = item.get(
            "priority",
            0,
        )

        research[
            "source_articles"
        ] = item.get(
            "source_articles",
            [],
        )

        research[
            "verified_at"
        ] = date.today().isoformat()

        results.append(
            research
        )

    return results


def save_results(
    results: list[dict[str, Any]],
) -> Path:
    """案件調査結果を既存結果へ追加・更新して保存する。"""

    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_programs: list[
        dict[str, Any]
    ] = []

    if RESULT_FILE.exists():
        try:
            existing_data = json.loads(
                RESULT_FILE.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                "program_research_results.jsonの"
                "JSON形式が不正です。"
            ) from error

        programs = existing_data.get(
            "programs",
            [],
        )

        if isinstance(
            programs,
            list,
        ):
            existing_programs = [
                item
                for item in programs
                if isinstance(
                    item,
                    dict,
                )
            ]

    program_map: dict[
        str,
        dict[str, Any],
    ] = {}

    # 既存結果を先に登録
    for item in existing_programs:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        program_map[
            service
        ] = item

    # 今回の調査結果で追加・上書き
    for item in results:
        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        program_map[
            service
        ] = item

    merged_programs = list(
        program_map.values()
    )

    merged_programs.sort(
        key=lambda item: int(
            item.get(
                "priority",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    data = {
        "programs":
            merged_programs,
    }

    RESULT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return RESULT_FILE


def print_results(
    results: list[dict[str, Any]],
) -> None:
    """案件調査結果を表示する。"""

    print(
        "\n===== Affiliate Program Research =====\n"
    )

    for item in results:
        print(
            f"{item['service']} "
            f"({item['priority']}点)"
        )

        print(
            "  program_found: "
            f"{item['program_found']}"
        )

        print(
            "  type: "
            f"{item['program_type']}"
        )

        print(
            "  network: "
            + (
                item["network"]
                if item["network"]
                else "不明"
            )
        )

        print(
            "  commission: "
            + (
                item["commission"]
                if item["commission"]
                else "不明"
            )
        )

        print(
            "  URL: "
            + (
                item["program_url"]
                if item["program_url"]
                else "なし"
            )
        )

        print(
            f"  notes: "
            f"{item['research_notes']}"
        )

        print()


def main() -> None:
    queue = (
        load_discovery_queue()
    )

    results = research_programs(
        queue
    )

    filepath = save_results(
        results
    )

    print_results(
        results
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()