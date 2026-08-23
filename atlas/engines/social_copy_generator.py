import json
from datetime import datetime
from pathlib import Path
from typing import Any
from openai import OpenAI
from config import (
    OPENAI_API_KEY,
    MODEL,
)
from engines.affiliate_disclosure import ensure_pr_prefix


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

    common_rules = """
最重要方針：
- 単なる記事内容の要約ではなく、読者が
  「これは自分の悩みだ」
  「この記事を読めば解決できそうだ」
  と具体的にイメージできる文章にする
- 記事タイトルや概要から、読者が実際に遭遇しそうな
  困りごと・疑問・利用場面を具体化する
- その困りごとに対して、この記事を読むことで
  「何が分かるか」だけでなく
  「読後に何を判断・実行できるようになるか」
  まで伝える
- 「〜に困っていませんか？」という定型文を
  毎回機械的に使わない
- 読者の不安を過度に煽らない
- 記事に書かれていない効果や解決策を創作しない
- 「完全解決」「必ず」「絶対」などの
  過度な断定表現を使わない
"""

    if bool(item.get("is_affiliate_article", False)):
        common_rules += """
- これはアフィリエイト広告を含む記事の紹介です
- 投稿本文の先頭1行は必ず「#PR」にする
"""

    if platform == "x":
        rules = """
X向けの投稿文を作成してください。

構成：
1. 冒頭で、読者が遭遇しそうな困りごと・疑問・
   利用場面を短く具体的に示す
2. この記事で分かること、または
   できるようになることを示す
3. 記事を読む理由が自然に伝わる形でURLへつなぐ

条件：
- 日本語
- 220文字以内を目安
- 最初の1文を最も重要視する
- 短い文章でも「悩み → 解決イメージ」が伝わるようにする
- 記事タイトルをそのまま言い換えただけにしない
- 「初心者向けに解説しました」のような
  作り手目線だけの表現を避ける
- 誇張しない
- 記事内容と一致させる
- URLを最後にそのまま付ける
- ハッシュタグは0〜2個
- 「ブログを更新しました」だけの弱い文章にしない
"""

    elif platform == "instagram":
        rules = """
Instagram向けの投稿文を作成してください。

構成：
1. 読者が実際に遭遇しそうな困りごと・疑問を
   具体的な場面として提示する
2. 「どうすればいい？」という気持ちにつながる
   問題意識を自然に示す
3. この記事で分かることを具体的に示す
4. 読後にどのような判断・行動が
   できるようになるかをイメージさせる
5. 記事への自然な誘導で締める

条件：
- 日本語
- 250〜500文字程度
- 2〜4行ごとに改行して読みやすくする
- 冒頭部分だけでも読者が
  「自分に関係がある」と判断できるようにする
- 記事内容の箇条書きだけで終わらせない
- 読後のメリットを具体的にする
- 誇張しない
- 記事内容と一致させる
- 最後に記事への誘導を書く
- URLを最後にそのまま付ける
- 関連性の高いハッシュタグを3〜6個付ける
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

{common_rules}

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

        if bool(item.get("is_affiliate_article", False)):
            text = ensure_pr_prefix(text)

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
