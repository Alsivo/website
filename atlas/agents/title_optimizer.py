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


TITLE_OPTIMIZATION_SCHEMA: dict[
    str,
    Any,
] = {
    "type": "object",
    "properties": {
        "new_title": {
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
        "new_title",
        "reason",
        "target_queries",
        "change_summary",
    ],
    "additionalProperties": False,
}


def optimize_title(
    article: dict[str, Any],
    search_queries: list[dict[str, Any]],
) -> dict[str, Any]:
    """既存記事の検索実績からタイトルを最適化する。"""

    current_title = str(
        article.get(
            "title",
            "",
        )
    ).strip()

    slug = str(
        article.get(
            "slug",
            "",
        )
    ).strip()

    if not current_title:
        raise ValueError(
            "現在のタイトルがありません。"
        )

    context = {
        "slug":
            slug,
        "current_title":
            current_title,
        "description":
            str(
                article.get(
                    "description",
                    "",
                )
            ).strip(),
        "search_queries":
            search_queries,
    }

    context_text = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
    )

    print(
        "[Title Optimizer] "
        "タイトル改善案を作成中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの"
            "SEO編集者です。"

            "既存記事の本文は変更せず、"
            "Search Consoleの実検索語をもとに"
            "記事タイトルだけを改善してください。"

            "目的は検索意図との一致度と"
            "検索結果上のCTRを改善することです。"

            "現在のタイトルの意味や記事テーマを"
            "大きく変えてはいけません。"

            "記事本文で扱っていない内容を"
            "タイトルへ追加してはいけません。"

            "検索語に含まれる重要な表現は、"
            "記事内容と一致する場合のみ"
            "自然に取り入れてください。"

            "煽り表現、誇張表現、"
            "根拠のないNo.1表現は使わないでください。"

            "年号は、入力情報に明確な必要性が"
            "ない限り追加しないでください。"

            "現在のタイトルが十分適切な場合は、"
            "無理に大きく変更せず、"
            "小さな改善に留めてください。"

            "new_titleにはタイトル文字列だけを"
            "入れてください。"
        ),
        input=(
            "以下の記事とSearch Console実績から"
            "タイトル改善案を1つ作成してください。\n\n"
            f"{context_text}"
        ),
        text={
            "format": {
                "type":
                    "json_schema",
                "name":
                    "alsivo_title_optimization",
                "schema":
                    TITLE_OPTIMIZATION_SCHEMA,
                "strict":
                    True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "タイトル改善案を取得できませんでした。"
        )

    try:
        result = json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "タイトル改善結果のJSON変換に"
            "失敗しました。"
        ) from error

    new_title = str(
        result.get(
            "new_title",
            "",
        )
    ).strip()

    if not new_title:
        raise RuntimeError(
            "new_titleが空です。"
        )

    return result