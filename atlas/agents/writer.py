import json
from typing import Any

from openai import OpenAI

from config import MODEL, OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


ARTICLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "記事タイトル。年号はテーマ上不可欠な場合だけ含める。",
        },
        "description": {
            "type": "string",
            "description": "検索結果に表示する120文字前後の説明文。",
        },
        "category": {
            "type": "string",
            "enum": [
                "AI基礎",
                "AIツール",
                "仕事効率化",
                "AI副業",
                "プログラミング",
                "ニュース解説",
            ],
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 3,
            "maxItems": 5,
        },
        "content": {
            "type": "string",
            "description": "Markdown形式の記事本文。",
        },
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


def generate_article(topic: str) -> dict[str, Any]:
    """テーマからAlsivo向けの記事データを生成する。"""

    cleaned_topic = topic.strip()

    if not cleaned_topic:
        raise ValueError("記事テーマを入力してください。")

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの編集者です。"
            "日本語の初心者向け記事を作成してください。"
            "事実と推測を区別し、誇張や根拠のない断定を避けてください。"
            "確認できない最新情報は、古い知識で補完せず、"
            "一般的で時間に依存しない説明に限定してください。"
            "タイトルに年号を自動で付けないでください。"
            "記事冒頭のH1見出しは不要です。タイトルと本文を重複させないでください。"
            "本文は2000〜3000字を目安とし、導入、複数のH2見出し、"
            "具体例、注意点、まとめを含めてください。"
        ),
        input=(
            f"次のテーマについて、Alsivo向けの記事を作成してください。\n\n"
            f"テーマ：{cleaned_topic}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_article",
                "description": "Alsivoの記事データ",
                "schema": ARTICLE_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError("AIから記事データを取得できませんでした。")

    try:
        article = json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "AIの出力をJSONとして読み込めませんでした。"
        ) from error

    return article