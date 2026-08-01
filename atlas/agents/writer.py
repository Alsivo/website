import json
from typing import Any

from openai import OpenAI

from config import (
    CATEGORIES,
    CORE_TAGS,
    MAX_NEW_TAGS,
    MAX_TAGS,
    MIN_TAGS,
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(api_key=OPENAI_API_KEY)


ARTICLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "slug": {"type": "string"},
        "category": {
            "type": "string",
            "enum": CATEGORIES,
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
            },
            "minItems": MIN_TAGS,
            "maxItems": MAX_TAGS,
        },
        "content": {"type": "string"},
    },
    "required": [
        "title",
        "description",
        "slug",
        "category",
        "tags",
        "content",
    ],
    "additionalProperties": False,
}


def generate_article(
    plan: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    """記事企画を基に、Alsivo向けの記事を生成する。"""

    plan_text = json.dumps(
        plan,
        ensure_ascii=False,
        indent=2,
    )

    research_text = json.dumps(
        research,
        ensure_ascii=False,
        indent=2,
    )
    print("[Writer] OpenAI APIへ送信...")

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoのライターです。"
            "渡された記事企画に忠実に、日本語の記事を作成してください。"
            "初心者にも理解できる言葉を使ってください。"
            "タイトルに年号を勝手に入れないでください。"
            "事実と推測を区別し、根拠のない断定を避けてください。"
            "記事冒頭にH1見出しは付けないでください。"
            "本文には導入、複数のH2見出し、具体例、注意点、まとめを含めてください。"
            "本文はMarkdown形式で作成してください。"
            "slugは記事内容を表す短い英語のURL文字列にしてください。"
            "slugには半角英小文字、数字、ハイフンのみを使用してください。"
            f"categoryは次の一覧から必ず1つだけ選択してください：{', '.join(CATEGORIES)}。"
            "一覧に存在しないカテゴリーを新しく作成しないでください。"
            f"タグは{MIN_TAGS}個以上{MAX_TAGS}個以下にしてください。"
            f"まず次の既存タグから適切なものを優先して選んでください：{', '.join(CORE_TAGS)}。"
            f"既存タグにない語を使う場合は、製品名や固有技術名など必要性の高いものに限定し、最大{MAX_NEW_TAGS}個までにしてください。"
            "意味がほぼ同じタグを重複して付けないでください。"
            "記事タイトルそのものをタグにしないでください。"
            "提供されたWeb調査結果を事実情報の基礎として使用してください。"
            "Web調査結果に存在しない最新情報を推測で追加しないでください。"
            "料金、機能、提供条件などは調査結果と矛盾しないようにしてください。"
            "調査結果で不確実とされた情報は、記事でも断定しないでください。"
        ),
        input=(
            "以下の記事企画とWeb調査結果を基に記事を作成してください。\n\n"
            "===== 記事企画 =====\n"
            f"{plan_text}\n\n"
            "===== Web調査結果 =====\n"
            f"{research_text}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_article",
                "schema": ARTICLE_SCHEMA,
                "strict": True,
            }
        },
    )

    print("[Writer] OpenAI APIから受信！")

    if not response.output_text:
        raise RuntimeError("記事データを取得できませんでした。")

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError("記事データのJSON変換に失敗しました。") from error