import argparse
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

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


def get_approved_programs(
    approval_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """申請可と人間が判断した案件だけ取得する。"""

    programs = approval_data.get(
        "programs",
        [],
    )

    if not isinstance(
        programs,
        list,
    ):
        raise ValueError(
            "human_approval_queue.jsonの"
            "programsは配列にしてください。"
        )

    result = []

    for item in programs:
        if not isinstance(
            item,
            dict,
        ):
            continue

        if item.get(
            "approval_status"
        ) not in {
            "approved_for_application",
            "applied",
            "approved",
        }:
            continue

        result.append(
            item
        )

    return result

def build_activation_preview(
    approved_programs: list[dict[str, Any]],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    """Affiliate Registry更新候補を作る。"""

    preview = []

    for program in approved_programs:
        service = str(
            program.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        registry_item = registry.get(
            service
        )

        if not isinstance(
            registry_item,
            dict,
        ):
            continue

        approval_status = str(
            program.get(
                "approval_status",
                "",
            )
        ).strip()

        if approval_status == (
            "approved_for_application"
        ):
            next_status = (
                registry_item.get(
                    "affiliate_status",
                    "none",
                )
            )

        elif approval_status == "applied":
            next_status = "pending"

        elif approval_status == "approved":
            next_status = "active"

        else:
            continue

        preview.append(
            {
                "service": service,
                "approval_status": (
                    approval_status
                ),
                "current_affiliate_status": (
                    registry_item.get(
                        "affiliate_status",
                        "none",
                    )
                ),
                "next_affiliate_status": (
                    next_status
                ),
                "network": program.get(
                    "network",
                    "",
                ),
                "program_name": program.get(
                    "program_name",
                    "",
                ),
            }
        )

    return preview

def print_activation_preview(
    preview: list[dict[str, Any]],
) -> None:
    """更新予定を表示する。"""

    print(
        "\n===== Affiliate Activation Preview =====\n"
    )

    if not preview:
        print(
            "現在、反映対象はありません。"
        )
        return

    for item in preview:
        print(
            f"{item['service']}"
        )

        print(
            "  approval_status: "
            f"{item['approval_status']}"
        )

        print(
            "  affiliate_status: "
            f"{item['current_affiliate_status']}"
            " -> "
            f"{item['next_affiliate_status']}"
        )

        print(
            "  network: "
            + (
                item["network"]
                or "未設定"
            )
        )

        print()

def apply_activation_updates(
    approved_programs: list[dict[str, Any]],
    registry: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Human Approval Queueの状態を
    affiliate_links.jsonへ安全に反映する。
    """

    updated_registry = dict(
        registry
    )

    messages: list[str] = []

    for program in approved_programs:
        service = str(
            program.get(
                "service",
                "",
            )
        ).strip()

        if not service:
            continue

        registry_item = updated_registry.get(
            service
        )

        if not isinstance(
            registry_item,
            dict,
        ):
            messages.append(
                f"{service}: Registry未登録のためスキップ"
            )
            continue

        approval_status = str(
            program.get(
                "approval_status",
                "",
            )
        ).strip()

        updated_item = dict(
            registry_item
        )

        # ----------------------------------------------------
        # まだ申請前
        # ----------------------------------------------------

        if (
            approval_status
            == "approved_for_application"
        ):
            messages.append(
                f"{service}: 申請前のため変更なし"
            )
            continue

        # ----------------------------------------------------
        # 申請済み → pending
        # ----------------------------------------------------

        if approval_status == "applied":
            updated_item[
                "affiliate_status"
            ] = "pending"

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

            for key in ("program_id", "promotion_details"):
                value = str(program.get(key, "")).strip()
                if value:
                    updated_item[key] = value

            updated_registry[
                service
            ] = updated_item

            messages.append(
                f"{service}: pendingへ更新"
            )

            continue

        # ----------------------------------------------------
        # 承認済み → active
        # ----------------------------------------------------

        if approval_status == "approved":
            affiliate_url = str(
                program.get(
                    "affiliate_url",
                    "",
                )
            ).strip()

            if not affiliate_url:
                raise ValueError(
                    f"{service}はapprovedですが、"
                    "affiliate_urlが未入力です。"
                )

            if not affiliate_url.startswith(
                "http"
            ):
                raise ValueError(
                    f"{service}のaffiliate_urlが"
                    "不正です。"
                )

            updated_item[
                "affiliate_status"
            ] = "active"

            updated_item[
                "affiliate_url"
            ] = affiliate_url

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

            for key in ("program_id", "promotion_details"):
                value = str(program.get(key, "")).strip()
                if value:
                    updated_item[key] = value

            updated_registry[
                service
            ] = updated_item

            messages.append(
                f"{service}: activeへ更新"
            )

    return (
        updated_registry,
        messages,
    )

def save_affiliate_registry(
    registry: dict[str, Any],
) -> None:
    """affiliate_links.jsonを保存する。"""

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
            "Affiliate案件状態を"
            "affiliate_links.jsonへ反映します。"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "実際にaffiliate_links.jsonを"
            "更新する場合に指定します。"
        ),
    )

    args = parser.parse_args()

    approval_data = load_json(
        APPROVAL_QUEUE_FILE
    )

    registry = load_json(
        AFFILIATE_LINKS_FILE
    )

    approved_programs = (
        get_approved_programs(
            approval_data
        )
    )

    preview = (
        build_activation_preview(
            approved_programs,
            registry,
        )
    )

    print_activation_preview(
        preview
    )

    if not args.apply:
        print(
            "\nDry Runです。"
            "affiliate_links.jsonは"
            "変更していません。"
        )
        print(
            "実際に反映する場合のみ"
            " --apply を付けて実行してください。"
        )
        return

    updated_registry, messages = (
        apply_activation_updates(
            approved_programs,
            registry,
        )
    )

    save_affiliate_registry(
        updated_registry
    )

    print(
        "\n===== Affiliate Activation Result =====\n"
    )

    for message in messages:
        print(
            f"- {message}"
        )

    print(
        "\naffiliate_links.jsonを更新しました。"
    )


if __name__ == "__main__":
    main()
