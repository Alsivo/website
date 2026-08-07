import json
from copy import deepcopy
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
from engines.affiliate_registry import (
    get_affiliate_tool_names,
)


client = OpenAI(
    api_key=OPENAI_API_KEY
)


REWRITE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
        },
        "description": {
            "type": "string",
        },
        "slug": {
            "type": "string",
        },
        "category": {
            "type": "string",
            "enum": CATEGORIES,
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": MIN_TAGS,
            "maxItems": MAX_TAGS,
        },
        "used_source_ids": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 1,
            "maxItems": 15,
        },
        "content": {
            "type": "string",
        },
        "faq": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                    },
                    "answer": {
                        "type": "string",
                    },
                },
                "required": [
                    "question",
                    "answer",
                ],
                "additionalProperties":
                    False,
            },
        },
        "recommended_tools": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 5,
        },
        "rewrite_summary": {
            "type": "string",
        },
    },
    "required": [
        "title",
        "description",
        "slug",
        "category",
        "tags",
        "used_source_ids",
        "content",
        "faq",
        "recommended_tools",
        "rewrite_summary",
    ],
    "additionalProperties": False,
}


def build_rewrite_schema(
    research: dict[str, Any],
) -> dict[str, Any]:
    """実在する出典とサービスだけ使えるSchemaを作る。"""

    source_ids = [
        str(
            source.get(
                "id",
                "",
            )
        ).strip()
        for source in research.get(
            "sources",
            [],
        )
        if isinstance(source, dict)
        and str(
            source.get(
                "id",
                "",
            )
        ).strip()
    ]

    if not source_ids:
        raise ValueError(
            "リライトに利用できる"
            "出典IDがありません。"
        )

    affiliate_tools = (
        get_affiliate_tool_names()
    )

    schema = deepcopy(
        REWRITE_SCHEMA
    )

    schema["properties"][
        "used_source_ids"
    ]["items"] = {
        "type": "string",
        "enum": source_ids,
    }

    schema["properties"][
        "used_source_ids"
    ]["maxItems"] = min(
        15,
        len(source_ids),
    )

    schema["properties"][
        "recommended_tools"
    ]["items"] = {
        "type": "string",
        "enum": affiliate_tools,
    }

    schema["properties"][
        "recommended_tools"
    ]["maxItems"] = min(
        5,
        len(affiliate_tools),
    )

    return schema


def rewrite_article(
    existing_article: dict[str, Any],
    editorial_decision: dict[str, Any],
    search_queries: list[dict[str, Any]],
    research: dict[str, Any],
) -> dict[str, Any]:
    """既存記事をSearch Consoleと最新調査に基づきリライトする。"""

    payload = {
        "existing_article":
            existing_article,
        "editorial_decision":
            editorial_decision,
        "search_console_queries":
            search_queries,
        "latest_research":
            research,
    }

    schema = build_rewrite_schema(
        research
    )

    print(
        "[Rewriter] "
        "既存記事をリライト中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの"
            "リライト専門ライターです。"

            "既存記事の良い部分を活かしつつ、"
            "Search Consoleの実績と最新調査結果に基づき"
            "記事全体を改善してください。"

            "既存記事を単純に長文化しないでください。"
            "検索意図への適合、情報鮮度、"
            "読みやすさ、CTR改善、"
            "内部構造の整理を重視してください。"

            "Search Consoleで表示されている検索語を"
            "不自然にならない範囲で本文へ反映してください。"

            "掲載順位4〜20位程度の検索語は、"
            "関連見出しや説明を強化してください。"

            "表示回数が多くCTRが低い場合は、"
            "タイトルとdescription改善を検討してください。"

            "既存slugは変更しないでください。"
            "URL変更はSEO上のリスクがあるため禁止です。"

            "記事冒頭にH1は書かないでください。"
            "本文はMarkdown形式にしてください。"

            "Web調査結果に存在しない最新情報を"
            "推測で追加しないでください。"

            "料金、機能、仕様、日付などの事実には"
            "[S1]形式の根拠を付けてください。"

            "存在しない出典IDを作らないでください。"

            "used_source_idsには本文またはFAQで"
            "実際に使用した出典IDだけを入れてください。"

            "FAQは3〜5件にしてください。"

            "recommended_toolsには記事で実際に扱った"
            "登録済みサービスだけを入れてください。"

            f"categoryは次から選択してください："
            f"{', '.join(CATEGORIES)}。"

            f"タグは{MIN_TAGS}〜{MAX_TAGS}個。"
            f"既存タグを優先してください："
            f"{', '.join(CORE_TAGS)}。"

            f"新規タグは最大{MAX_NEW_TAGS}個です。"

            "rewrite_summaryには、"
            "今回何を改善したかを簡潔に記述してください。"
        ),
        input=json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        text={
            "format": {
                "type": "json_schema",
                "name":
                    "alsivo_rewritten_article",
                "schema":
                    schema,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "リライト結果を取得できませんでした。"
        )

    try:
        result = json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "リライト結果のJSON変換に"
            "失敗しました。"
        ) from error

    original_slug = str(
        existing_article[
            "slug"
        ]
    ).strip()

    result_slug = str(
        result.get(
            "slug",
            "",
        )
    ).strip()

    if result_slug != original_slug:
        raise ValueError(
            "リライト時にslugが"
            "変更されました。"
            f"元：{original_slug} / "
            f"生成：{result_slug}"
        )

    return result