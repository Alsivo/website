import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

MATCH_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_matches.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_research_queue.json"
)

MIN_MATCH_SCORE = 50


def load_monetization_matches(
) -> list[dict[str, Any]]:
    """Monetization Match結果を読み込む。"""

    if not MATCH_FILE.exists():
        raise FileNotFoundError(
            "monetization_matches.jsonが"
            "見つかりません："
            f"{MATCH_FILE}"
        )

    data = json.loads(
        MATCH_FILE.read_text(
            encoding="utf-8",
        )
    )

    matches = data.get(
        "matches",
        [],
    )

    if not isinstance(
        matches,
        list,
    ):
        raise ValueError(
            "matchesは配列にしてください。"
        )

    return matches


def build_research_queue(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """未調査かつ高マッチのサービスを抽出する。"""

    service_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in matches:
        if (
            item.get(
                "monetization_status"
            )
            != "unresearched"
        ):
            continue

        score = int(
            item.get(
                "match_score",
                0,
            )
        )

        if score < MIN_MATCH_SCORE:
            continue

        service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        title = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        if service not in service_map:
            service_map[service] = {
                "service": service,
                "priority": score,
                "source_articles": [],
                "source_titles": [],
                "status": (
                    "pending_research"
                ),
            }

        service_map[
            service
        ]["priority"] = max(
            service_map[
                service
            ]["priority"],
            score,
        )

        if slug:
            service_map[
                service
            ]["source_articles"].append(
                slug
            )

        if title:
            service_map[
                service
            ]["source_titles"].append(
                title
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


def save_research_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """再調査Queueを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "minimum_match_score": (
                    MIN_MATCH_SCORE
                ),
                "programs": queue,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_research_queue(
    queue: list[dict[str, Any]],
) -> None:
    """再調査Queueを表示する。"""

    print(
        "\n===== Monetization Research Queue =====\n"
    )

    if not queue:
        print(
            "追加調査対象はありません。"
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
            "   対象記事："
            + ", ".join(
                item[
                    "source_articles"
                ]
            )
        )

        print()


def main() -> None:
    matches = (
        load_monetization_matches()
    )

    queue = (
        build_research_queue(
            matches
        )
    )

    filepath = (
        save_research_queue(
            queue
        )
    )

    print_research_queue(
        queue
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()