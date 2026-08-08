import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

BASE_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

MONETIZATION_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "monetization"
    / "monetization_research_results.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)


def load_programs(
    filepath: Path,
) -> list[dict[str, Any]]:
    """案件調査結果JSONを読み込む。"""

    if not filepath.exists():
        return []

    data = json.loads(
        filepath.read_text(
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
            f"{filepath.name}のprogramsは"
            "配列にしてください。"
        )

    return [
        item
        for item in programs
        if isinstance(item, dict)
    ]


def normalize_service_name(
    service: str,
) -> str:
    """サービス名の表記揺れをRegistry名へ寄せる。"""

    service = service.strip()

    if service.startswith(
        "Gemini"
    ):
        return "Gemini"

    return service


def merge_program_results(
    base_programs: list[dict[str, Any]],
    additional_programs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """新しい調査結果を既存結果へマージする。"""

    program_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in base_programs:
        service = normalize_service_name(
            str(
                item.get(
                    "service",
                    "",
                )
            )
        )

        if not service:
            continue

        copied_item = dict(item)
        copied_item["service"] = service

        program_map[service] = (
            copied_item
        )

    # 追加調査結果を優先して上書き
    for item in additional_programs:
        service = normalize_service_name(
            str(
                item.get(
                    "service",
                    "",
                )
            )
        )

        if not service:
            continue

        copied_item = dict(item)
        copied_item["service"] = service

        program_map[service] = (
            copied_item
        )

    result = list(
        program_map.values()
    )

    result.sort(
        key=lambda item: int(
            item.get(
                "priority",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    return result


def save_program_results(
    programs: list[dict[str, Any]],
) -> Path:
    """マージ済み案件情報を保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "programs": programs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def main() -> None:
    base_programs = load_programs(
        BASE_RESULTS_FILE
    )

    additional_programs = load_programs(
        MONETIZATION_RESULTS_FILE
    )

    merged = merge_program_results(
        base_programs,
        additional_programs,
    )

    filepath = save_program_results(
        merged
    )

    print(
        "\n===== Affiliate Program Merge =====\n"
    )

    for item in merged:
        print(
            f"- {item.get('service', '')}: "
            f"program_found="
            f"{item.get('program_found')}"
        )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()