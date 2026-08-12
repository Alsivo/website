import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

ACTION_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_action_queue.json"
)

PROGRAM_RESULTS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "program_research_results.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "domestic_asp_candidate_queue.json"
)

REVENUE_ACTION_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_action_queue.json"
)

MAX_CANDIDATES = 5

DOMESTIC_ASPS = [
    "A8.net",
    "もしもアフィリエイト",
    "バリューコマース",
    "afb",
    "アクセストレード",
]

VERIFICATION_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "asp_verification_history.json"
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


def build_revenue_action_map(
    data: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Revenue Action Queueをサービス別Mapへ変換する。"""

    actions = data.get(
        "actions",
        [],
    )

    if not isinstance(
        actions,
        list,
    ):
        return {}

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for item in actions:
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
            service.lower()
        ] = item

    return result


def build_verification_map(
    data: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:

    verifications = data.get(
        "verifications",
        [],
    )

    if not isinstance(
        verifications,
        list,
    ):
        return {}

    result = {}

    for item in verifications:
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

        network = str(
            item.get(
                "network",
                "",
            )
        ).strip()

        if not service or not network:
            continue

        result[
            (
                service.lower(),
                network.lower(),
            )
        ] = item

    return result


def build_program_map(
    program_data: dict[str, Any],
) -> dict[str, dict[str, Any]]:

    programs = program_data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        return {}

    result = {}

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


def detect_domestic_asp(
    program: dict[str, Any],
) -> str:

    network = str(
        program.get(
            "network",
            "",
        )
    ).strip()

    notes = str(
        program.get(
            "research_notes",
            "",
        )
    )

    for asp in DOMESTIC_ASPS:

        if (
            asp.lower()
            in network.lower()
        ):
            return asp

    for asp in DOMESTIC_ASPS:

        if (
            asp.lower()
            in notes.lower()
        ):
            return asp

    return ""


def get_search_keywords(
    service: str,
) -> list[str]:

    return [
        service,
        f"{service} アフィリエイト",
        f"{service} A8",
        f"{service} もしも",
        f"{service} バリューコマース",
    ]


def calculate_priority(
    action_item: dict[str, Any],
    program: dict[str, Any],
    revenue_action: dict[str, Any] | None = None,
) -> int:

    base_priority = int(
        action_item.get(
            "priority",
            0,
        )
        or 0
    )

    action = str(
        action_item.get(
            "action",
            "",
        )
    )

    priority = base_priority

    if action == "REVIEW":
        priority += 15

    elif action == "NO_PROGRAM":
        priority += 10

    elif action == "NO_REVENUE":
        priority += 5

    notes = str(
        program.get(
            "research_notes",
            "",
        )
    )

    if (
        "ASP管理画面で要確認"
        in notes
    ):
        priority += 15

    existing_articles = (
        action_item.get(
            "existing_articles",
            [],
        )
    )

    if isinstance(
        existing_articles,
        list,
    ):
        if existing_articles:
            priority += 10

    if isinstance(
        revenue_action,
        dict,
    ):
        revenue_clicks = int(
            revenue_action.get(
                "clicks",
                0,
            )
            or 0
        )

        revenue_destination = str(
            revenue_action.get(
                "destination",
                "",
            )
        ).strip()

        if (
            revenue_destination
            == "monetization"
        ):
            priority += 10

        if revenue_clicks >= 10:
            priority += 20

        elif revenue_clicks >= 5:
            priority += 15

        elif revenue_clicks >= 2:
            priority += 10

        elif revenue_clicks >= 1:
            priority += 5

    return min(
        priority,
        100,
    )


def decide_candidate_action(
    action_item: dict[str, Any],
    program: dict[str, Any],
) -> tuple[str, str]:

    action = str(
        action_item.get(
            "action",
            "",
        )
    )

    status = str(
        action_item.get(
            "affiliate_status",
            "none",
        )
    )

    if status in {
        "pending",
        "active",
    }:
        return (
            "SKIP",
            "すでに申請済みまたは有効案件です。",
        )

    domestic_asp = (
        detect_domestic_asp(
            program
        )
    )

    if domestic_asp:
        return (
            "CHECK_DOMESTIC_ASP",
            f"{domestic_asp} に関連情報があるため、"
            "管理画面で案件確認を推奨します。",
        )

    notes = str(
        program.get(
            "research_notes",
            "",
        )
    )

    if (
        "ASP管理画面で要確認"
        in notes
    ):
        return (
            "CHECK_DOMESTIC_ASP",
            "公開Webでは国内ASP案件を確認できないため、"
            "主要ASP管理画面で確認を推奨します。",
        )

    if action in {
        "REVIEW",
        "NO_PROGRAM",
        "NO_REVENUE",
    }:
        return (
            "CHECK_DOMESTIC_ASP",
            "直接案件が弱いため、"
            "国内ASP経由の案件有無を確認する価値があります。",
        )

    return (
        "SKIP",
        "現時点では国内ASP確認の優先度が低いです。",
    )


def build_queue() -> list[dict[str, Any]]:
    revenue_action_data = load_json(
        REVENUE_ACTION_QUEUE_FILE
    )

    revenue_action_map = (
        build_revenue_action_map(
            revenue_action_data
        )
    )

    verification_data = load_json(
        VERIFICATION_HISTORY_FILE
    )

    verification_map = (
        build_verification_map(
            verification_data
        )
    )

    action_data = load_json(
        ACTION_QUEUE_FILE
    )

    program_data = load_json(
        PROGRAM_RESULTS_FILE
    )

    actions = action_data.get(
        "actions",
        [],
    )

    if not isinstance(
        actions,
        list,
    ):
        return []

    program_map = (
        build_program_map(
            program_data
        )
    )

    candidates = []

    for item in actions:

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

        program = program_map.get(
            service,
            {},
        )

        revenue_action = (
            revenue_action_map.get(
                service.lower(),
                {},
            )
        )

        candidate_action, reason = (
            decide_candidate_action(
                item,
                program,
            )
        )

        if (
            candidate_action
            != "CHECK_DOMESTIC_ASP"
        ):
            continue

        detected_asp = (
            detect_domestic_asp(
                program
            )
        )

        base_networks = (
            [detected_asp]
            if detected_asp
            else DOMESTIC_ASPS[:3]
        )

        found_networks = []
        unclear_networks = []
        unverified_networks = []

        for network in base_networks:

            verification = (
                verification_map.get(
                    (
                        service.lower(),
                        network.lower(),
                    )
                )
            )

            if verification is None:
                unverified_networks.append(
                    network
                )
                continue

            result = str(
                verification.get(
                    "result",
                    "",
                )
            ).strip()

            if result == "found":
                found_networks.append(
                    network
                )

            elif result == "unclear":
                unclear_networks.append(
                    network
                )

            elif result == "not_found":
                continue

            else:
                unverified_networks.append(
                    network
                )

        recommended_networks = (
            found_networks
            + unclear_networks
            + unverified_networks
        )

        if not recommended_networks:
            continue

        priority = (
            calculate_priority(
                item,
                program,
                revenue_action,
            )
        )

        candidates.append(
            {
                "service": service,
                "priority": priority,
                "action": (
                    candidate_action
                ),
                "current_action": (
                    item.get(
                        "action"
                    )
                ),
                "recommended_networks": (
                    recommended_networks
                ),
                "search_keywords": (
                    get_search_keywords(
                        service
                    )
                ),
                "existing_articles": (
                    item.get(
                        "existing_articles",
                        [],
                    )
                ),
                "direct_program_found": (
                    program.get(
                        "program_found"
                    )
                    is True
                ),
                "direct_program_name": str(
                    program.get(
                        "program_name",
                        "",
                    )
                ),
                "direct_network": str(
                    program.get(
                        "network",
                        "",
                    )
                ),
                "direct_commission": str(
                    program.get(
                        "commission",
                        "",
                    )
                ),
                "reason": reason,
                "revenue_signal": {
                    "source_action": str(
                        revenue_action.get(
                            "source_action",
                            "",
                        )
                    ),
                    "destination": str(
                        revenue_action.get(
                            "destination",
                            "",
                        )
                    ),
                    "clicks": int(
                        revenue_action.get(
                            "clicks",
                            0,
                        )
                        or 0
                    ),
                    "conversions": int(
                        revenue_action.get(
                            "conversions",
                            0,
                        )
                        or 0
                    ),
                    "revenue": float(
                        revenue_action.get(
                            "revenue",
                            0.0,
                        )
                        or 0.0
                    ),
                    "epc": float(
                        revenue_action.get(
                            "epc",
                            0.0,
                        )
                        or 0.0
                    ),
                },
                "verification_status": {
                    network: (
                        verification_map.get(
                            (
                                service.lower(),
                                network.lower(),
                            ),
                            {},
                        ).get(
                            "result",
                            "unverified",
                        )
                    )
                    for network
                    in recommended_networks
                },
            }
        )

    candidates.sort(
        key=lambda item: item[
            "priority"
        ],
        reverse=True,
    )

    return candidates[
        :MAX_CANDIDATES
    ]


def save_queue(
    candidates: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "max_candidates": (
                    MAX_CANDIDATES
                ),
                "candidates": (
                    candidates
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_queue(
    candidates: list[dict[str, Any]],
) -> None:

    print(
        "\n===== Domestic ASP Candidate Queue =====\n"
    )

    if not candidates:
        print(
            "現在、国内ASPで確認すべき"
            "高優先候補はありません。"
        )
        return

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        print(
            f"[{index}] "
            f"{item['service']}"
        )

        print(
            "    priority: "
            f"{item['priority']}"
        )

        print(
            "    current action: "
            f"{item['current_action']}"
        )

        print(
            "    推奨ASP: "
            + ", ".join(
                item[
                    "recommended_networks"
                ]
            )
        )

        print(
            "    確認状態:"
        )

        for network in item[
            "recommended_networks"
        ]:
            status = (
                item.get(
                    "verification_status",
                    {},
                ).get(
                    network,
                    "unverified",
                )
            )

            print(
                f"      - {network}: "
                f"{status}"
            )

        print(
            "    ASP検索語:"
        )

        for keyword in item[
            "search_keywords"
        ]:
            print(
                f"      - {keyword}"
            )

        articles = item.get(
            "existing_articles",
            [],
        )

        if articles:
            print(
                "    既存記事:"
            )

            for article in articles[
                :3
            ]:
                print(
                    "      - "
                    f"{article.get('slug', '')} "
                    f"(match "
                    f"{article.get('match_score', 0)})"
                )

        if item[
            "direct_program_found"
        ]:
            print(
                "    直接案件: "
                + (
                    item[
                        "direct_program_name"
                    ]
                    or "あり"
                )
            )

            print(
                "    直接報酬: "
                + (
                    item[
                        "direct_commission"
                    ]
                    or "不明"
                )
            )

        print(
            "    reason: "
            f"{item['reason']}"
        )

        print(
            "    next: "
            "上記ASPだけ管理画面で確認"
        )

        print()


def main() -> None:

    candidates = (
        build_queue()
    )

    filepath = (
        save_queue(
            candidates
        )
    )

    print_queue(
        candidates
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()