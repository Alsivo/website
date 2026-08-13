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
                "additionalProperties": False,
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
        "comparison_table": {
            "anyOf": [
                {
                    "type": "null",
                },
                {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                        },
                        "columns": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 8,
                            "items": {
                                "type": "string",
                            },
                        },
                        "rows": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 12,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                    },
                                    "values": {
                                        "type": "array",
                                        "minItems": 2,
                                        "maxItems": 8,
                                        "items": {
                                            "type": "string",
                                        },
                                    },
                                },
                                "required": [
                                    "label",
                                    "values",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": [
                        "title",
                        "columns",
                        "rows",
                    ],
                    "additionalProperties": False,
                },
            ],
        },
        "cta_plan": {
            "type": "object",
            "properties": {
                "primary_service": {
                    "type": [
                        "string",
                        "null",
                    ],
                },
                "placement": {
                    "type": "string",
                    "enum": [
                        "after_toc",
                        "after_comparison",
                        "before_faq",
                    ],
                },
                "cta_label": {
                    "type": [
                        "string",
                        "null",
                    ],
                },
                "reason": {
                    "type": "string",
                },
            },
            "required": [
                "primary_service",
                "placement",
                "cta_label",
                "reason",
            ],
            "additionalProperties": False,
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
        "comparison_table",
        "cta_plan",
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

    # 実際にResearcherが取得した
    # 出典IDだけを使用可能にする
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

    # リンク台帳に登録されている
    # サービスだけを使用可能にする
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
    """
    既存記事をSearch Consoleと最新調査に基づき、
    Alsivoの現行記事仕様へリライトする。
    """

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

    affiliate_tool_names = (
        get_affiliate_tool_names()
    )

    affiliate_tool_text = ", ".join(
        affiliate_tool_names
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

            "既存記事の良い部分は可能な限り活かし、"
            "不要な全面書き換えは避けてください。"
            "ただし、古い情報、読みにくい構造、"
            "現在のAlsivo記事仕様に合わない部分は"
            "積極的に改善してください。"

            "Search Consoleの実績と最新Web調査結果に基づき、"
            "検索意図への適合、情報鮮度、読みやすさ、"
            "CTR、記事構造を改善してください。"

            "既存記事を単純に長文化しないでください。"
            "情報量を増やすことより、"
            "読者が判断しやすい構成を優先してください。"

            "Search Consoleで表示されている検索語は、"
            "記事内容と関連するものだけを"
            "不自然にならない範囲で反映してください。"

            "掲載順位4〜20位程度の検索語について、"
            "検索意図に合う場合は"
            "関連見出しや説明を強化してください。"

            "表示回数が多くCTRが低い場合は、"
            "内容との整合性を維持した上で"
            "titleとdescriptionの改善を検討してください。"

            "既存slugは絶対に変更しないでください。"
            "URL変更はSEO上のリスクがあるため禁止です。"

            "記事タイトルに年号を勝手に追加しないでください。"

            "事実と推測を明確に区別し、"
            "根拠のない断定や過度な推奨を避けてください。"

            "記事冒頭にH1見出しは付けないでください。"
            "本文はMarkdown形式にしてください。"

            "本文には、必要に応じて導入、"
            "複数のH2、具体例、注意点、まとめを含めてください。"

            "本文内の情報は、内容に応じて"
            "次の3種類のMarkdown構造を使い分けてください。"

            "1つ目は、短い要点を並べる箇条書きです。"
            "「特徴」「向いている人」「料金」「注意点」など、"
            "1項目の説明が1〜2文程度で完結する場合は、"
            "『- **項目名：** 説明文』の形式にしてください。"
            "項目名とコロンだけを太字にし、"
            "説明文全体を太字にしないでください。"

            "2つ目は、説明量の多い詳細小項目です。"
            "1つの項目について複数文の説明や"
            "複数の箇条書きが続く場合は、"
            "その項目をH3見出しとして独立させてください。"
            "『### 項目名』の後に空行を入れ、"
            "通常の段落や箇条書きで説明してください。"

            "3つ目は、操作手順や判断フローです。"
            "順序そのものに意味がある場合だけ、"
            "番号付きリストを使用してください。"
            "『1. **入口：** 説明』のように、"
            "項目タイトルだけを太字にしてください。"

            "順序に意味のない特徴・注意点・選択肢を、"
            "番号付きリストにしないでください。"

            "H2直下の内容をすべて同じ見た目にせず、"
            "H2、H3、短い要点一覧、"
            "通常段落、手順を適切に使い分けてください。"

            "Markdownの見出し階層は"
            "次のルールを厳守してください。"

            "H2（##）は記事の主要セクションだけに"
            "使用してください。"

            "H2内で、その項目について"
            "複数の説明文・箇条書き・手順が続く場合は、"
            "H3（###）として独立させてください。"

            "H3にすべき項目を、"
            "長い箇条書き1項目として"
            "代用しないでください。"

            "一方、1〜2文で説明が完結する小項目は、"
            "『- **項目名：** 説明文』"
            "の形式を優先してください。"

            "見出しの直前と直後には"
            "必ず空行を入れてください。"

            "Markdown見出しを、"
            "文章・リスト・MDXタグと"
            "同じ行に書かないでください。"

            "特に『</AffiliateLink>## まとめ』のように、"
            "MDXタグの直後へ"
            "見出しを連結しないでください。"

            "Markdown装飾記号を"
            "不要にエスケープしないでください。"

            "太字は必ず"
            "『**項目名**』と記述してください。"

            "『\\*\\*項目名\\*\\*』のように、"
            "Markdown表示用のアスタリスクを"
            "エスケープしないでください。"

            "提供された最新Web調査結果を"
            "事実情報の基礎として使用してください。"

            "Web調査結果に存在しない最新情報を"
            "推測で追加しないでください。"

            "既存記事と最新Web調査結果が矛盾する場合は、"
            "最新Web調査結果を優先してください。"

            "料金、プラン、機能、利用上限、"
            "仕様、日付、提供条件など、"
            "変更されやすい情報は特に慎重に更新してください。"

            "調査結果で確認できない情報は、"
            "断定せず「要確認」「公式サイトで確認」"
            "など適切な表現にしてください。"

            "出典を選択する際は、"
            "日本語の公式情報・一次情報を"
            "最優先してください。"

            "日本語の適切な出典がない場合は、"
            "英語の公式情報・一次情報を使用してください。"

            "日本語または英語以外の出典は、"
            "原則として使用しないでください。"

            "同じ内容の日本語または英語の"
            "公式出典が存在する場合は、"
            "中国語、韓国語、アラビア語などの"
            "他言語版の出典IDを"
            "used_source_idsへ含めないでください。"

            "Web調査結果の各出典には"
            "S1、S2のようなIDが付いています。"

            "料金、機能、仕様、日付、"
            "プラン名、提供条件などの"
            "事実を記述した直後に、"
            "根拠となる出典IDを"
            "[S1]形式で付けてください。"

            "複数の出典が根拠の場合は、"
            "[S1][S2]のように記載してください。"

            "この[S1]形式はPublisherが"
            "公開時に自動的に削除し、"
            "記事末尾の参考情報へ変換します。"

            "したがって、本文中にURLを"
            "直接書かないでください。"

            "存在しない出典IDを"
            "作らないでください。"

            "used_source_idsには、"
            "本文、FAQ、比較表で"
            "実際に利用した出典IDだけを"
            "入れてください。"

            "既存記事に古い参考情報セクションが"
            "含まれている場合、"
            "content本文には"
            "『## 参考情報』を残さないでください。"

            "参考情報はPublisherが"
            "最新のused_source_idsから"
            "記事末尾へ自動生成します。"

            "既存記事に"
            "『本文中に各出典IDを明記』など、"
            "現在の公開仕様と矛盾する説明がある場合は"
            "削除または適切に修正してください。"

            f"categoryは次の一覧から"
            f"必ず1つ選択してください："
            f"{', '.join(CATEGORIES)}。"

            "一覧に存在しないカテゴリーを"
            "新しく作成しないでください。"

            f"タグは{MIN_TAGS}個以上"
            f"{MAX_TAGS}個以下にしてください。"

            "既存記事の適切なタグは"
            "可能な限り維持してください。"

            f"まず次の既存タグから"
            f"適切なものを優先してください："
            f"{', '.join(CORE_TAGS)}。"

            f"既存タグにない語を追加する場合は、"
            f"製品名や固有技術名など"
            f"必要性の高いものに限定し、"
            f"最大{MAX_NEW_TAGS}個までにしてください。"

            "意味がほぼ同じタグを"
            "重複して付けないでください。"

            "記事タイトルそのものを"
            "タグにしないでください。"

            "FAQは3件以上5件以下にしてください。"

            "FAQは記事本文を読んだ初心者が"
            "実際に疑問に感じやすい内容にしてください。"

            "FAQはcontent本文へ"
            "重複して書かないでください。"

            "FAQ回答に料金、機能、仕様、"
            "日付、プラン名などの"
            "事実を含める場合は、"
            "回答内にも根拠となる"
            "[S1]形式の出典IDを付けてください。"

            "recommended_toolsには、"
            "記事内で実際に紹介または比較した"
            "サービスのうち、"
            "読者が公式ページを確認する"
            "価値が高いものを最大5件入れてください。"

            "CTAへ登録可能なサービス一覧に"
            "存在する正式名称だけを使用してください。"

            f"CTAへ登録可能なサービス一覧："
            f"{affiliate_tool_text}。"

            "記事内で扱っていないサービスは"
            "recommended_toolsへ追加しないでください。"

            "適切なサービスがなければ"
            "recommended_toolsは"
            "空の配列にしてください。"

            "recommended_toolsを埋めるためだけに、"
            "本文へ不自然なサービス紹介を"
            "追加しないでください。"

            "料金比較、プラン比較、"
            "複数サービス比較など、"
            "表形式にすると読者が"
            "判断しやすい記事では"
            "comparison_tableを作成してください。"

            "比較表が不要な記事では"
            "comparison_tableをnullにしてください。"

            "既存記事に有用な比較表がある場合は、"
            "最新情報と整合させた上で"
            "comparison_tableとして"
            "可能な限り維持してください。"

            "comparison_tableのcolumnsには"
            "比較対象名を入れてください。"

            "rowsのlabelには比較項目、"
            "valuesには各比較対象の値を"
            "入れてください。"

            "columnsの件数と各rowのvaluesの件数は"
            "必ず一致させてください。"

            "比較表の料金、機能、仕様、"
            "利用上限などの事実にも、"
            "根拠となる[S1]形式の"
            "出典IDを値の直後に付けてください。"

            "comparison_tableの内容を"
            "content本文へMarkdown表として"
            "重複して書かないでください。"

            "cta_planでは、"
            "この記事の読者が次に取るべき行動を"
            "自然に支援するCTA設計をしてください。"

            "primary_serviceを設定する場合は、"
            "recommended_toolsに含まれる"
            "サービスから1つだけ選択してください。"

            "特定サービスを推奨する根拠が"
            "十分でない場合は、"
            "primary_serviceをnullにしてください。"

            "CTAの配置はAlsivo共通仕様として固定します。"
            "placementは必ずafter_tocにしてください。"
            "primary_serviceが設定されている場合、"
            "PublisherがPrimary CTAを"
            "目次直後と記事後半の2か所へ自動配置します。"
            "Secondary CTAは記事後半だけに配置されます。"
            "after_comparisonまたはbefore_faqを"
            "placementとして選択しないでください。"

            "cta_labelはリンク先で"
            "何を確認できるか分かる"
            "具体的な文言にしてください。"

            "『今すぐ申し込む』"
            "『絶対おすすめ』などの"
            "過度な販促表現は"
            "使用しないでください。"

            "reasonには、そのサービスと"
            "配置を選んだ理由を"
            "簡潔に記述してください。"

            "rewrite_summaryには、"
            "今回のリライトで"
            "何を改善したかを"
            "簡潔に記述してください。"

            "rewrite_summaryは記事本文へ"
            "含めないでください。"
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

    cta_plan = result.get(
        "cta_plan"
    )

    if isinstance(
        cta_plan,
        dict,
    ):
        cta_plan[
            "placement"
        ] = "after_toc"

    return result