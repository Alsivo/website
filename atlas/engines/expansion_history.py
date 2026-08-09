import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "expansion_history.json"
)


def load_expansion_history(
) -> list[dict[str, Any]]:
    """記事拡張の使用履歴を読み込む。"""

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
            "expansion_history.jsonの"
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


def save_expansion_history(
    history: list[dict[str, Any]],
) -> Path:
    """記事拡張履歴を保存する。"""

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    HISTORY_FILE.write_text(
        json.dumps(
            {
                "history":
                    history[-500:],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return HISTORY_FILE


def record_expansion_used(
    topic: str,
    target_keyword: str,
    article_slug: str = "",
    article_title: str = "",
) -> Path:
    """生成に成功したExpansion候補を履歴へ記録する。"""

    topic = topic.strip()
    target_keyword = (
        target_keyword.strip()
    )

    if not topic:
        raise ValueError(
            "Expansion topicが"
            "未入力です。"
        )

    history = (
        load_expansion_history()
    )

    history.append(
        {
            "topic":
                topic,
            "target_keyword":
                target_keyword,
            "article_slug":
                article_slug.strip(),
            "article_title":
                article_title.strip(),
            "used_at":
                datetime.now().isoformat(),
        }
    )

    return save_expansion_history(
        history
    )


def expansion_was_used(
    topic: str,
    target_keyword: str = "",
) -> bool:
    """同じExpansion候補を過去に使用済みか確認する。"""

    topic = topic.strip().lower()
    target_keyword = (
        target_keyword
        .strip()
        .lower()
    )

    history = (
        load_expansion_history()
    )

    for item in history:
        past_topic = str(
            item.get(
                "topic",
                "",
            )
        ).strip().lower()

        past_keyword = str(
            item.get(
                "target_keyword",
                "",
            )
        ).strip().lower()

        if (
            topic
            and past_topic == topic
        ):
            return True

        if (
            target_keyword
            and past_keyword
            == target_keyword
        ):
            return True

    return False


def main() -> None:
    history = (
        load_expansion_history()
    )

    print(
        "\n===== Expansion History =====\n"
    )

    if not history:
        print(
            "Expansion履歴はありません。"
        )
        return

    for item in history[-10:]:
        print(
            f"{item.get('topic')} / "
            f"{item.get('target_keyword')} / "
            f"{item.get('used_at')}"
        )


if __name__ == "__main__":
    main()