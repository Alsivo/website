import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

PROGRAM_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

MONETIZATION_MATCHES_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_matches.json"
)

APPROVAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "human_approval_queue.json"
)

AFFILIATE_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_links.json"
)


ALLOWED_STATUSES = {
    "approved_for_application",
    "applied",
    "approved",
    "rejected",
}


def load_json(
    filepath: Path,
) -> dict[str, Any]:
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
            f"{filepath.name} のJSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{filepath.name} の最上位は"
            "オブジェクトにしてください。"
        )

    return data


def find_program(
    service: str,
    program_data: dict[str, Any],
) -> dict[str, Any] | None:

    programs = program_data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        return None

    for item in programs:
        if not isinstance(
            item,
            dict,
        ):
            continue

        item_service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if (
            item_service.lower()
            == service.lower()
        ):
            return item

    return None


def find_matches(
    service: str,
    monetization_data: dict[str, Any],
) -> list[dict[str, Any]]:

    matches = monetization_data.get(
        "matches",
        [],
    )

    if not isinstance(
        matches,
        list,
    ):
        return []

    result = []

    for item in matches:
        if not isinstance(
            item,
            dict,
        ):
            continue

        item_service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if (
            item_service.lower()
            != service.lower()
        ):
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

        score = int(
            item.get(
                "match_score",
                0,
            )
            or 0
        )

        result.append(
            {
                "slug": slug,
                "title": title,
                "match_score": score,
            }
        )

    result.sort(
        key=lambda item: item[
            "match_score"
        ],
        reverse=True,
    )

    return result


def build_approval_item(
    service: str,
    status: str,
    program: dict[str, Any],
    source_articles: list[dict[str, Any]],
    notes: str,
    affiliate_url: str,
) -> dict[str, Any]:

    priority = 0

    if source_articles:
        priority = max(
            item.get(
                "match_score",
                0,
            )
            for item in source_articles
        )

    item = {
        "service": service,
        "priority": priority,
        "program_name": str(
            program.get(
                "program_name",
                "",
            )
        ),
        "program_type": (
            program.get(
                "program_type"
            )
        ),
        "network": str(
            program.get(
                "network",
                "",
            )
        ),
        "program_url": str(
            program.get(
                "program_url",
                "",
            )
        ),
        "commission": str(
            program.get(
                "commission",
                "",
            )
        ),
        "cookie_duration": str(
            program.get(
                "cookie_duration",
                "",
            )
        ),
        "target_country": str(
            program.get(
                "target_country",
                "",
            )
        ),
        "application_required": (
            program.get(
                "application_required"
            )
        ),
        "verified_at": (
            program.get(
                "verified_at"
            )
            or date.today().isoformat()
        ),
        "source_articles": (
            source_articles
        ),
        "approval_status": status,
        "human_notes": notes,
    }

    if status == "approved":
        item[
            "affiliate_url"
        ] = affiliate_url

    return item


def update_approval_queue(
    service: str,
    item: dict[str, Any],
) -> None:

    data = load_json(
        APPROVAL_QUEUE_FILE
    )

    programs = data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        programs = []

    updated = False

    for index, existing in enumerate(
        programs
    ):
        if not isinstance(
            existing,
            dict,
        ):
            continue

        existing_service = str(
            existing.get(
                "service",
                "",
            )
        ).strip()

        if (
            existing_service.lower()
            == service.lower()
        ):
            programs[index] = item
            updated = True
            break

    if not updated:
        programs.append(
            item
        )

    data[
        "programs"
    ] = programs

    APPROVAL_QUEUE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    APPROVAL_QUEUE_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def update_affiliate_registry(
    service: str,
    status: str,
    program: dict[str, Any],
    affiliate_url: str,
) -> None:

    registry = load_json(
        AFFILIATE_LINKS_FILE
    )

    item = registry.get(
        service,
    )

    if not isinstance(
        item,
        dict,
    ):
        raise ValueError(
            f"{service} が affiliate_links.json "
            "に登録されていません。"
        )

    updated_item = dict(
        item
    )

    network = str(
        program.get(
            "network",
            "",
        )
    ).strip()

    program_name = str(
        program.get(
            "program_name",
            "",
        )
    ).strip()

    if network:
        updated_item[
            "network"
        ] = network

    if program_name:
        updated_item[
            "program_name"
        ] = program_name

    if status == "applied":
        updated_item[
            "affiliate_status"
        ] = "pending"

    elif status == "approved":
        if not affiliate_url:
            raise ValueError(
                "approved を指定する場合は "
                "--affiliate-url が必要です。"
            )

        if not affiliate_url.startswith(
            "http"
        ):
            raise ValueError(
                "affiliate URL が不正です。"
            )

        updated_item[
            "affiliate_status"
        ] = "active"

        updated_item[
            "affiliate_url"
        ] = affiliate_url

    elif status == "rejected":
        updated_item[
            "affiliate_status"
        ] = "rejected"

    elif status == "approved_for_application":
        pass

    registry[
        service
    ] = updated_item

    AFFILIATE_LINKS_FILE.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Affiliate案件の申請状態を"
            "Atlasへ記録します。"
        )
    )

    parser.add_argument(
        "--service",
        required=True,
        help="サービス名",
    )

    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(
            ALLOWED_STATUSES
        ),
        help=(
            "approved_for_application / "
            "applied / approved / rejected"
        ),
    )

    parser.add_argument(
        "--affiliate-url",
        default="",
        help=(
            "approved 時のAffiliate URL"
        ),
    )

    parser.add_argument(
        "--notes",
        default="",
        help="人間によるメモ",
    )

    args = parser.parse_args()

    service = args.service.strip()

    program_data = load_json(
        PROGRAM_RESULTS_FILE
    )

    monetization_data = load_json(
        MONETIZATION_MATCHES_FILE
    )

    program = find_program(
        service,
        program_data,
    )

    if program is None:
        raise ValueError(
            f"{service} の案件調査結果が"
            "見つかりません。"
        )

    source_articles = find_matches(
        service,
        monetization_data,
    )

    approval_item = (
        build_approval_item(
            service=service,
            status=args.status,
            program=program,
            source_articles=source_articles,
            notes=args.notes,
            affiliate_url=args.affiliate_url,
        )
    )

    update_approval_queue(
        service,
        approval_item,
    )

    update_affiliate_registry(
        service=service,
        status=args.status,
        program=program,
        affiliate_url=args.affiliate_url,
    )

    print(
        "\n===== Affiliate Application Manager =====\n"
    )

    print(
        f"service: {service}"
    )

    print(
        f"status: {args.status}"
    )

    print(
        "network: "
        + (
            str(
                program.get(
                    "network",
                    "",
                )
            )
            or "不明"
        )
    )

    print(
        "program: "
        + (
            str(
                program.get(
                    "program_name",
                    "",
                )
            )
            or "不明"
        )
    )

    print(
        f"source_articles: "
        f"{len(source_articles)}"
    )

    if args.status == "applied":
        print(
            "affiliate_status: pending"
        )

    elif args.status == "approved":
        print(
            "affiliate_status: active"
        )

    elif args.status == "rejected":
        print(
            "affiliate_status: rejected"
        )

    else:
        print(
            "affiliate_status: unchanged"
        )

    print(
        "\nAtlasへ申請状態を反映しました。"
    )


if __name__ == "__main__":
    main()