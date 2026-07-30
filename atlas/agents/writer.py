import json
from typing import Any

from openai import OpenAI

from config import MODEL, OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


ARTICLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "category": {"type": "string"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5,
        },
        "content": {"type": "string"},
    },
    "required": [
        "title",
        "description",
        "category",
        "tags",
        "content",
    ],
    "additionalProperties": False,
}


def generate_article(plan: dict[str, Any]) -> dict[str, Any]:
    """記事企画を基に、Alsivo向けの記事を生成する。"""

    plan_text = json.dumps(
        plan,
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
        ),
        input=(
            "以下の記事企画を基に記事を作成してください。\n\n"
            f"{plan_text}"
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