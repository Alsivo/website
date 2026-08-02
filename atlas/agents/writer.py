import json
from typing import Any
from copy import deepcopy
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


client = OpenAI(api_key=OPENAI_API_KEY)


ARTICLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "slug": {"type": "string"},
        "category": {
            "type": "string",
            "enum": CATEGORIES,
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
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
            "maxItems": 10,
        },
        "content": {"type": "string"},
    },
    "required": [
        "title",
        "description",
        "slug",
        "category",
        "tags",
        "used_source_ids",
        "content",
    ],
    "additionalProperties": False,
}

def build_article_schema(
    research: dict[str, Any],
) -> dict[str, Any]:
    """実在する出典IDだけを選択できるSchemaを作る。"""

    source_ids = [
        str(source.get("id", "")).strip()
        for source in research.get("sources", [])
        if isinstance(source, dict)
        and str(source.get("id", "")).strip()
    ]

    if not source_ids:
        raise ValueError(
            "記事生成に利用できる出典IDがありません。"
        )

    schema = deepcopy(ARTICLE_SCHEMA)

    schema["properties"]["used_source_ids"]["items"] = {
        "type": "string",
        "enum": source_ids,
    }

    schema["properties"]["used_source_ids"]["maxItems"] = min(
        10,
        len(source_ids),
    )

    return schema

def generate_article(
    plan: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    """記事企画を基に、Alsivo向けの記事を生成する。"""

    plan_text = json.dumps(
        plan,
        ensure_ascii=False,
        indent=2,
    )

    research_text = json.dumps(
        research,
        ensure_ascii=False,
        indent=2,
    )
    print("[Writer] OpenAI APIへ送信...")

    article_schema = build_article_schema(
        research
    )

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
            "slugは記事内容を表す短い英語のURL文字列にしてください。"
            "slugには半角英小文字、数字、ハイフンのみを使用してください。"
            f"categoryは次の一覧から必ず1つだけ選択してください：{', '.join(CATEGORIES)}。"
            "一覧に存在しないカテゴリーを新しく作成しないでください。"
            f"タグは{MIN_TAGS}個以上{MAX_TAGS}個以下にしてください。"
            f"まず次の既存タグから適切なものを優先して選んでください：{', '.join(CORE_TAGS)}。"
            f"既存タグにない語を使う場合は、製品名や固有技術名など必要性の高いものに限定し、最大{MAX_NEW_TAGS}個までにしてください。"
            "意味がほぼ同じタグを重複して付けないでください。"
            "記事タイトルそのものをタグにしないでください。"
            "提供されたWeb調査結果を事実情報の基礎として使用してください。"
            "Web調査結果に存在しない最新情報を推測で追加しないでください。"
            "料金、機能、提供条件などは調査結果と矛盾しないようにしてください。"
            "調査結果で不確実とされた情報は、記事でも断定しないでください。"
            "Web調査結果の各出典にはS1、S2のようなIDが付いています。"
            "料金、機能、仕様、日付、プラン名などの事実を記述した直後に、"
            "根拠となる出典IDを[S1]の形式で付けてください。"
            "複数の出典が根拠なら[S1][S2]のように記載してください。"
            "存在しない出典IDを作らないでください。"
            "本文中にURLを直接書かないでください。"
            "used_source_idsには、本文で実際に使った出典IDだけを入れてください。"
            "調査結果で確認できない最新情報は記事へ追加しないでください。"
        ),
        input=(
            "以下の記事企画とWeb調査結果を基に記事を作成してください。\n\n"
            "===== 記事企画 =====\n"
            f"{plan_text}\n\n"
            "===== Web調査結果 =====\n"
            f"{research_text}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_article",
                "schema": article_schema,
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

def revise_article(
    plan: dict[str, Any],
    research: dict[str, Any],
    article: dict[str, Any],
    review: dict[str, Any],
) -> dict[str, Any]:
    """Reviewerの指摘と調査結果を基に記事全体を修正する。"""

    revision_data = {
        "article_plan": plan,
        "web_research": research,
        "current_article": article,
        "review_result": review,
    }

    print("[Writer] 修正版をOpenAI APIへ送信...")

    article_schema = build_article_schema(
        research
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの修正担当ライターです。"
            "現在の記事を、Reviewerの指摘に従って修正してください。"
            "修正箇所だけではなく、記事データ全体を返してください。"
            "Web調査結果を事実情報の根拠として使用してください。"
            "Web調査結果にない最新情報を推測で追加しないでください。"
            "料金、機能、仕様、日付、プラン名などの事実の直後には、"
            "根拠となる[S1]形式の出典IDを付けてください。"
            "存在しない出典IDを作らないでください。"
            "本文中にURLを直接書かないでください。"
            "used_source_idsには本文で実際に使用したIDだけを入れてください。"
            "記事冒頭にH1見出しを付けないでください。"
            "本文はMarkdown形式にしてください。"
            f"categoryは次の一覧から選択してください：{', '.join(CATEGORIES)}。"
            f"タグは{MIN_TAGS}個以上{MAX_TAGS}個以下にしてください。"
            f"既存タグを優先してください：{', '.join(CORE_TAGS)}。"
            f"新規タグは最大{MAX_NEW_TAGS}個までです。"
        ),
        input=json.dumps(
            revision_data,
            ensure_ascii=False,
            indent=2,
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_revised_article",
                "schema": article_schema,
                "strict": True,
            }
        },
    )

    print("[Writer] 修正版を受信！")

    if not response.output_text:
        raise RuntimeError(
            "修正版の記事データを取得できませんでした。"
        )

    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "修正版の記事データをJSONへ変換できませんでした。"
        ) from error