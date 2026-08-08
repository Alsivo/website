import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

MONETIZATION_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_matches.json"
)

PROGRAM_CANDIDATES_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_registration_candidates.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "human_approval_queue.json"
)


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONファイルを読み込む。"""

    if not filepath.exists():
        raise FileNotFoundError(
            f"ファイルが見つかりません：{filepath}"
        )

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{filepath.name}のJSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{filepath.name}の最上位は"
            "オブジェクトにしてください。"
        )

    return data


def build_candidate_map(
    data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """登録候補をサービス名で引ける形にする。"""

    candidates = data.get(
        "registration_candidates",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        raise ValueError(
            "registration_candidatesは"
            "配列にしてください。"
        )

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in candidates:
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


def build_approval_queue(
    monetization_data: dict[str, Any],
    program_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """人間確認が必要な案件候補を作る。"""

    matches = monetization_data.get(
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

    candidate_map = (
        build_candidate_map(
            program_data
        )
    )

    service_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for match in matches:
        if not isinstance(
            match,
            dict,
        ):
            continue

        if (
            match.get(
                "monetization_status"
            )
            != "candidate"
        ):
            continue

        service = str(
            match.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        program = candidate_map.get(
            service
        )

        if program is None:
            continue

        score = int(
            match.get(
                "match_score",
                0,
            )
            or 0
        )

        slug = str(
            match.get(
                "slug",
                "",
            )
        ).strip()

        title = str(
            match.get(
                "title",
                "",
            )
        ).strip()

        if service not in service_map:
            service_map[service] = {
                "service": service,
                "priority": score,
                "program_name": program.get(
                    "program_name",
                    "",
                ),
                "program_type": program.get(
                    "program_type"
                ),
                "network": program.get(
                    "network",
                    "",
                ),
                "program_url": program.get(
                    "program_url",
                    "",
                ),
                "commission": program.get(
                    "commission",
                    "",
                ),
                "cookie_duration": program.get(
                    "cookie_duration",
                    "",
                ),
                "target_country": program.get(
                    "target_country",
                    "",
                ),
                "application_required": (
                    program.get(
                        "application_required"
                    )
                ),
                "verified_at": program.get(
                    "verified_at"
                ),
                "source_articles": [],
                "approval_status": "pending",
                "human_notes": "",
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
                {
                    "slug": slug,
                    "title": title,
                    "match_score": score,
                }
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


def save_approval_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """Human Approval Queueを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "programs": queue,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_approval_queue(
    queue: list[dict[str, Any]],
) -> None:
    """Human Approval Queueを表示する。"""

    print(
        "\n===== Affiliate Human Approval Queue =====\n"
    )

    if not queue:
        print(
            "現在、承認待ち案件はありません。"
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
            "   program: "
            + (
                item["program_name"]
                or "不明"
            )
        )

        print(
            "   network: "
            + (
                item["network"]
                or "不明"
            )
        )

        print(
            "   commission: "
            + (
                item["commission"]
                or "不明"
            )
        )

        print(
            "   URL: "
            + (
                item["program_url"]
                or "なし"
            )
        )

        print(
            "   approval_status: "
            f"{item['approval_status']}"
        )

        print()


def main() -> None:
    monetization_data = (
        load_json(
            MONETIZATION_FILE
        )
    )

    program_data = (
        load_json(
            PROGRAM_CANDIDATES_FILE
        )
    )

    queue = (
        build_approval_queue(
            monetization_data,
            program_data,
        )
    )

    filepath = (
        save_approval_queue(
            queue
        )
    )

    print_approval_queue(
        queue
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()