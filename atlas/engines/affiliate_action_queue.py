import json
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

AFFILIATE_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_links.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_action_queue.json"
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


def build_match_map(
    monetization_data: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:

    matches = monetization_data.get(
        "matches",
        [],
    )

    if not isinstance(
        matches,
        list,
    ):
        return {}

    result: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for item in matches:
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

        result.setdefault(
            service,
            [],
        ).append(
            item
        )

    return result


def get_affiliate_status(
    registry: dict[str, Any],
    service: str,
) -> str:

    item = registry.get(
        service,
        {},
    )

    if not isinstance(
        item,
        dict,
    ):
        return "none"

    return str(
        item.get(
            "affiliate_status",
            "none",
        )
    ).strip()


def calculate_priority(
    program: dict[str, Any],
    matches: list[dict[str, Any]],
    affiliate_status: str,
) -> int:

    if affiliate_status == "active":
        return 0

    if affiliate_status == "pending":
        return 90

    if program.get(
        "program_found"
    ) is not True:
        return 20

    program_type = str(
        program.get(
            "program_type",
            "",
        )
        or ""
    ).strip()

    commission = str(
        program.get(
            "commission",
            "",
        )
    ).strip()

    network = str(
        program.get(
            "network",
            "",
        )
    ).strip()

    priority = 40

    if program_type == "affiliate":
        priority += 20

    if commission:
        priority += 15

    if network:
        priority += 5

    if matches:
        best_match = max(
            int(
                item.get(
                    "match_score",
                    0,
                )
                or 0
            )
            for item in matches
        )

        priority += min(
            20,
            round(
                best_match * 0.20
            ),
        )

    return min(
        priority,
        100,
    )


def decide_action(
    program: dict[str, Any],
    matches: list[dict[str, Any]],
    affiliate_status: str,
) -> tuple[str, str]:

    if affiliate_status == "active":
        return (
            "ACTIVE",
            "アフィリエイト案件はすでに有効です。",
        )

    if affiliate_status == "pending":
        return (
            "WAIT",
            "提携申請済み・審査待ちです。",
        )

    if affiliate_status == "rejected":
        return (
            "REVIEW_LATER",
            "過去に提携が却下されています。",
        )

    program_found = (
        program.get("program_found")
        is True
    )

    if not program_found:
        notes = str(
            program.get(
                "research_notes",
                "",
            )
        )

        if "ASP管理画面で要確認" in notes:
            return (
                "VERIFY_ASP",
                "公開Webでは案件を確認できません。"
                "ASP管理画面での確認候補です。",
            )

        return (
            "NO_PROGRAM",
            "現在利用可能な案件を確認できませんでした。",
        )

    program_type = str(
        program.get(
            "program_type",
            "",
        )
        or ""
    ).strip()

    commission = str(
        program.get(
            "commission",
            "",
        )
    ).strip()

    commission_lower = (
        commission.lower()
    )

    # 金銭報酬がない制度は収益化案件として扱わない
    no_cash_reward_terms = [
        "no cash payout",
        "no monetary reward",
        "no commission",
        "free trial only",
        "usage credit",
        "credits only",
    ]

    if any(
        term in commission_lower
        for term in no_cash_reward_terms
    ):
        return (
            "NO_REVENUE",
            "紹介制度はありますが、"
            "現金報酬のある収益化案件ではありません。",
        )

    if program_type == "referral":
        if not commission:
            return (
                "REVIEW",
                "Referral制度はありますが、"
                "金銭報酬を確認できません。",
            )

    if program_type in {
        "partner",
        "creator",
        "other",
    }:
        if not commission:
            return (
                "REVIEW",
                "一般的な成果報酬型Affiliateか"
                "人間による確認が必要です。",
            )

    # Affiliate案件でも報酬条件が確認できなければ要確認
    if (
        program_type == "affiliate"
        and not commission
    ):
        return (
            "REVIEW",
            "Affiliate Programはありますが、"
            "報酬条件を確認できていません。",
        )

    if matches:
        return (
            "APPLY_EXISTING",
            "利用可能な収益化案件があり、"
            "既存記事との関連も確認されています。",
        )

    return (
        "CREATE_ARTICLE",
        "利用可能な収益化案件がありますが、"
        "現在の既存記事との紐付けがありません。",
    )


def build_action_queue() -> list[dict[str, Any]]:

    program_data = load_json(
        PROGRAM_RESULTS_FILE
    )

    monetization_data = load_json(
        MONETIZATION_MATCHES_FILE
    )

    registry = load_json(
        AFFILIATE_LINKS_FILE
    )

    programs = program_data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        programs = []

    match_map = build_match_map(
        monetization_data
    )

    program_map: dict[
        str,
        dict[str, Any],
    ] = {}

    for program in programs:
        if not isinstance(
            program,
            dict,
        ):
            continue

        service = str(
            program.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        program_map[
            service
        ] = program

    # Registryにあるサービスも必ず評価対象にする
    services = set(
        program_map.keys()
    )

    services.update(
        str(service)
        for service in registry.keys()
    )

    actions = []

    for service in services:

        program = program_map.get(
            service,
            {
                "service": service,
                "program_found": False,
                "program_type": None,
                "program_name": "",
                "network": "",
                "program_url": "",
                "commission": "",
                "cookie_duration": "",
                "target_country": "",
                "application_required": None,
                "research_notes": (
                    "案件調査結果がありません。"
                ),
                "sources": [],
                "verified_at": None,
            },
        )

        matches = match_map.get(
            service,
            [],
        )

        affiliate_status = (
            get_affiliate_status(
                registry,
                service,
            )
        )

        action, reason = (
            decide_action(
                program,
                matches,
                affiliate_status,
            )
        )

        priority = (
            calculate_priority(
                program,
                matches,
                affiliate_status,
            )
        )

        existing_articles = []

        for match in matches:
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

            score = int(
                match.get(
                    "match_score",
                    0,
                )
                or 0
            )

            if not slug:
                continue

            existing_articles.append(
                {
                    "slug": slug,
                    "title": title,
                    "match_score": score,
                }
            )

        existing_articles.sort(
            key=lambda item: item[
                "match_score"
            ],
            reverse=True,
        )

        actions.append(
            {
                "service": service,
                "priority": priority,
                "action": action,
                "affiliate_status": (
                    affiliate_status
                ),
                "program_found": (
                    program.get(
                        "program_found"
                    )
                    is True
                ),
                "program_type": (
                    program.get(
                        "program_type"
                    )
                ),
                "program_name": str(
                    program.get(
                        "program_name",
                        "",
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
                "verified_at": (
                    program.get(
                        "verified_at"
                    )
                ),
                "reason": reason,
                "existing_articles": (
                    existing_articles
                ),
            }
        )

    action_order = {
        "APPLY_EXISTING": 0,
        "WAIT": 1,
        "CREATE_ARTICLE": 2,
        "VERIFY_ASP": 3,
        "REVIEW": 4,
        "REVIEW_LATER": 5,
        "NO_REVENUE": 6,
        "NO_PROGRAM": 7,
        "ACTIVE": 8,
    }

    actions.sort(
        key=lambda item: (
            action_order.get(
                item[
                    "action"
                ],
                99,
            ),
            -item[
                "priority"
            ],
        )
    )

    return actions


def save_action_queue(
    actions: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "actions": actions,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_action_queue(
    actions: list[dict[str, Any]],
) -> None:

    print(
        "\n===== Today's Affiliate Actions =====\n"
    )

    actionable = [
        item
        for item in actions
        if item[
            "action"
        ]
        != "ACTIVE"
    ]

    if not actionable:
        print(
            "現在対応が必要な案件はありません。"
        )
        return

    for index, item in enumerate(
        actionable,
        start=1,
    ):

        print(
            f"[{index}] "
            f"{item['service']}"
        )

        print(
            "    action: "
            f"{item['action']}"
        )

        print(
            "    priority: "
            f"{item['priority']}"
        )

        print(
            "    status: "
            f"{item['affiliate_status']}"
        )

        print(
            "    network: "
            + (
                item[
                    "network"
                ]
                or "不明"
            )
        )

        print(
            "    program: "
            + (
                item[
                    "program_name"
                ]
                or "不明"
            )
        )

        print(
            "    commission: "
            + (
                item[
                    "commission"
                ]
                or "不明"
            )
        )

        print(
            "    cookie: "
            + (
                item[
                    "cookie_duration"
                ]
                or "不明"
            )
        )

        articles = item.get(
            "existing_articles",
            [],
        )

        if articles:
            print(
                "    existing articles:"
            )

            for article in articles:
                print(
                    "      - "
                    f"{article['slug']} "
                    f"(match "
                    f"{article['match_score']})"
                )

        print(
            "    reason: "
            f"{item['reason']}"
        )

        if item[
            "action"
        ] == "APPLY_EXISTING":
            print(
                "    next: "
                "案件へ提携申請"
            )

        elif item[
            "action"
        ] == "CREATE_ARTICLE":
            print(
                "    next: "
                "新規記事候補として評価"
            )

        elif item[
            "action"
        ] == "WAIT":
            print(
                "    next: "
                "審査結果を待つ"
            )

        elif item[
            "action"
        ] == "VERIFY_ASP":
            print(
                "    next: "
                "ASP管理画面で案件有無を確認"
            )

        elif item[
            "action"
        ] == "NO_REVENUE":
            print(
                "    next: "
                "収益化対象から除外"
            )
        print()


def main() -> None:

    actions = (
        build_action_queue()
    )

    filepath = (
        save_action_queue(
            actions
        )
    )

    print_action_queue(
        actions
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()