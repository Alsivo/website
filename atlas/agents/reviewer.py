import json
from typing import Any

from openai import OpenAI

from config import MODEL, OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


REVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "approved": {
            "type": "boolean",
        },
        "score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "summary": {
            "type": "string",
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "improvement_instructions": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "approved",
        "score",
        "summary",
        "issues",
        "improvement_instructions",
    ],
    "additionalProperties": False,
}


def review_article(
    plan: dict[str, Any],
    article: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    """記事企画と完成記事を比較し、品質を評価する。"""

    review_target = {
        "plan": plan,
        "research": research,
        "article": article,
    }

    print("[Reviewer] OpenAI APIへ送信...")

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの編集責任者です。"
            "記事企画と完成記事を比較して、公開品質を評価してください。"
            "検索意図への適合、初心者への分かりやすさ、構成、"
            "内容の具体性、重複、誇張表現、事実誤認の可能性を確認してください。"
            "確認できない最新情報や根拠のない断定がある場合は問題として指摘してください。"
            "重大な問題がなく、実用的な記事であればapprovedをtrueにしてください。"
            "軽微な表現修正だけであればapprovedをfalseにする必要はありません。"
            "記事中の料金、機能、仕様、日付などの事実が、"
            "Web調査結果によって裏付けられているか確認してください。"
            "事実の直後に[S1]などの出典IDが付いているか確認してください。"
            "本文で使われた出典IDが、research.sourcesに実在するか確認してください。"
            "根拠がない断定、存在しない出典、出典内容との矛盾があれば、"
            "approvedをfalseにしてください。"
        ),
        input=(
            "以下の記事をレビューしてください。\n\n"
            + json.dumps(
                review_target,
                ensure_ascii=False,
                indent=2,
            )
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_article_review",
                "schema": REVIEW_SCHEMA,
                "strict": True,
            }
        },
    )

    print("[Reviewer] OpenAI APIから受信！")

    if not response.output_text:
        raise RuntimeError("レビュー結果を取得できませんでした。")

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "レビュー結果のJSON変換に失敗しました。"
        ) from error