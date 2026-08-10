import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


DATA_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
)

PROGRAMS_FILE = (
    DATA_DIR
    / "affiliate_programs.csv"
)

REGISTRY_FILE = (
    DATA_DIR
    / "affiliate_links.json"
)

ALLOWED_STATUSES = {
    "none",
    "pending",
    "active",
    "paused",
    "rejected",
}

ALLOWED_REWARD_TYPES = {
    "none",
    "fixed",
    "percent",
}


def parse_float(
    value: str,
    default: float = 0.0,
) -> float:
    """CSV内の数値を安全にfloatへ変換する。"""

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(
    value: str,
    default: int = 0,
) -> int:
    """CSV内の数値を安全にintへ変換する。"""

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_date_score(
    value: str,
) -> float:
    """
    最終確認日から鮮度スコアを計算する。

    30日以内：100
    90日以内：70
    180日以内：40
    それ以上：10
    """

    try:
        verified_date = datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()
    except (TypeError, ValueError):
        return 0.0

    elapsed_days = (
        date.today() - verified_date
    ).days

    if elapsed_days <= 30:
        return 100.0

    if elapsed_days <= 90:
        return 70.0

    if elapsed_days <= 180:
        return 40.0

    return 10.0


def load_affiliate_programs() -> list[dict[str, Any]]:
    """ASP案件CSVを読み込み、内容を検証する。"""

    if not PROGRAMS_FILE.exists():
        raise FileNotFoundError(
            "affiliate_programs.csvが見つかりません："
            f"{PROGRAMS_FILE}"
        )

    programs: list[dict[str, Any]] = []

    with PROGRAMS_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        required_columns = {
            "tool_name",
            "network",
            "program_name",
            "status",
            "official_url",
            "affiliate_url",
            "reward_type",
            "reward_value",
            "currency",
            "conversion_action",
            "cookie_days",
            "approval_score",
            "article_match_score",
            "last_verified",
            "notes",
        }

        actual_columns = set(
            reader.fieldnames or []
        )

        missing_columns = (
            required_columns
            - actual_columns
        )

        if missing_columns:
            raise ValueError(
                "affiliate_programs.csvに"
                "必要な列がありません："
                + ", ".join(
                    sorted(missing_columns)
                )
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):
            tool_name = (
                row["tool_name"].strip()
            )

            if not tool_name:
                raise ValueError(
                    f"{row_number}行目の"
                    "tool_nameが未入力です。"
                )

            status = row["status"].strip()

            if status not in ALLOWED_STATUSES:
                raise ValueError(
                    f"{row_number}行目のstatusが"
                    f"不正です：{status}"
                )

            reward_type = (
                row["reward_type"].strip()
            )

            if (
                reward_type
                not in ALLOWED_REWARD_TYPES
            ):
                raise ValueError(
                    f"{row_number}行目の"
                    "reward_typeが不正です："
                    f"{reward_type}"
                )

            official_url = (
                row["official_url"].strip()
            )

            affiliate_url = (
                row["affiliate_url"].strip()
            )

            if (
                not official_url.startswith(
                    "http"
                )
            ):
                raise ValueError(
                    f"{row_number}行目の"
                    "official_urlが不正です。"
                )

            if (
                status == "active"
                and not affiliate_url.startswith(
                    "http"
                )
            ):
                raise ValueError(
                    f"{row_number}行目はactiveですが、"
                    "affiliate_urlが未入力です。"
                )

            programs.append(
                {
                    "tool_name": tool_name,
                    "network": (
                        row["network"].strip()
                    ),
                    "program_name": (
                        row[
                            "program_name"
                        ].strip()
                    ),
                    "status": status,
                    "official_url": (
                        official_url
                    ),
                    "affiliate_url": (
                        affiliate_url
                    ),
                    "reward_type": (
                        reward_type
                    ),
                    "reward_value": parse_float(
                        row["reward_value"]
                    ),
                    "currency": (
                        row["currency"].strip()
                    ),
                    "conversion_action": (
                        row[
                            "conversion_action"
                        ].strip()
                    ),
                    "cookie_days": parse_int(
                        row["cookie_days"]
                    ),
                    "approval_score": parse_float(
                        row["approval_score"]
                    ),
                    "article_match_score": parse_float(
                        row[
                            "article_match_score"
                        ]
                    ),
                    "last_verified": (
                        row[
                            "last_verified"
                        ].strip()
                    ),
                    "notes": (
                        row["notes"].strip()
                    ),
                }
            )

    return programs


def calculate_program_score(
    program: dict[str, Any],
) -> float:
    """案件の紹介優先度を0～100点で算出する。"""

    if program["status"] != "active":
        return 0.0

    reward_value = float(
        program["reward_value"]
    )

    reward_type = program[
        "reward_type"
    ]

    if reward_type == "fixed":
        reward_score = min(
            100.0,
            reward_value / 20.0,
        )
    elif reward_type == "percent":
        reward_score = min(
            100.0,
            reward_value * 4.0,
        )
    else:
        reward_score = 0.0

    approval_score = min(
        100.0,
        max(
            0.0,
            float(
                program[
                    "approval_score"
                ]
            ),
        ),
    )

    article_match_score = min(
        100.0,
        max(
            0.0,
            float(
                program[
                    "article_match_score"
                ]
            ),
        ),
    )

    cookie_score = min(
        100.0,
        float(
            program["cookie_days"]
        ) * 3.0,
    )

    freshness_score = parse_date_score(
        program["last_verified"]
    )

    total_score = (
        reward_score * 0.30
        + approval_score * 0.25
        + article_match_score * 0.30
        + cookie_score * 0.05
        + freshness_score * 0.10
    )

    return round(total_score, 2)


def select_best_programs() -> dict[str, dict[str, Any]]:
    """
    サービスごとに最も評価の高い
    承認済み案件を選択する。
    """

    programs = load_affiliate_programs()

    grouped: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    for program in programs:
        grouped.setdefault(
            program["tool_name"],
            [],
        ).append(program)

    selected: dict[str, dict[str, Any]] = {}

    for tool_name, candidates in grouped.items():
        active_candidates = [
            {
                **candidate,
                "program_score":
                    calculate_program_score(
                        candidate
                    ),
            }
            for candidate in candidates
            if candidate["status"] == "active"
            and candidate["affiliate_url"]
        ]

        if active_candidates:
            best_program = max(
                active_candidates,
                key=lambda item: (
                    item["program_score"],
                    item["reward_value"],
                ),
            )

            selected[tool_name] = (
                best_program
            )
            continue

        official_candidate = candidates[0]

        selected[tool_name] = {
            **official_candidate,
            "status": "none",
            "affiliate_url": "",
            "program_score": 0.0,
        }

    return selected


def create_cta_label(
    tool_name: str,
    selected_program: dict[str, Any],
) -> str:
    """CTAの文言を作る。"""

    action = selected_program.get(
        "conversion_action",
        "",
    )

    if (
        selected_program["status"]
        == "active"
        and action
        and action != "なし"
    ):
        return (
            f"{tool_name}の"
            f"{action}を確認する"
        )

    return (
        f"{tool_name}を"
        "公式サイトで確認する"
    )


def sync_affiliate_registry() -> dict[str, dict[str, Any]]:
    """
    最適案件を選択して、
    affiliate_links.jsonを安全に更新する。

    既存サービスは保持し、
    今回取得したサービスだけ最新情報で上書きする。
    """

    selected_programs = (
        select_best_programs()
    )

    # ----------------------------------------------------
    # 既存Registryを読み込み
    # ----------------------------------------------------

    registry: dict[
        str,
        dict[str, Any],
    ] = {}

    if REGISTRY_FILE.exists():
        try:
            existing_data = json.loads(
                REGISTRY_FILE.read_text(
                    encoding="utf-8",
                )
            )

            if isinstance(
                existing_data,
                dict,
            ):
                registry = {
                    str(key): value
                    for key, value
                    in existing_data.items()
                    if isinstance(
                        value,
                        dict,
                    )
                }

        except json.JSONDecodeError:
            # 壊れている場合のみ
            # 新規Registryとして再構築する
            registry = {}

    # ----------------------------------------------------
    # 今回取得したサービスだけ更新
    # ----------------------------------------------------

    for tool_name, program in (
        selected_programs.items()
    ):
        existing_item = (
            registry.get(
                tool_name,
                {},
            )
        )

        existing_aliases = (
            existing_item.get(
                "aliases",
                [],
            )
            if isinstance(
                existing_item,
                dict,
            )
            else []
        )

        if not isinstance(
            existing_aliases,
            list,
        ):
            existing_aliases = []

        aliases = [
            str(alias).strip()
            for alias
            in existing_aliases
            if str(alias).strip()
        ]

        if tool_name not in aliases:
            aliases.insert(
                0,
                tool_name,
            )

        registry[tool_name] = {
            "official_url": (
                program["official_url"]
            ),
            "affiliate_url": (
                program["affiliate_url"]
                if program["status"]
                == "active"
                else ""
            ),
            "cta_label": create_cta_label(
                tool_name,
                program,
            ),
            "aliases": aliases,
            "affiliate_status": (
                program["status"]
            ),
            "network": (
                program["network"]
            ),
            "program_name": (
                program["program_name"]
            ),
            "reward_type": (
                program["reward_type"]
            ),
            "reward_value": (
                program["reward_value"]
            ),
            "currency": (
                program["currency"]
            ),
            "conversion_action": (
                program[
                    "conversion_action"
                ]
            ),
            "cookie_days": (
                program["cookie_days"]
            ),
            "program_score": (
                program["program_score"]
            ),
            "last_verified": (
                program["last_verified"]
            ),
        }

    REGISTRY_FILE.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return registry


def print_affiliate_selection() -> None:
    """選択された案件をコンソールへ表示する。"""

    registry = sync_affiliate_registry()

    print(
        "\n===== Affiliate Manager ====="
    )

    for tool_name, item in registry.items():
        if (
            item["affiliate_status"]
            == "active"
        ):
            print(
                f"- {tool_name}: "
                f"{item['network']} / "
                f"{item['program_name']} / "
                f"{item['program_score']}点"
            )
        else:
            print(
                f"- {tool_name}: "
                "広告案件なし "
                "→ 公式URLを使用"
            )