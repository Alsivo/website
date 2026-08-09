import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "rewrite_history.json"
)

DEFAULT_COOLDOWN_DAYS = 14


def load_rewrite_history(
) -> list[dict[str, Any]]:
    """リライト履歴を読み込む。"""

    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(
            HISTORY_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "rewrite_history.jsonの"
            "JSON形式が不正です。"
        ) from error

    history = data.get(
        "history",
        [],
    )

    if not isinstance(
        history,
        list,
    ):
        raise ValueError(
            "historyは配列にしてください。"
        )

    return [
        item
        for item in history
        if isinstance(
            item,
            dict,
        )
    ]


def save_rewrite_history(
    history: list[dict[str, Any]],
) -> Path:
    """リライト履歴を保存する。"""

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HISTORY_FILE.write_text(
        json.dumps(
            {
                "history": history,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return HISTORY_FILE

def record_rewrite(
    slug: str,
    title: str = "",
    reason: str = "",
) -> Path:
    """リライト実行履歴を1件追加する。"""

    slug = slug.strip()

    if not slug:
        raise ValueError(
            "slugが未入力です。"
        )

    history = (
        load_rewrite_history()
    )

    history.append(
        {
            "slug": slug,
            "title": title.strip(),
            "rewritten_at":
                datetime.now().isoformat(),
            "reason": reason.strip(),
        }
    )

    # 履歴が無限に増えないよう
    # 直近500件まで保存
    history = history[-500:]

    return save_rewrite_history(
        history
    )

def get_last_rewrite(
    slug: str,
) -> dict[str, Any] | None:
    """指定記事の最新リライト履歴を返す。"""

    slug = slug.strip()

    history = (
        load_rewrite_history()
    )

    matches = [
        item
        for item in history
        if str(
            item.get(
                "slug",
                "",
            )
        ).strip()
        == slug
    ]

    if not matches:
        return None

    matches.sort(
        key=lambda item: str(
            item.get(
                "rewritten_at",
                "",
            )
        ),
        reverse=True,
    )

    return matches[0]


def is_rewrite_allowed(
    slug: str,
    cooldown_days: int = (
        DEFAULT_COOLDOWN_DAYS
    ),
) -> tuple[bool, str]:
    """クールダウン期間を満たすか判定する。"""

    last_rewrite = (
        get_last_rewrite(
            slug
        )
    )

    if last_rewrite is None:
        return (
            True,
            "過去のリライト履歴なし",
        )

    rewritten_at_text = str(
        last_rewrite.get(
            "rewritten_at",
            "",
        )
    ).strip()

    try:
        rewritten_at = (
            datetime.fromisoformat(
                rewritten_at_text
            )
        )
    except ValueError:
        return (
            True,
            "過去履歴の日時形式が不正なため許可",
        )

    elapsed = (
        datetime.now()
        - rewritten_at
    )

    cooldown = timedelta(
        days=cooldown_days
    )

    if elapsed < cooldown:
        remaining = (
            cooldown
            - elapsed
        )

        remaining_days = max(
            1,
            remaining.days + 1,
        )

        return (
            False,
            (
                "クールダウン中です。"
                f"あと約{remaining_days}日"
            ),
        )

    return (
        True,
        "クールダウン期間終了",
    )

def main() -> None:
    history = (
        load_rewrite_history()
    )

    print(
        "\n===== Rewrite History =====\n"
    )

    if not history:
        print(
            "リライト履歴はありません。"
        )
        return

    for item in history[-10:]:
        print(
            f"{item.get('slug')} / "
            f"{item.get('rewritten_at')}"
        )


if __name__ == "__main__":
    main()
