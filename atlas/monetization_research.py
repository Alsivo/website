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
    / "monetization"
    / "monetization_research_queue.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_research_results.json"
)


def load_queue(
) -> list[dict[str, Any]]:
    """再調査Queueを読み込む。"""

    if not QUEUE_FILE.exists():
        raise FileNotFoundError(
            "monetization_research_queue.jsonが"
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


def research_queue(
    queue: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """再調査Queue内サービスをWeb調査する。"""

    registry = (
        load_affiliate_registry()
    )

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

        source_titles = item.get(
            "source_titles",
            [],
        )

        context = (
            "Alsivo上の関連記事："
            + " / ".join(
                str(title)
                for title in source_titles
            )
        )

        research = (
            research_affiliate_program(
                service=service,
                official_url=official_url,
                context=context,
            )
        )

        research["priority"] = (
            item.get(
                "priority",
                0,
            )
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
    """追加案件調査結果を保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "programs": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_results(
    results: list[dict[str, Any]],
) -> None:
    """追加調査結果を表示する。"""

    print(
        "\n===== Monetization Research Results =====\n"
    )

    if not results:
        print(
            "調査対象はありません。"
        )
        return

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
            "  program_type: "
            f"{item['program_type']}"
        )

        print(
            "  commission: "
            + (
                item["commission"]
                or "不明"
            )
        )

        print(
            "  URL: "
            + (
                item["program_url"]
                or "なし"
            )
        )

        print()


def main() -> None:
    queue = load_queue()

    results = research_queue(
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