import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

RESEARCH_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_registration_candidates.json"
)


def load_research_results(
) -> list[dict[str, Any]]:
    """Phase 34のWeb調査結果を読み込む。"""

    if not RESEARCH_FILE.exists():
        raise FileNotFoundError(
            "program_research_results.jsonが"
            "見つかりません："
            f"{RESEARCH_FILE}"
        )

    data = json.loads(
        RESEARCH_FILE.read_text(
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


def classify_program(
    program: dict[str, Any],
) -> str:
    """
    調査結果から、
    実際に収益化可能な登録候補かを分類する。
    """

    program_found = program.get(
        "program_found"
    )

    program_type = program.get(
        "program_type"
    )

    program_url = str(
        program.get(
            "program_url",
            "",
        )
    ).strip()

    commission = str(
        program.get(
            "commission",
            "",
        )
    ).strip()

    sources = program.get(
        "sources",
        [],
    )

    # 調査の結果、案件自体が確認できなかった
    if program_found is not True:
        return "not_found"

    # URLがなければ人間による再確認が必要
    if not program_url:
        return "needs_review"

    # 信頼できる根拠があるか
    if not isinstance(
        sources,
        list,
    ):
        return "needs_review"

    trusted_source_found = any(
        isinstance(source, dict)
        and source.get(
            "source_type"
        ) in {
            "official",
            "affiliate_network",
        }
        for source in sources
    )

    if not trusted_source_found:
        return "needs_review"

    # Referralが存在しても、
    # 紹介者への報酬が確認できないなら
    # アフィリエイト登録候補にはしない
    if (
        program_type == "referral"
        and not commission
    ):
        return "needs_review"

    # 報酬条件が確認できない案件も
    # 自動的に登録候補にはしない
    if not commission:
        return "needs_review"

    return "registration_candidates"


def build_registration_candidates(
    programs: list[dict[str, Any]],
) -> dict[str, Any]:
    """案件を登録候補・要確認・未発見へ分類する。"""

    result = {
        "registration_candidates": [],
        "needs_review": [],
        "not_found": [],
    }

    for program in programs:
        classification = (
            classify_program(
                program
            )
        )

        item = {
            "service": program.get(
                "service",
                "",
            ),
            "priority": program.get(
                "priority",
                0,
            ),
            "program_type": program.get(
                "program_type"
            ),
            "program_name": program.get(
                "program_name",
                "",
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
            "research_notes": program.get(
                "research_notes",
                "",
            ),
            "verified_at": program.get(
                "verified_at"
            ),
            "source_articles": program.get(
                "source_articles",
                [],
            ),
            "sources": program.get(
                "sources",
                [],
            ),
        }

        result[
            classification
        ].append(
            item
        )

    for key in result:
        result[key].sort(
            key=lambda item: item.get(
                "priority",
                0,
            ),
            reverse=True,
        )

    return result


def save_registration_candidates(
    data: dict[str, Any],
) -> Path:
    """登録候補一覧をJSON保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_registration_candidates(
    data: dict[str, Any],
) -> None:
    """候補を見やすく表示する。"""

    print(
        "\n===== Affiliate Program Candidates =====\n"
    )

    sections = [
        (
            "registration_candidates",
            "登録候補",
        ),
        (
            "needs_review",
            "要確認",
        ),
        (
            "not_found",
            "未発見",
        ),
    ]

    for key, label in sections:
        items = data.get(
            key,
            [],
        )

        print(
            f"--- {label} ({len(items)}件) ---"
        )

        if not items:
            print("なし\n")
            continue

        for item in items:
            print(
                f"[{item['priority']}点] "
                f"{item['service']}"
            )

            print(
                "  program: "
                + (
                    item["program_name"]
                    or "不明"
                )
            )

            print(
                "  network: "
                + (
                    item["network"]
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

            print(
                "  commission: "
                + (
                    item["commission"]
                    or "不明"
                )
            )

            print()


def main() -> None:
    programs = (
        load_research_results()
    )

    data = (
        build_registration_candidates(
            programs
        )
    )

    filepath = (
        save_registration_candidates(
            data
        )
    )

    print_registration_candidates(
        data
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()