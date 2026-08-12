import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

RELATED_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "related_affiliate_opportunities.json"
)

PROGRAM_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

AFFILIATE_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_links.json"
)


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


def find_related_opportunity(
    program_name: str,
) -> dict[str, Any] | None:

    data = load_json(
        RELATED_FILE
    )

    opportunities = data.get(
        "opportunities",
        [],
    )

    if not isinstance(
        opportunities,
        list,
    ):
        return None

    for item in opportunities:

        if not isinstance(
            item,
            dict,
        ):
            continue

        name = str(
            item.get(
                "program_name",
                "",
            )
        ).strip()

        if (
            name.lower()
            == program_name.lower()
        ):
            return item

    return None


def promote_program_result(
    opportunity: dict[str, Any],
) -> dict[str, Any]:

    service = str(
        opportunity.get(
            "program_name",
            "",
        )
    ).strip()

    network = str(
        opportunity.get(
            "network",
            "",
        )
    ).strip()

    reward_value = float(
        opportunity.get(
            "reward_value",
            0,
        )
        or 0
    )

    currency = str(
        opportunity.get(
            "currency",
            "JPY",
        )
    ).strip()

    conversion_action = str(
        opportunity.get(
            "conversion_action",
            "",
        )
    ).strip()

    program_url = str(
        opportunity.get(
            "program_url",
            "",
        )
    ).strip()

    notes = str(
        opportunity.get(
            "notes",
            "",
        )
    ).strip()

    commission = ""

    if reward_value > 0:
        commission = (
            f"{conversion_action}: "
            f"{reward_value:g} {currency}"
        )

    return {
        "service": service,
        "program_found": True,
        "program_type": "affiliate",
        "program_name": service,
        "network": network,
        "program_url": program_url,
        "commission": commission,
        "cookie_duration": "",
        "target_country": "Japan",
        "application_required": True,
        "research_notes": (
            "国内ASP管理画面で人間が案件を確認。"
            + (
                f" {notes}"
                if notes
                else ""
            )
        ),
        "sources": [],
        "verified_at": date.today().isoformat(),
    }


def update_program_results(
    promoted: dict[str, Any],
) -> None:

    data = load_json(
        PROGRAM_RESULTS_FILE
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

    service = str(
        promoted.get(
            "service",
            "",
        )
    ).strip()

    updated = False

    for index, item in enumerate(
        programs
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        existing_service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        if (
            existing_service.lower()
            == service.lower()
        ):
            programs[index] = promoted
            updated = True
            break

    if not updated:
        programs.append(
            promoted
        )

    programs.sort(
        key=lambda item: str(
            item.get(
                "service",
                "",
            )
        ).lower()
    )

    data[
        "programs"
    ] = programs

    PROGRAM_RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROGRAM_RESULTS_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def update_affiliate_links(
    promoted: dict[str, Any],
    opportunity: dict[str, Any],
) -> None:

    registry = load_json(
        AFFILIATE_LINKS_FILE
    )

    service = str(
        promoted.get(
            "service",
            "",
        )
    ).strip()

    network = str(
        promoted.get(
            "network",
            "",
        )
    ).strip()

    program_name = str(
        promoted.get(
            "program_name",
            "",
        )
    ).strip()

    reward_value = float(
        opportunity.get(
            "reward_value",
            0,
        )
        or 0
    )

    currency = str(
        opportunity.get(
            "currency",
            "JPY",
        )
    ).strip()

    conversion_action = str(
        opportunity.get(
            "conversion_action",
            "",
        )
    ).strip()

    existing = registry.get(
        service,
        {},
    )

    if not isinstance(
        existing,
        dict,
    ):
        existing = {}

    official_url = str(
        existing.get(
            "official_url",
            "",
        )
    ).strip()

    registry[
        service
    ] = {
        "official_url": official_url,
        "affiliate_url": str(
            existing.get(
                "affiliate_url",
                "",
            )
        ),
        "cta_label": (
            str(
                existing.get(
                    "cta_label",
                    "",
                )
            )
            or f"{service}を確認する"
        ),
        "aliases": (
            existing.get(
                "aliases"
            )
            if isinstance(
                existing.get(
                    "aliases"
                ),
                list,
            )
            else [service]
        ),
        "affiliate_status": str(
            existing.get(
                "affiliate_status",
                "none",
            )
        ),
        "network": network,
        "program_name": program_name,
        "reward_type": "fixed",
        "reward_value": reward_value,
        "currency": currency,
        "conversion_action": conversion_action,
        "cookie_days": int(
            existing.get(
                "cookie_days",
                0,
            )
            or 0
        ),
        "program_score": float(
            existing.get(
                "program_score",
                0,
            )
            or 0
        ),
        "last_verified": date.today().isoformat(),
    }

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
            "関連Affiliate案件を正式案件として"
            "Atlas Registryへ昇格します。"
        )
    )

    parser.add_argument(
        "--program-name",
        required=True,
        help="昇格する案件名",
    )

    args = parser.parse_args()

    program_name = (
        args.program_name.strip()
    )

    opportunity = (
        find_related_opportunity(
            program_name
        )
    )

    if opportunity is None:
        raise ValueError(
            f"{program_name} が "
            "related_affiliate_opportunities.json "
            "に見つかりません。"
        )

    promoted = (
        promote_program_result(
            opportunity
        )
    )

    update_program_results(
        promoted
    )

    update_affiliate_links(
        promoted,
        opportunity,
    )

    print(
        "\n===== Affiliate Program Promoter =====\n"
    )

    print(
        f"service: "
        f"{promoted['service']}"
    )

    print(
        f"network: "
        f"{promoted['network']}"
    )

    print(
        f"program: "
        f"{promoted['program_name']}"
    )

    print(
        f"commission: "
        f"{promoted['commission']}"
    )

    print(
        "affiliate_status: none"
    )

    print(
        "\n正式案件としてAtlasへ登録しました。"
    )


if __name__ == "__main__":
    main()