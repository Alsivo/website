import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "asp_verification_history.json"
)

ALLOWED_RESULTS = {
    "found",
    "not_found",
    "unclear",
}

VERIFICATION_COOLDOWN_DAYS = 30


def load_history() -> list[dict[str, Any]]:
    if not OUTPUT_FILE.exists():
        return []

    try:
        data = json.loads(
            OUTPUT_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "asp_verification_history.json の"
            "JSON形式が不正です。"
        ) from error

    history = data.get(
        "verifications",
        [],
    )

    if not isinstance(
        history,
        list,
    ):
        raise ValueError(
            "verifications は配列にしてください。"
        )

    return [
        item
        for item in history
        if isinstance(
            item,
            dict,
        )
    ]


def save_history(
    history: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "verification_cooldown_days": (
                    VERIFICATION_COOLDOWN_DAYS
                ),
                "verifications": history,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def normalize_network(
    network: str,
) -> str:

    value = network.strip()

    aliases = {
        "a8": "A8.net",
        "a8.net": "A8.net",
        "もしも": "もしもアフィリエイト",
        "もしもアフィリエイト": "もしもアフィリエイト",
        "valuecommerce": "バリューコマース",
        "バリューコマース": "バリューコマース",
        "afb": "afb",
        "アクセストレード": "アクセストレード",
    }

    return aliases.get(
        value.lower(),
        value,
    )


def upsert_verification(
    history: list[dict[str, Any]],
    service: str,
    network: str,
    result: str,
    notes: str,
    program_name: str,
    program_url: str,
) -> list[dict[str, Any]]:

    today = date.today().isoformat()

    item = {
        "service": service,
        "network": network,
        "result": result,
        "verified_at": today,
        "notes": notes,
        "program_name": program_name,
        "program_url": program_url,
    }

    updated = False

    for index, existing in enumerate(
        history
    ):
        existing_service = str(
            existing.get(
                "service",
                "",
            )
        ).strip()

        existing_network = str(
            existing.get(
                "network",
                "",
            )
        ).strip()

        if (
            existing_service.lower()
            == service.lower()
            and existing_network.lower()
            == network.lower()
        ):
            history[index] = item
            updated = True
            break

    if not updated:
        history.append(
            item
        )

    history.sort(
        key=lambda x: (
            str(
                x.get(
                    "service",
                    "",
                )
            ).lower(),
            str(
                x.get(
                    "network",
                    "",
                )
            ).lower(),
        )
    )

    return history


def is_recent(
    item: dict[str, Any],
) -> bool:

    verified_at_text = str(
        item.get(
            "verified_at",
            "",
        )
    ).strip()

    if not verified_at_text:
        return False

    try:
        verified_at = (
            datetime.fromisoformat(
                verified_at_text
            ).date()
        )
    except ValueError:
        return False

    elapsed_days = (
        date.today()
        - verified_at
    ).days

    return (
        0
        <= elapsed_days
        < VERIFICATION_COOLDOWN_DAYS
    )


def get_recent_verification(
    service: str,
    network: str,
) -> dict[str, Any] | None:

    history = load_history()

    for item in history:

        item_service = str(
            item.get(
                "service",
                "",
            )
        ).strip()

        item_network = str(
            item.get(
                "network",
                "",
            )
        ).strip()

        if (
            item_service.lower()
            != service.lower()
        ):
            continue

        if (
            item_network.lower()
            != network.lower()
        ):
            continue

        if is_recent(
            item
        ):
            return item

    return None


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "国内ASPの案件確認結果を"
            "Atlasへ記録します。"
        )
    )

    parser.add_argument(
        "--service",
        required=True,
        help="サービス名",
    )

    parser.add_argument(
        "--network",
        required=True,
        help="ASP名",
    )

    parser.add_argument(
        "--result",
        required=True,
        choices=sorted(
            ALLOWED_RESULTS
        ),
        help=(
            "found / not_found / unclear"
        ),
    )

    parser.add_argument(
        "--notes",
        default="",
        help="確認メモ",
    )

    parser.add_argument(
        "--program-name",
        default="",
        help="案件名",
    )

    parser.add_argument(
        "--program-url",
        default="",
        help="案件URL",
    )

    args = parser.parse_args()

    service = (
        args.service.strip()
    )

    network = normalize_network(
        args.network
    )

    if (
        args.result == "found"
        and not args.program_name.strip()
    ):
        print(
            "注意: found ですが"
            " program_name が未入力です。"
        )

    history = load_history()

    history = upsert_verification(
        history=history,
        service=service,
        network=network,
        result=args.result,
        notes=args.notes,
        program_name=(
            args.program_name.strip()
        ),
        program_url=(
            args.program_url.strip()
        ),
    )

    filepath = save_history(
        history
    )

    print(
        "\n===== ASP Verification Tracker =====\n"
    )

    print(
        f"service: {service}"
    )

    print(
        f"network: {network}"
    )

    print(
        f"result: {args.result}"
    )

    print(
        f"verified_at: "
        f"{date.today().isoformat()}"
    )

    if args.notes:
        print(
            f"notes: {args.notes}"
        )

    if args.program_name:
        print(
            "program: "
            f"{args.program_name}"
        )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()