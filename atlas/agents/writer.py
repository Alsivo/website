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
from engines.affiliate_registry import (
    get_affiliate_tool_names,
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
            "maxItems": 20,
        },
        "content": {"type": "string"},
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
            ]
        },
        "cta_plan": {
            "type": "object",
            "properties": {
                "primary_service": {
                    "type": ["string", "null"],
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
                    "type": ["string", "null"],
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
        "faq": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string"
                    },
                    "answer": {
                        "type": "string"
                    }
                },
                "required": [
                    "question",
                    "answer"
                ],
                "additionalProperties": False
            }
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
        "recommended_tools",
        "comparison_table",
        "cta_plan",
        "faq",
    ],
    "additionalProperties": False,
}

def build_article_schema(
    research: dict[str, Any],
) -> dict[str, Any]:
    """記事生成時に使用する動的Schemaを作る。"""

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

    affiliate_tool_names = (
        get_affiliate_tool_names()
    )

    # 最初にSchemaのコピーを作る
    schema = deepcopy(ARTICLE_SCHEMA)

    # 実在する出典IDだけを選択可能にする
    schema["properties"][
        "used_source_ids"
    ]["items"] = {
        "type": "string",
        "enum": source_ids,
    }

    schema["properties"][
        "used_source_ids"
    ]["maxItems"] = min(
        10,
        len(source_ids),
    )

    # リンク台帳に登録されたサービスだけを
    # recommended_toolsで選択可能にする
    schema["properties"][
        "recommended_tools"
    ]["items"] = {
        "type": "string",
        "enum": affiliate_tool_names,
    }

    schema["properties"][
        "recommended_tools"
    ]["maxItems"] = min(
        5,
        len(affiliate_tool_names),
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

    affiliate_tool_names = (
        get_affiliate_tool_names()
    )

    affiliate_tool_text = ", ".join(
        affiliate_tool_names
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
            "本文内の情報は、内容に応じて次の3種類のMarkdown構造を使い分けてください。"
            "1つ目は、短い要点を並べる箇条書きです。"
            "「この記事でわかること」「特徴」「向いている人」「料金」「注意点」など、"
            "1項目の説明が1〜2文程度で完結する場合は、"
            "『- **項目名：** 説明文』の形式にしてください。"
            "項目名とコロンだけを太字にし、説明文は通常文字にしてください。"
            "例：『- **日本語対応：** UIや出力の日本語品質を確認します。』"
            "説明文全体を太字にしないでください。"
            "2つ目は、1項目ごとの説明が長い小項目です。"
            "複数文の説明や詳細な解説が続く場合は、"
            "項目タイトルだけを独立したMarkdown太字行にしてください。"
            "その後に空行を入れ、説明文を通常文字の別段落として記述してください。"
            "例：『**出典の明確さ**』の後に空行を入れ、説明文を記述してください。"
            "この場合は順序に意味がなければ番号を付けないでください。"
            "3つ目は操作手順や判断フローです。"
            "順序そのものに意味がある場合だけ番号付きリストを使用してください。"
            "『1. **入口：**』のように番号と項目タイトルを書き、"
            "説明が短い場合は同じ項目内、長い場合は次の行へ分けてください。"
            "項目タイトルだけを太字にし、説明文全体を太字にしないでください。"
            "H2直下の内容をすべて同じ見た目にせず、"
            "大見出し、短い要点一覧、詳細小項目、手順の階層が"
            "視覚的に区別できるMarkdown構造にしてください。"
            "Markdown装飾記号を不要にエスケープしないでください。"
            "太字には必ず『**項目名**』を使用し、『\\*\\*項目名\\*\\*』とは記述しないでください。"
            "Markdownとして表示させるアスタリスクの直前にバックスラッシュを付けないでください。"
            "slugは記事内容を表す短い英語のURL文字列にしてください。"
            "slugには半角英小文字、数字、ハイフンのみを使用してください。"
            "本文のMarkdown階層は、次のルールを厳守してください。"
            "H2（##）は記事の主要セクションだけに使用してください。"
            "H2内で、その項目について複数の説明文・箇条書き・手順が続く場合は、H3（###）として独立させてください。"
            "H3にすべき項目を、箇条書きの1項目として代用しないでください。"
            "例えば「ウェブ/アプリ（個人向け）」「API（Console）」「共通プールに注意」のように、その後に複数の説明が続く項目は、"
            "『### ウェブ/アプリ（個人向け）』のようなH3見出しにしてください。"
            "一方、1〜2文だけで説明が完結する小項目は『**項目名：** 説明文』の形式にしてください。"
            "箇条書きは、手順・条件・特徴・選択肢などを列挙するときだけ使用してください。"
            "見出しの直前と直後には必ず空行を入れてください。"
            "『## まとめ』『### 見出し』などのMarkdown見出しを、文章・リスト・MDXタグと同じ行に書かないでください。"
            "特に『</AffiliateLink>## まとめ』のように、MDXタグの直後へ見出しを連結しないでください。"
            f"categoryは次の一覧から必ず1つだけ選択してください：{', '.join(CATEGORIES)}。"
            "一覧に存在しないカテゴリーを新しく作成しないでください。"
            f"タグは{MIN_TAGS}個以上{MAX_TAGS}個以下にしてください。"
            f"まず次の既存タグから適切なものを優先して選んでください：{', '.join(CORE_TAGS)}。"
            f"既存タグにない語を使う場合は、製品名や固有技術名など必要性の高いものに限定し、最大{MAX_NEW_TAGS}個までにしてください。"
            "意味がほぼ同じタグを重複して付けないでください。"
            "記事タイトルそのものをタグにしないでください。"
            "提供されたWeb調査結果を事実情報の基礎として使用してください。"
            "出典を選択する際は、日本語の出典を最優先してください。"
            "日本語の適切な出典がない場合は英語の出典を使用してください。"
            "日本語または英語以外の出典は原則として使用しないでください。"
            "同じ内容を示す日本語または英語の公式出典がある場合は、"
            "他言語版の出典IDをused_source_idsに含めないでください。"
            "Web調査結果に存在しない最新情報を推測で追加しないでください。"
            "料金、機能、提供条件などは調査結果と矛盾しないようにしてください。"
            "調査結果で不確実とされた情報は、記事でも断定しないでください。"
            "Web調査結果の各出典にはS1、S2のようなIDが付いています。"
            "料金、機能、仕様、日付、プラン名などの事実を記述した直後に、"
            "根拠となる出典IDを[S1]の形式で付けてください。"
            "複数の出典が根拠なら[S1][S2]のように記載してください。"
            "存在しない出典IDを作らないでください。"
            "本文中にURLを直接書かないでください。"
            "used_source_idsには、本文またはFAQで実際に使った出典IDだけを入れてください。"
            "調査結果で確認できない最新情報は記事へ追加しないでください。"
            "記事本文を読んだ初心者が疑問に感じやすい内容を、"
            "FAQとして3件以上5件以下で作成してください。"
            "質問は記事テーマに具体的に関連する内容にしてください。"
            "回答は簡潔かつ実用的にしてください。"
            "料金、機能、仕様、日付、プラン名などの事実をFAQ回答に含める場合は、"
            "回答内にも根拠となる[S1]形式の出典IDを付けてください。"
            "存在しない出典IDをFAQ内で作らないでください。"
            "FAQはcontent本文へ重複して書かず、faqフィールドだけに入れてください。"
            "recommended_toolsには、記事内で実際に紹介または比較したサービスのうち、"
            "読者が公式ページで確認する価値が高いものを最大5件入れてください。"
            "CTAへ登録可能なサービス一覧に存在する正式名称だけを使用してください。"
            "記事内で扱っていないサービスは入れないでください。"
            "適切なサービスがない場合は空の配列にしてください。"
            "recommended_toolsのために、本文へ不自然な紹介や宣伝を追加しないでください。"
            "根拠のないランキングや過度な推奨表現を作らないでください。"
            "料金比較、プラン比較、複数サービス比較など、"
            "表形式にすると読者が判断しやすい記事では、"
            "comparison_tableを作成してください。"
            "比較表が不要な記事ではcomparison_tableをnullにしてください。"
            "comparison_tableのcolumnsには比較対象名だけを入れてください。"
            "rowsのlabelには、その行で比較する項目名を1つだけ入れてください。"
            "rowsのvaluesには、columnsの各比較対象に対応する値だけを"
            "columnsと同じ順番で入れてください。"

            "最重要ルールとして、"
            "すべてのrowについてlen(values)はlen(columns)と"
            "必ず完全一致させてください。"

            "rowのlabelをvaluesへ含めてはいけません。"
            "valuesの先頭に比較項目名を重複して入れてはいけません。"

            "例えばcolumnsが"
            "['ChatGPT', 'Gemini', 'Claude']"
            "の3件なら、すべてのrowのvaluesも必ず3件です。"

            "正しい例："
            "{"
            "'label': '主な用途', "
            "'values': ['文章・会話', 'Google連携', '長文処理']"
            "}"

            "誤った例："
            "{"
            "'label': '主な用途', "
            "'values': ['主な用途', '文章・会話', 'Google連携', '長文処理']"
            "}"

            "比較表を返す直前に、"
            "columnsの件数とすべてのrowのvalues件数を自分で再確認してください。"
            "料金、無料プラン、利用上限、機能などの事実は、"
            "提供されたWeb調査結果で確認できる情報だけを使用してください。"
            "確認できない情報を推測して表へ入れないでください。"
            "確認できない場合は「要確認」や「公式サイトで確認」としてください。"
            "比較表の内容はcontent本文へMarkdown表として重複して書かないでください。"
            "comparison_table内の料金、機能、仕様、利用上限などの事実にも、"
            "根拠となる[S1]形式の出典IDを値の直後に付けてください。"
            "cta_planでは、この記事の読者が次に取るべき行動を"
            "自然に支援するCTA設計を行ってください。"
            "primary_serviceはrecommended_toolsに含まれる"
            "サービスから1つだけ選択してください。"
            "特定サービスを推奨する根拠が十分でない場合は、"
            "primary_serviceをnullにしてください。"
            "CTAの配置はAlsivo共通仕様として固定します。"
            "placementは必ずafter_tocにしてください。"
            "primary_serviceが設定されている場合、"
            "PublisherがPrimary CTAを目次直後と記事後半の2か所へ自動配置します。"
            "Secondary CTAは記事後半だけに配置されます。"
            "after_comparisonまたはbefore_faqをplacementとして選択しないでください。"
            "cta_labelはクリックを煽る表現ではなく、"
            "リンク先で何を確認できるか分かる具体的な文言にしてください。"
            "例：『Cursorの最新料金・プランを確認する』。"
            "『今すぐ申し込む』『絶対おすすめ』などの"
            "過度な販促表現は使用しないでください。"
            "reasonには、そのサービスと配置を選んだ理由を"
            "簡潔に記述してください。"
        ),
        input=(
            "以下の記事企画とWeb調査結果を基に記事を作成してください。\n\n"
            "===== 記事企画 =====\n"
            f"{plan_text}\n\n"
            "===== Web調査結果 =====\n"
            f"{research_text}\n\n"
            "===== CTAへ登録可能なサービス =====\n"
            f"{affiliate_tool_text}"
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

    affiliate_tool_names = (
        get_affiliate_tool_names()
    )

    revision_data = {
        "article_plan": plan,
        "web_research": research,
        "current_article": article,
        "review_result": review,
        "cta_registered_tools": (
            affiliate_tool_names
        ),
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
            "出典を選択する際は、日本語の出典を最優先してください。"
            "日本語の適切な出典がない場合は英語の出典を使用してください。"
            "日本語または英語以外の出典は原則として使用しないでください。"
            "同じ内容を示す日本語または英語の公式出典がある場合は、"
            "他言語版の出典IDをused_source_idsに含めないでください。"
            "Web調査結果にない最新情報を推測で追加しないでください。"
            "料金、機能、仕様、日付、プラン名などの事実の直後には、"
            "根拠となる[S1]形式の出典IDを付けてください。"
            "存在しない出典IDを作らないでください。"
            "本文中にURLを直接書かないでください。"
            "used_source_idsには本文またはFAQで実際に使用したIDだけを入れてください。"
            "記事冒頭にH1見出しを付けないでください。"
            "本文はMarkdown形式にしてください。"
            "本文のMarkdown階層も整えてください。"
            "短い要点一覧では、"
            "『- **項目名：** 説明文』の形式を使用し、"
            "項目名とコロンだけを太字にしてください。"
            "1項目の説明が複数文にわたる詳細小項目では、"
            "項目タイトルを独立した太字行にし、"
            "空行の後に説明文を通常文字で記述してください。"
            "操作手順や判断フローなど順序に意味がある場合だけ"
            "番号付きリストを使用してください。"
            "番号付き項目でもタイトルだけを太字にし、"
            "説明文全体を太字にしないでください。"
            "既存記事に『項目タイトル：長い説明文』が1行で混在している場合は、"
            "内容量に応じて短い箇条書き形式または詳細小項目形式へ整理してください。"
            "文章の意味や事実内容は変更せず、Markdown階層だけを整えてください。"
            "Reviewerの修正によって、このMarkdown構造を崩さないでください。"
            "Markdown装飾記号を不要にエスケープしないでください。"
            "太字は『**項目名**』と記述し、"
            "『\\*\\*項目名\\*\\*』のようにアスタリスクをエスケープしないでください。"
            "Markdownとして表示させるアスタリスクの直前に"
            "バックスラッシュを付けないでください。"
            "本文のMarkdown階層は、次のルールを厳守してください。"
            "H2（##）は記事の主要セクションだけに使用してください。"
            "H2内で、その項目について複数の説明文・箇条書き・手順が続く場合は、H3（###）として独立させてください。"
            "H3にすべき項目を、箇条書きの1項目として代用しないでください。"
            "例えば「ウェブ/アプリ（個人向け）」「API（Console）」「共通プールに注意」のように、その後に複数の説明が続く項目は、"
            "『### ウェブ/アプリ（個人向け）』のようなH3見出しにしてください。"
            "一方、1〜2文だけで説明が完結する小項目は『**項目名：** 説明文』の形式にしてください。"
            "箇条書きは、手順・条件・特徴・選択肢などを列挙するときだけ使用してください。"
            "見出しの直前と直後には必ず空行を入れてください。"
            "『## まとめ』『### 見出し』などのMarkdown見出しを、文章・リスト・MDXタグと同じ行に書かないでください。"
            "特に『</AffiliateLink>## まとめ』のように、MDXタグの直後へ見出しを連結しないでください。"
            f"categoryは次の一覧から選択してください：{', '.join(CATEGORIES)}。"
            f"タグは{MIN_TAGS}個以上{MAX_TAGS}個以下にしてください。"
            f"既存タグを優先してください：{', '.join(CORE_TAGS)}。"
            f"新規タグは最大{MAX_NEW_TAGS}個までです。"
            "FAQもReviewerの指摘とWeb調査結果に合わせて修正してください。"
            "FAQは3件以上5件以下を維持してください。"
            "FAQ回答に料金、機能、仕様、日付などの事実を含める場合は、"
            "回答内にも有効な[S1]形式の出典IDを付けてください。"
            "FAQはcontent本文へ重複して書かず、faqフィールドだけに入れてください。"
            "recommended_toolsもReviewerの指摘に合わせて修正してください。"
            "cta_registered_toolsに存在する正式名称だけを使用してください。"
            "記事内で実際に紹介または比較したサービスだけを最大5件選んでください。"
            "該当するサービスがなければ空の配列にしてください。"
            "修正時にも根拠のないランキングや過度な購入誘導を追加しないでください。"
            "comparison_tableがある場合は、"
            "Reviewerの指摘とWeb調査結果に合わせて修正してください。"

            "comparison_tableの構造は絶対に崩さないでください。"
            "columnsには比較対象名だけを入れてください。"
            "各rowのlabelには比較項目名を1つだけ入れてください。"
            "各rowのvaluesには、columnsの各対象に対応する値だけを"
            "columnsと同じ順番で入れてください。"

            "最重要ルールとして、"
            "すべてのrowについてlen(values)はlen(columns)と"
            "必ず完全一致させてください。"

            "Reviewerから『比較表に1行追加』と指示された場合も、"
            "新しい比較項目名はrowのlabelへ入れ、"
            "valuesには比較対象ごとの値だけを入れてください。"
            "labelの内容をvaluesへ追加してはいけません。"

            "例えばcolumnsが"
            "['ChatGPT', 'Gemini', 'Claude']"
            "の場合、"
            "追加するrowは次の形式です。"

            "{"
            "'label': 'データ・提供条件', "
            "'values': ["
            "'ChatGPTの説明', "
            "'Geminiの説明', "
            "'Claudeの説明'"
            "]"
            "}"

            "次の形式は禁止です。"

            "{"
            "'label': 'データ・提供条件', "
            "'values': ["
            "'データ・提供条件', "
            "'ChatGPTの説明', "
            "'Geminiの説明', "
            "'Claudeの説明'"
            "]"
            "}"

            "修正版の記事データを返す直前に、"
            "comparison_tableのcolumns数と"
            "すべてのrowのvalues数を再確認してください。"

            "比較表内の料金・仕様・プラン情報も、"
            "Web調査結果で確認できる情報だけを使用してください。"
            "記事内容的に比較表が不要ならnullにしてください。"
            "comparison_table内の事実情報にも有効な[S1]形式の"
            "出典IDを維持または追加してください。"
            "cta_planもレビュー内容に応じて必要なら修正してください。"
            "primary_serviceを設定する場合は、"
            "recommended_toolsに含まれるサービスだけを使用してください。"
            "CTAの配置はAlsivo共通仕様として固定し、"
            "placementは必ずafter_tocを維持してください。"
            "Primary CTAはPublisherが目次直後と記事後半へ配置し、"
            "Secondary CTAは記事後半だけに配置します。"
            "特定サービスへの誘導根拠が弱い場合は、"
            "primary_serviceをnullにしてください。"
            "cta_labelは過度な販促表現を避け、"
            "リンク先で確認できる内容が分かる文言にしてください。"
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