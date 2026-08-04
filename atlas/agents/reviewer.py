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
            "FAQが記事内容と整合しているか確認してください。"
            "FAQの質問が記事テーマと具体的に関連しているか確認してください。"
            "FAQ回答に料金、機能、仕様、日付、プラン名などの事実がある場合は、"
            "有効な[S1]形式の出典IDが付いているか確認してください。"
            "本文とFAQで内容が不必要に重複している場合は指摘してください。"
            "FAQが3件以上5件以下であることも確認してください。"
            "recommended_toolsに、記事内で実際に紹介していない"
            "サービスが含まれていないか確認してください。"
            "recommended_toolsは記事の検索意図と一致するものだけにしてください。"
            "記事内で扱っている場合でも、読者が公式ページを確認する価値が"
            "低いサービスは無理に選ばないでください。"
            "根拠のないランキング、過度な推奨、誤解を招く購入誘導が"
            "含まれている場合は修正を指示してください。"
            "登録済みサービスが記事内に存在しない場合は、"
            "recommended_toolsを空配列にするよう指示してください。"
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