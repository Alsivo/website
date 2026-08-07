import json
from typing import Any

from openai import OpenAI

from config import (
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY
)


EDITORIAL_DECISION_SCHEMA: dict[
    str,
    Any,
] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "new_article",
                "rewrite_article",
                "wait",
            ],
        },
        "priority_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "reason": {
            "type": "string",
        },
        "target_keyword": {
            "type": "string",
        },
        "target_slug": {
            "type": "string",
        },
        "target_title": {
            "type": "string",
        },
        "search_intent": {
            "type": "string",
        },
        "recommended_focus": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 8,
        },
        "target_queries": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 10,
        },
        "monetization_opportunity": {
            "type": "string",
        },
        "expected_effect": {
            "type": "string",
        },
    },
    "required": [
        "action",
        "priority_score",
        "reason",
        "target_keyword",
        "target_slug",
        "target_title",
        "search_intent",
        "recommended_focus",
        "target_queries",
        "monetization_opportunity",
        "expected_effect",
    ],
    "additionalProperties": False,
}


def make_editorial_decision(
    editorial_context: dict[str, Any],
) -> dict[str, Any]:
    """サイト状況から次に行う施策をAIが判断する。"""

    context_text = json.dumps(
        editorial_context,
        ensure_ascii=False,
        indent=2,
    )

    print(
        "[Editor] "
        "次の編集施策を判断中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの編集長です。"
            "目的はPVを増やすだけではなく、"
            "検索ユーザーへ価値を提供しながら"
            "中長期的な検索流入と収益性を高めることです。"

            "渡されたSearch Consoleデータ、"
            "既存記事、未処理キーワード、"
            "アフィリエイト案件を総合して、"
            "次に行うべき施策を1つだけ選んでください。"

            "actionはnew_article、rewrite_article、waitの"
            "いずれかです。"

            "Search Consoleデータが少ない場合は、"
            "無理にリライトを選ばず、"
            "検索意図が明確な未処理キーワードから"
            "新規記事を優先してください。"

            "既存記事が掲載順位4〜20位程度で、"
            "一定の表示回数がある場合は、"
            "リライトによって上位表示できる可能性を"
            "重視してください。"

            "表示回数が多いのにCTRが低い場合は、"
            "タイトルやdescription改善の価値を"
            "考慮してください。"

            "アフィリエイト案件があることだけを理由に、"
            "検索意図と無関係な記事を選ばないでください。"

            "収益性は判断要素の1つですが、"
            "読者価値と検索意図を優先してください。"

            "新規記事の場合はtarget_keywordへ"
            "未処理キーワードを1つ入れてください。"
            "target_slugは空文字にしてください。"

            "リライトの場合はtarget_slugへ"
            "既存記事のslugを入れてください。"
            "target_keywordは主に強化すべき検索語を"
            "入れてください。"

            "waitは、未処理キーワードもなく、"
            "改善に値するSearch Consoleデータも"
            "ない場合だけ選択してください。"

            "根拠のない検索ボリュームや売上予測を"
            "作らないでください。"
        ),
        input=(
            "以下が現在のAlsivoの状況です。\n\n"
            f"{context_text}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name":
                    "alsivo_editorial_decision",
                "schema":
                    EDITORIAL_DECISION_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "編集判断を取得できませんでした。"
        )

    try:
        return json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "編集判断のJSON変換に"
            "失敗しました。"
        ) from error