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


STRENGTHEN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "section_title": {
            "type": "string",
        },
        "section_content": {
            "type": "string",
        },
        "reason": {
            "type": "string",
        },
        "target_queries": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 10,
        },
        "change_summary": {
            "type": "string",
        },
    },
    "required": [
        "section_title",
        "section_content",
        "reason",
        "target_queries",
        "change_summary",
    ],
    "additionalProperties": False,
}


def strengthen_article(
    article: dict[str, Any],
    search_queries: list[dict[str, Any]],
    reason: str = "",
) -> dict[str, Any]:
    """
    既存記事を全面リライトせず、
    SEO上不足している内容を補う
    追加セクションを生成する。
    """

    payload = {
        "article": {
            "slug":
                article.get(
                    "slug",
                    "",
                ),
            "title":
                article.get(
                    "title",
                    "",
                ),
            "description":
                article.get(
                    "description",
                    "",
                ),
            "content":
                article.get(
                    "content",
                    "",
                ),
        },
        "search_console_queries":
            search_queries,
        "optimization_reason":
            reason,
    }

    print(
        "[Content Strengthener] "
        "追加セクションを検討中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(

            "あなたはAIメディアAlsivoの"
            "SEOコンテンツ改善担当です。"

            "既存記事を全面的に書き直してはいけません。"
            "既存記事の検索意図と構成を維持したまま、"
            "不足している情報を補う"
            "追加セクションを1つだけ作成してください。"

            "Search Console検索語がある場合は、"
            "表示回数や掲載順位を参考に、"
            "既存記事で十分回答できていない"
            "検索意図を優先してください。"

            "既存本文ですでに十分説明されている内容を"
            "重複して追加しないでください。"

            "section_titleはH2見出しとして使える"
            "自然な日本語にしてください。"
            "section_titleには##を付けないでください。"

            "section_contentには見出しそのものを"
            "含めないでください。"

            "section_contentはMarkdown形式で、"
            "そのまま既存記事へ挿入できる"
            "本文だけを返してください。"

            "新しい料金、仕様、日付、統計など、"
            "既存記事や入力データから確認できない事実を"
            "勝手に作らないでください。"

            "SEO目的だけの不自然なキーワード反復や"
            "検索エンジン向けの文章は禁止です。"

            "読者にとって実際に役立つ情報追加を"
            "最優先してください。"

            "既存記事のタイトル、description、slug、"
            "既存本文は変更してはいけません。"

            "target_queriesには、今回の追加内容で"
            "対応するSearch Console検索語だけを"
            "入れてください。"

            "change_summaryには何を追加したのかを"
            "簡潔に記述してください。"
        ),
        input=json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        text={
            "format": {
                "type":
                    "json_schema",
                "name":
                    "alsivo_content_strengthening",
                "schema":
                    STRENGTHEN_SCHEMA,
                "strict":
                    True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "コンテンツ強化案を"
            "取得できませんでした。"
        )

    try:
        result = json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "コンテンツ強化案のJSON変換に"
            "失敗しました。"
        ) from error

    return result