import json
from datetime import datetime
from pathlib import Path
from typing import Any
from openai import OpenAI
from config import (
    OPENAI_API_KEY,
    MODEL,
)


BASE_DIR = Path(__file__).resolve().parents[1]

SOCIAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_queue.json"
)


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def build_prompt(
    item: dict[str, Any],
) -> str:
    """媒体別の投稿文生成Promptを作る。"""

    platform = str(
        item.get(
            "platform",
            "",
        )
    ).strip()

    title = str(
        item.get(
            "article_title",
            "",
        )
    ).strip()

    description = str(
        item.get(
            "article_description",
            "",
        )
    ).strip()

    url = str(
        item.get(
            "article_url",
            "",
        )
    ).strip()

    if platform == "x":
        rules = """
X向けの投稿文を作成してください。

条件：
- 日本語
- 220文字以内を目安
- 最初の1文で興味を引く
- 誇張しない
- 記事内容と一致させる
- URLを最後にそのまま付ける
- ハッシュタグは0〜2個
- 「ブログを更新しました」だけの弱い文章にしない
"""

    elif platform == "instagram":
        rules = """
Instagram向けの投稿文を作成してください。

条件：
- 日本語
- 250〜500文字程度
- 2〜4行ごとに改行して読みやすくする
- 記事で分かることを具体的に示す
- 誇張しない
- 最後に記事への誘導を書く
- URLを最後にそのまま付ける
- 関連性の高いハッシュタグを3〜6個付ける
"""

    elif platform == "line":
        rules = """
LINE公式アカウント向けの新着通知文を作成してください。

条件：
- 日本語
- 100〜180文字程度
- 短く分かりやすくする
- 新着記事であることが分かる
- 記事のメリットを1つ示す
- URLを最後にそのまま付ける
- ハッシュタグは不要
- 煽り表現は禁止
"""

    else:
        raise ValueError(
            "未対応platformです："
            f"{platform}"
        )

    return f"""
あなたはAIツール情報メディア
「Alsivo」のSNS編集者です。

以下の記事をSNSで紹介します。

タイトル：
{title}

概要：
{description}

記事URL：
{url}

{rules}

投稿本文だけを出力してください。
説明や前置きは不要です。
""".strip()


def generate_copy(
    item: dict[str, Any],
) -> str:
    """OpenAI APIで投稿文を生成する。"""

    client = OpenAI(
        api_key=OPENAI_API_KEY,
    )

    prompt = build_prompt(
        item
    )

    response = (
        client.responses.create(
            model=MODEL,
            input=prompt,
        )
    )

    text = (
        response.output_text
        or ""
    ).strip()

    if not text:
        raise RuntimeError(
            "SNS投稿文を生成できませんでした。"
        )

    return text


def update_social_queue(
) -> tuple[
    list[dict[str, Any]],
    int,
]:
    """未生成のSocial Queueに投稿文を追加する。"""

    data = load_json(
        SOCIAL_QUEUE_FILE
    )

    queue = data.get(
        "queue",
        [],
    )

    if not isinstance(
        queue,
        list,
    ):
        raise RuntimeError(
            "Social Queue形式が不正です。"
        )

    generated_count = 0

    for item in queue:
        if not isinstance(
            item,
            dict,
        ):
            continue

        status = str(
            item.get(
                "status",
                "",
            )
        ).strip()

        post_text = str(
            item.get(
                "post_text",
                "",
            )
        ).strip()

        if status != "pending":
            continue

        if post_text:
            continue

        platform = str(
            item.get(
                "platform",
                "",
            )
        ).strip()

        print(
            "[Social Copy] "
            f"{platform}向け投稿文を生成中..."
        )

        text = generate_copy(
            item
        )

        item[
            "post_text"
        ] = text

        item[
            "copy_generated_at"
        ] = datetime.now().isoformat()

        item[
            "updated_at"
        ] = datetime.now().isoformat()

        generated_count += 1

    data[
        "updated_at"
    ] = datetime.now().isoformat()

    data[
        "queue"
    ] = queue

    SOCIAL_QUEUE_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        queue,
        generated_count,
    )


def print_summary(
    queue: list[dict[str, Any]],
    generated_count: int,
) -> None:
    """結果を表示する。"""

    print(
        "\n===== Atlas Social Copy Generator =====\n"
    )

    print(
        "Generated："
        f"{generated_count}"
    )

    print(
        "Queue Total："
        f"{len(queue)}"
    )

    print()

    for item in queue:

        platform = str(
            item.get(
                "platform",
                "",
            )
        )

        text = str(
            item.get(
                "post_text",
                "",
            )
        )

        print(
            "--------------------------------"
        )

        print(
            "Platform："
            f"{platform}"
        )

        print()

        print(
            text
        )

        print()


def main() -> None:
    """Social Copy Generatorを実行する。"""

    queue, generated_count = (
        update_social_queue()
    )

    print_summary(
        queue,
        generated_count,
    )


if __name__ == "__main__":
    main()