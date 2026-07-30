import json
from typing import Any

from openai import OpenAI

from config import MODEL, OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "primary_keyword": {
            "type": "string",
        },
        "search_intent": {
            "type": "string",
        },
        "target_reader": {
            "type": "string",
        },
        "reader_problem": {
            "type": "string",
        },
        "article_goal": {
            "type": "string",
        },
        "suggested_title": {
            "type": "string",
        },
        "outline": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 4,
            "maxItems": 8,
        },
        "related_keywords": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 3,
            "maxItems": 8,
        },
    },
    "required": [
        "primary_keyword",
        "search_intent",
        "target_reader",
        "reader_problem",
        "article_goal",
        "suggested_title",
        "outline",
        "related_keywords",
    ],
    "additionalProperties": False,
}


def create_article_plan(topic: str) -> dict[str, Any]:

    
    cleaned_topic = topic.strip()

    if not cleaned_topic:
        raise ValueError("テーマを入力してください。")

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの編集者です。"
            "初心者に役立ち、検索意図を満たす記事企画を作成してください。"
            "過度に広いテーマの場合は、読者の悩みが明確になるように絞り込んでください。"
            "タイトルに年号を勝手に入れないでください。"
        ),
        input=f"次のテーマから記事企画を作成してください。\n\nテーマ：{cleaned_topic}",
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_article_plan",
                "schema": PLAN_SCHEMA,
                "strict": True,
            }
        },
    )


    if not response.output_text:
        raise RuntimeError("記事企画を取得できませんでした。")

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError("記事企画のJSON変換に失敗しました。") from error