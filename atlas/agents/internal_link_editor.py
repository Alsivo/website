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


INTERNAL_LINK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "selected_links": {
            "type": "array",
            "minItems": 0,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                    },
                    "anchor": {
                        "type": "string",
                    },
                    "reason": {
                        "type": "string",
                    },
                },
                "required": [
                    "slug",
                    "anchor",
                    "reason",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": [
        "selected_links",
    ],
    "additionalProperties": False,
}


def select_internal_links(
    source_article: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """候補記事から本当に有益な内部リンクだけをAIが選ぶ。"""

    if not candidates:
        return []

    payload = {
        "source_article": {
            "slug": source_article.get(
                "slug",
                "",
            ),
            "title": source_article.get(
                "title",
                "",
            ),
            "description": source_article.get(
                "description",
                "",
            ),
            "category": source_article.get(
                "category",
                "",
            ),
            "tags": source_article.get(
                "tags",
                [],
            ),
        },
        "candidate_articles": [
            {
                "slug": item.get(
                    "slug",
                    "",
                ),
                "title": item.get(
                    "title",
                    "",
                ),
                "score": item.get(
                    "score",
                    0,
                ),
            }
            for item in candidates
        ],
    }

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAlsivoの内部リンク編集担当です。"
            "元記事を読んだ読者が次に読む価値がある記事だけを選んでください。"

            "候補記事は最大3件選択してください。"
            "適切な候補がなければ0件で構いません。"

            "単にAI、生成AI、料金比較などの"
            "広いカテゴリが同じという理由だけで選ばないでください。"

            "以下のどれかを満たす場合に優先してください。"
            "1. 同じサービスをさらに詳しく説明する記事"
            "2. 同じ用途のツール比較記事"
            "3. 比較記事と個別サービス記事の関係"
            "4. 読者が自然に次に疑問を持つテーマ"
            "5. 元記事の意思決定を補完する記事"

            "読者にとって文脈が飛ぶ記事は選択しないでください。"

            "anchorにはSEOキーワードを詰め込まず、"
            "クリック先の内容が自然に分かる日本語を使ってください。"

            "slugは候補に存在するものだけを使用してください。"
            "新しいslugを作らないでください。"
        ),
        input=json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_internal_links",
                "schema": INTERNAL_LINK_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "内部リンク判定を取得できませんでした。"
        )

    result = json.loads(
        response.output_text
    )

    allowed_slugs = {
        str(
            candidate.get(
                "slug",
                "",
            )
        )
        for candidate in candidates
    }

    selected_links = []

    for item in result[
        "selected_links"
    ]:
        slug = str(
            item.get(
                "slug",
                "",
            )
        ).strip()

        if slug not in allowed_slugs:
            continue

        selected_links.append(
            {
                "slug": slug,
                "anchor": str(
                    item.get(
                        "anchor",
                        "",
                    )
                ).strip(),
                "reason": str(
                    item.get(
                        "reason",
                        "",
                    )
                ).strip(),
            }
        )

    return selected_links