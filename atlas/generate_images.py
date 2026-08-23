from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import (
    MODEL,
    OPENAI_API_KEY,
)
from engines.article_loader import (
    load_article_by_slug,
)
from engines.instagram_image_generator import (
    generate_article_images,
)
from engines.affiliate_disclosure import content_has_affiliate_link


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

WEBSITE_ROOT = BASE_DIR.parent

BLOG_DIR = (
    WEBSITE_ROOT
    / "content"
    / "blog"
)


# =========================================================
# OpenAI
# =========================================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=120.0,
    max_retries=2,
)


# =========================================================
# Validation
# =========================================================

def validate_slug(
    slug: str,
) -> str:
    """コマンドラインから受け取ったslugを確認する。"""

    cleaned_slug = (
        slug.strip()
        .lower()
    )

    if not cleaned_slug:
        raise ValueError(
            "slugが指定されていません。"
        )

    if not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*",
        cleaned_slug,
    ):
        raise ValueError(
            "slugには半角英小文字、数字、"
            "ハイフンだけを使用してください。"
        )

    return cleaned_slug


def normalize_layout_text(
    value: str,
) -> str:
    """
    AI改行前後で文字列が変更されていないか
    比較するために整える。

    AIには改行位置だけを変更させるため、
    改行コードのみ除去して比較する。

    元の通常空白は保持する。
    """

    return (
        str(value)
        .replace("\r", "")
        .replace("\n", "")
    )


# =========================================================
# Article data
# =========================================================

def build_image_article(
    article: dict[str, Any],
) -> dict[str, Any]:
    """
    article_loaderで読み込んだ記事から、
    Phase Cで必要な情報を取り出す。
    """

    slug = str(
        article.get(
            "slug",
            "",
        )
    ).strip()

    title = str(
        article.get(
            "title",
            "",
        )
    ).strip()

    description = str(
        article.get(
            "description",
            "",
        )
    ).strip()

    category = str(
        article.get(
            "category",
            "",
        )
    ).strip()

    content = str(
        article.get(
            "content",
            "",
        )
    ).strip()

    raw_tags = article.get(
        "tags",
        [],
    )

    if not slug:
        raise ValueError(
            "記事のslugを取得できませんでした。"
        )

    if not title:
        raise ValueError(
            "記事のtitleを取得できませんでした。"
        )

    if not description:
        raise ValueError(
            "記事のdescriptionを取得できませんでした。"
        )

    if not category:
        raise ValueError(
            "記事のcategoryを取得できませんでした。"
        )

    if not isinstance(
        raw_tags,
        list,
    ):
        raw_tags = []

    tags = [
        str(tag).strip()
        for tag in raw_tags
        if str(tag).strip()
    ]

    return {
        "slug": slug,
        "title": title,
        "description": description,
        "category": category,
        "tags": tags,
        "content": content,
        "is_affiliate_article": content_has_affiliate_link(content),
    }


# =========================================================
# AI image copy
# =========================================================

IMAGE_COPY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "image_title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 40,
        },
        "image_subtitle": {
            "type": "string",
            "minLength": 1,
            "maxLength": 60,
        },
    },
    "required": [
        "image_title",
        "image_subtitle",
    ],
    "additionalProperties": False,
}


def generate_image_copy(
    article: dict[str, Any],
) -> dict[str, str]:
    """
    記事内容を基に、
    Blog / Instagram共通の画像専用コピーを生成する。
    """

    title = str(
        article.get(
            "title",
            "",
        )
    ).strip()

    description = str(
        article.get(
            "description",
            "",
        )
    ).strip()

    content = str(
        article.get(
            "content",
            "",
        )
    ).strip()

    content_excerpt = (
        content[:3000]
    )

    print(
        "[Image Copy] "
        "AIが画像用コピーを生成中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIツール情報メディアAlsivoの"
            "編集者兼グラフィックデザイナーです。"

            "記事のBlogアイキャッチ画像と"
            "Instagram投稿画像に共通で使用する、"
            "短く分かりやすい画像専用コピーを作成してください。"

            "SEO記事タイトルをそのまま短縮するのではなく、"
            "読者が抱えている疑問・悩み・判断課題と、"
            "この記事を読むことで得られる答えが"
            "一瞬で伝わるコピーにしてください。"

            "画像だけを見ても、"
            "何についての記事なのか分かるようにしてください。"

            "ただし、記事本文にない内容を"
            "追加してはいけません。"

            "事実、料金、数値、機能、提供条件などを"
            "記事にない形で新しく断定しないでください。"

            "煽り表現は禁止です。"

            "『知らないと損』"
            "『絶対』"
            "『危険』"
            "『今すぐ』"
            "『必ず』"
            "など、過度に不安や焦りを"
            "あおる表現を使用しないでください。"

            "記事タイトルより短くし、"
            "検索キーワードを不自然に"
            "詰め込まないでください。"

            "サービス名や製品名など、"
            "記事テーマを理解するために重要な語は"
            "できるだけ保持してください。"

            "image_titleは、"
            "画像で最も大きく表示する主見出しです。"

            "image_titleでは、"
            "読者が自分の疑問だと感じられる表現、"
            "または記事の中心的な判断課題を"
            "簡潔に示してください。"

            "image_titleは原則として"
            "15〜30文字程度を目安にしてください。"

            "疑問形が自然な記事では、"
            "『〜で十分？』"
            "『〜は必要？』"
            "『〜は何が違う？』"
            "のような自然な疑問形を使用して構いません。"

            "ただし、すべての記事を"
            "疑問形にする必要はありません。"

            "image_subtitleは、"
            "image_titleを補足し、"
            "この記事で何が分かるのか、"
            "何を判断できるのかを示してください。"

            "image_subtitleは原則として"
            "25〜50文字程度を目安にしてください。"

            "短くしすぎて抽象的な文章にせず、"
            "画像内のスペースを活用して、"
            "読者がこの記事を読むメリットを"
            "具体的に理解できる文章にしてください。"

            "ただし、60文字を超えてはいけません。"

            "image_titleとimage_subtitleで"
            "同じ内容を言い換えて"
            "重複させないでください。"

            "悪い例："
            "image_title：ChatGPT Plusは無料版と何が違う？"
            "image_subtitle：ChatGPT Plusと無料版の違いを解説"

            "良い例："
            "image_title：ChatGPT Plus、無料版で十分？"
            "image_subtitle：料金・利用制限・できることを比べて、"
            "自分に課金が必要か判断できます"

            "悪い例："
            "image_title：知らないと損！ChatGPT Plus"
            "image_subtitle：今すぐ課金すべき理由"

            "このような煽り表現は使用しないでください。"
        ),
        input=(
            "以下の記事から画像専用コピーを"
            "作成してください。\n\n"

            "===== 記事タイトル =====\n"
            f"{title}\n\n"

            "===== 記事概要 =====\n"
            f"{description}\n\n"

            "===== 記事本文冒頭 =====\n"
            f"{content_excerpt}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_image_copy",
                "schema": IMAGE_COPY_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "画像用コピーを取得できませんでした。"
        )

    try:

        result = json.loads(
            response.output_text
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "画像用コピーのJSON変換に"
            "失敗しました。"
        ) from error

    image_title = str(
        result.get(
            "image_title",
            "",
        )
    ).strip()

    image_subtitle = str(
        result.get(
            "image_subtitle",
            "",
        )
    ).strip()

    if not image_title:
        raise ValueError(
            "image_titleが空です。"
        )

    if not image_subtitle:
        raise ValueError(
            "image_subtitleが空です。"
        )

    print()
    print(
        "[Image Copy]"
    )

    print(
        f"  Title：{image_title}"
    )

    print(
        f"  Subtitle：{image_subtitle}"
    )

    print()

    return {
        "image_title":
            image_title,
        "image_subtitle":
            image_subtitle,
    }


# =========================================================
# AI layout
#
# TitleだけでなくSubtitleも、
# Blog / Instagramそれぞれ別にAIで改行する。
# =========================================================

IMAGE_LAYOUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {

        "blog_title_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },

        "instagram_title_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },

        "blog_subtitle_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },

        "instagram_subtitle_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },

        "article_title_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },

        "card_title_lines": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "string",
                "minLength": 1,
            },
        },
    },

    "required": [
        "blog_title_lines",
        "instagram_title_lines",
        "blog_subtitle_lines",
        "instagram_subtitle_lines",
        "article_title_lines",
        "card_title_lines",
    ],

    "additionalProperties": False,
}


def validate_layout_lines(
    original_text: str,
    lines: Any,
    max_lines: int,
    field_name: str,
) -> list[str]:
    """
    AIが返した改行結果について、

    ・文字を書き換えていない
    ・行数が上限以内
    ・空行がない

    ことを確認する。
    """

    if not isinstance(
        lines,
        list,
    ):

        raise ValueError(
            f"{field_name}が配列ではありません。"
        )

    cleaned_lines = [
        str(line).strip()
        for line in lines
        if str(line).strip()
    ]

    if not cleaned_lines:

        raise ValueError(
            f"{field_name}が空です。"
        )

    if len(
        cleaned_lines
    ) > max_lines:

        raise ValueError(
            f"{field_name}の行数が多すぎます。"
        )

    original = normalize_layout_text(
        original_text
    )

    reconstructed = normalize_layout_text(
        "".join(
            cleaned_lines
        )
    )

    if original != reconstructed:

        raise ValueError(
            f"{field_name}で元の文字列が"
            "変更されています。"
        )

    return cleaned_lines


def generate_image_layout(
    article: dict[str, Any],
) -> dict[str, list[str]]:
    """
    OpenAIに表示場所ごとの自然な改行位置を決めさせる。

    ・Blog画像タイトル
    ・Instagram画像タイトル
    ・Blog画像説明文
    ・Instagram画像説明文
    ・記事H1
    ・記事カードタイトル

    の6種類を独立して最適化する。
    """

    article_title = str(
        article[
            "title"
        ]
    )

    image_title = str(
        article[
            "image_title"
        ]
    )

    image_subtitle = str(
        article[
            "image_subtitle"
        ]
    )

    print(
        "[Image Layout] "
        "AIがタイトル・説明文の"
        "自然な改行位置を解析中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(

            "あなたは日本語WebメディアAlsivoの"
            "編集者兼グラフィックデザイナーです。"

            "記事タイトルと画像専用コピーについて、"
            "表示場所ごとの自然な改行位置だけを"
            "決定してください。"

            # =================================================
            # 最重要ルール
            # =================================================

            "最重要ルールです。"

            "渡された文字列を"
            "1文字も変更してはいけません。"

            "追加、削除、要約、言い換え、"
            "表記変更、句読点変更は禁止です。"

            "返した各配列の文字列を"
            "上から順にすべて連結すると、"
            "対応する元文字列と"
            "完全に一致しなければなりません。"

            "あなたが行うのは"
            "改行位置を決めることだけです。"

            # =================================================
            # 共通ルール
            # =================================================

            "文字数だけで機械的に"
            "分割しないでください。"

            "日本語として意味のまとまり、"
            "文節、語句のまとまりを理解して"
            "改行してください。"

            "単語の途中では"
            "絶対に改行しないでください。"

            "例えば、"
            "『おすすめ』を"
            "『おすす』『め』に分けたり、"
            "『使い方』を"
            "『使』『い方』に分けたりしてはいけません。"

            "助詞だけが次の行へ"
            "孤立する改行も避けてください。"

            "『は』『が』『を』『に』『で』『と』"
            "などが単独で行頭に来る形は"
            "できるだけ避けてください。"

            "句読点が次の行の"
            "先頭に来ないようにしてください。"

            "『？』『！』『。』『：』『｜』などは"
            "意味の区切りとして"
            "積極的に利用してください。"

            "『・』は列挙を示す場合があるため、"
            "列挙全体の意味を確認してから"
            "改行してください。"

            "意味が強くつながっている語句を"
            "単に行幅を揃えるためだけに"
            "分割しないでください。"

            "改行は日本語としての自然さだけでなく、"
            "実際に表示したときの"
            "視覚的な行幅バランスも"
            "必ず考慮してください。"

            "各行を完全に同じ長さに"
            "揃える必要はありませんが、"
            "1行だけ極端に長い、"
            "または1行だけ極端に短い配置は"
            "避けてください。"

            "特に最終行だけが短く残る場合は、"
            "その改行位置が本当に最適か"
            "必ず再検討してください。"

            "前の行から意味のまとまりを"
            "自然に移動できる場合は、"
            "各行の視覚的な幅が"
            "極端に偏らないように"
            "改行位置を調整してください。"

            "ただし、行幅を揃えるために"
            "単語や強く結びついた語句を"
            "不自然に分割してはいけません。"

            "最終的には、"
            "意味の自然さと"
            "視覚的な行幅バランスの"
            "両方を満たす改行を選んでください。"

            "また、6種類の表示場所は"
            "それぞれ横幅、文字サイズ、用途が異なります。"

            "他の表示場所で決めた改行を"
            "流用してはいけません。"

            "6種類それぞれについて、"
            "元の文字列から独立して"
            "最適な改行位置を判断してください。"

            # =================================================
            # 括弧
            # =================================================

            "丸括弧『（ ）』内は"
            "原則として1つの意味のまとまりとして"
            "扱ってください。"

            "括弧内を途中で分割することは"
            "できるだけ避けてください。"

            "括弧内にサービス名や製品名が"
            "スラッシュ『/』で列挙されている場合、"
            "原則としてスラッシュ位置で"
            "改行しないでください。"

            # =================================================
            # Blog image title
            # =================================================

            "【blog_title_lines】"

            "1536×864の横長Blog画像で"
            "大きく表示する画像専用タイトルです。"

            "横幅が広いため、"
            "原則1〜2行を優先してください。"

            "長い場合のみ3行を使用してください。"

            "短い画像タイトルを"
            "不必要に細かく"
            "分割してはいけません。"

            # =================================================
            # Instagram image title
            # =================================================

            "【instagram_title_lines】"

            "1080×1350のInstagram画像で"
            "大きく表示する画像専用タイトルです。"

            "Blogより表示可能な横幅が狭いため、"
            "Blogと同じ改行位置を"
            "そのまま使う必要はありません。"

            "原則2〜3行を優先してください。"

            "必要な場合のみ4行まで"
            "使用してください。"

            # =================================================
            # Blog subtitle
            # =================================================

            "【blog_subtitle_lines】"

            "1536×864の横長Blog画像に表示する"
            "画像専用説明文です。"

            "画像内で比較的大きな文字として"
            "表示されます。"

            "Blogは横幅が広いため、"
            "意味のまとまりを保ちながら"
            "1〜3行程度を優先してください。"

            "文章が長い場合のみ"
            "4行まで使用してください。"

            "特に、"
            "『料金・利用制限・できることを比べて、"
            "自分に課金が必要か判断できます』"
            "のような文章では、"

            "『料金・利用制限・できることを比べて、』"
            "『自分に課金が必要か判断できます』"

            "のように、意味の切れ目で"
            "改行することを優先してください。"

            "単に画像幅いっぱいまで"
            "文字を詰めてから"
            "次の行へ送る方法は禁止です。"

            # =================================================
            # Instagram subtitle
            # =================================================

            "【instagram_subtitle_lines】"

            "1080×1350のInstagram画像に表示する"
            "画像専用説明文です。"

            "Blogより横幅が狭いため、"
            "Blogとは独立して"
            "改行位置を判断してください。"

            "原則2〜4行程度を優先してください。"

            "文章が長い場合のみ"
            "5行まで使用してください。"

            "1行へ詰め込みすぎて"
            "極端に小さなフォントになるより、"
            "意味の自然な位置で"
            "複数行へ分けることを優先してください。"

            "ただし、行数を増やすためだけに"
            "短い語句を細かく分割してはいけません。"

            "Instagram説明文では特に、"
            "最後の1行だけが"
            "他の行より大幅に短くなる配置を"
            "避けてください。"

            "例えば3行にする場合、"
            "1〜2行目へ文字を詰め込み、"
            "3行目に短い結論だけを残すより、"
            "意味のまとまりを保ったまま"
            "3行全体の視覚的な幅が"
            "自然になる改行を優先してください。"

            "2行で自然か、3行で自然か、"
            "4行で自然かを比較したうえで、"
            "最も読みやすい行数を選んでください。"
            # =================================================
            # Article H1
            # =================================================

            "【article_title_lines】"

            "個別記事ページ上部の"
            "SEO記事タイトルです。"

            "画像ではありません。"

            "PCでは横幅が比較的広いため、"
            "原則1〜3行で"
            "自然に読みやすくしてください。"

            "画像用タイトルの改行位置を"
            "流用してはいけません。"

            # =================================================
            # Card
            # =================================================

            "【card_title_lines】"

            "記事一覧、検索結果、トップページ、"
            "関連記事カードで表示する"
            "SEO記事タイトルです。"

            "基本は2行でまとめてください。"

            "かなり長いタイトルの場合のみ"
            "3行まで使用してください。"

            "明確な区切り記号"
            "『｜』『？』『：』などがある場合は、"
            "まずその位置で自然に"
            "2行へ分けられないか検討してください。"
        ),
        input=(
            "以下の3種類の文字列について、"
            "6種類の表示場所ごとに"
            "自然な改行位置を決定してください。\n\n"

            "===== SEO記事タイトル =====\n"
            f"{article_title}\n\n"

            "===== 画像専用タイトル =====\n"
            f"{image_title}\n\n"

            "===== 画像専用説明文 =====\n"
            f"{image_subtitle}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_image_layout",
                "schema": IMAGE_LAYOUT_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:

        raise RuntimeError(
            "画像レイアウト結果を"
            "取得できませんでした。"
        )

    try:

        result = json.loads(
            response.output_text
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            "画像レイアウト結果の"
            "JSON変換に失敗しました。"
        ) from error

    # =====================================================
    # Validate
    # =====================================================

    blog_title_lines = (
        validate_layout_lines(
            original_text=image_title,
            lines=result.get(
                "blog_title_lines"
            ),
            max_lines=3,
            field_name="blog_title_lines",
        )
    )

    instagram_title_lines = (
        validate_layout_lines(
            original_text=image_title,
            lines=result.get(
                "instagram_title_lines"
            ),
            max_lines=4,
            field_name="instagram_title_lines",
        )
    )

    blog_subtitle_lines = (
        validate_layout_lines(
            original_text=image_subtitle,
            lines=result.get(
                "blog_subtitle_lines"
            ),
            max_lines=4,
            field_name="blog_subtitle_lines",
        )
    )

    instagram_subtitle_lines = (
        validate_layout_lines(
            original_text=image_subtitle,
            lines=result.get(
                "instagram_subtitle_lines"
            ),
            max_lines=5,
            field_name="instagram_subtitle_lines",
        )
    )

    article_title_lines = (
        validate_layout_lines(
            original_text=article_title,
            lines=result.get(
                "article_title_lines"
            ),
            max_lines=3,
            field_name="article_title_lines",
        )
    )

    card_title_lines = (
        validate_layout_lines(
            original_text=article_title,
            lines=result.get(
                "card_title_lines"
            ),
            max_lines=3,
            field_name="card_title_lines",
        )
    )

    # =====================================================
    # Print
    # =====================================================

    print()
    print(
        "[Image Layout] Blog Title"
    )

    for line in blog_title_lines:

        print(
            f"  {line}"
        )

    print()
    print(
        "[Image Layout] Instagram Title"
    )

    for line in instagram_title_lines:

        print(
            f"  {line}"
        )

    print()
    print(
        "[Image Layout] Blog Subtitle"
    )

    for line in blog_subtitle_lines:

        print(
            f"  {line}"
        )

    print()
    print(
        "[Image Layout] Instagram Subtitle"
    )

    for line in instagram_subtitle_lines:

        print(
            f"  {line}"
        )

    print()
    print(
        "[Image Layout] Article"
    )

    for line in article_title_lines:

        print(
            f"  {line}"
        )

    print()
    print(
        "[Image Layout] Card"
    )

    for line in card_title_lines:

        print(
            f"  {line}"
        )

    print()

    return {
        "blog_title_lines":
            blog_title_lines,

        "instagram_title_lines":
            instagram_title_lines,

        "blog_subtitle_lines":
            blog_subtitle_lines,

        "instagram_subtitle_lines":
            instagram_subtitle_lines,

        "article_title_lines":
            article_title_lines,

        "card_title_lines":
            card_title_lines,
    }


# =========================================================
# MDX helpers
# =========================================================

def find_article_path(
    slug: str,
) -> Path:
    """slugからMDXファイルを取得する。"""

    article_path = (
        BLOG_DIR
        / f"{slug}.mdx"
    )

    if not article_path.exists():

        raise FileNotFoundError(
            "記事ファイルが見つかりません："
            f"{article_path}"
        )

    return article_path


def escape_yaml_string(
    value: str,
) -> str:
    """YAMLダブルクォート用に文字列を処理する。"""

    return (
        value
        .replace(
            "\\",
            "\\\\",
        )
        .replace(
            '"',
            '\\"',
        )
    )


def build_yaml_string_array(
    field_name: str,
    values: list[str],
) -> str:
    """文字列配列をYAMLへ変換する。"""

    lines = [
        f"{field_name}:"
    ]

    for value in values:

        escaped = escape_yaml_string(
            value
        )

        lines.append(
            f'  - "{escaped}"'
        )

    return "\n".join(
        lines
    )


def remove_frontmatter_array(
    frontmatter: str,
    field_name: str,
) -> str:
    """
    既存の

    field:
      - "..."
      - "..."

    を削除する。
    """

    pattern = re.compile(
        rf"^{re.escape(field_name)}:\s*\n"
        rf"(?:[ \t]+-[^\n]*\n?)*",
        flags=re.MULTILINE,
    )

    return pattern.sub(
        "",
        frontmatter,
    )


def update_article_frontmatter(
    slug: str,
    blog_path: Path,
    article_title_lines: list[str] | None = None,
    card_title_lines: list[str] | None = None,
) -> None:
    """
    MDX frontmatterへ

    ・新しいBlog画像
    ・個別記事ページ用のtitleLines

    を反映する。

    cardTitleLinesは保存しない。
    記事一覧・トップページ・関連記事カードは
    ブラウザ側の自然な改行へ任せる。

    Blog / Instagram画像用の改行情報は
    Phase C生成時だけ使用し、MDXへは保存しない。
    """

    # カードタイトルは強制改行しない。
    del card_title_lines

    if (
        not isinstance(
            article_title_lines,
            list,
        )
        or not article_title_lines
    ):
        raise ValueError(
            f"{slug}: article_title_linesがありません。"
        )

    article_path = find_article_path(
        slug
    )

    content = article_path.read_text(
        encoding="utf-8"
    )

    if not content.startswith(
        "---"
    ):
        raise ValueError(
            f"{slug}: frontmatterが見つかりません。"
        )

    parts = content.split(
        "---",
        2,
    )

    if len(parts) < 3:
        raise ValueError(
            f"{slug}: frontmatterの形式が不正です。"
        )

    frontmatter = parts[1]
    body = parts[2]

    # -----------------------------------------------------
    # image更新
    # -----------------------------------------------------

    image_url = (
        f"/images/blog/{blog_path.name}"
    )

    image_pattern = re.compile(
        r'^image:\s*["\']?.*?["\']?\s*$',
        flags=re.MULTILINE,
    )

    if not image_pattern.search(
        frontmatter
    ):
        raise ValueError(
            f"{slug}: frontmatterにimageがありません。"
        )

    frontmatter = image_pattern.sub(
        f'image: "{image_url}"',
        frontmatter,
        count=1,
    )

    # -----------------------------------------------------
    # titleLines更新
    #
    # 個別記事ページH1だけは、
    # Phase CでAIが独立して判断した改行を使用する。
    # -----------------------------------------------------

    frontmatter = remove_frontmatter_array(
        frontmatter,
        "titleLines",
    )

    frontmatter = remove_frontmatter_array(
        frontmatter,
        "cardTitleLines",
    )

    title_pattern = re.compile(
        r'^(title:\s*.+)$',
        flags=re.MULTILINE,
    )

    title_match = title_pattern.search(
        frontmatter
    )

    if not title_match:
        raise ValueError(
            f"{slug}: frontmatterにtitleがありません。"
        )

    title_lines_yaml = (
        build_yaml_string_array(
            "titleLines",
            article_title_lines,
        )
    )

    insertion = (
        title_match.group(1)
        + "\n"
        + title_lines_yaml
    )

    frontmatter = title_pattern.sub(
        lambda _: insertion,
        frontmatter,
        count=1,
    )

    # 削除によって空行が増えすぎた場合だけ軽く整理
    frontmatter = re.sub(
        r"\n{3,}",
        "\n\n",
        frontmatter,
    )

    updated_content = (
        "---"
        + frontmatter
        + "---"
        + body
    )

    article_path.write_text(
        updated_content,
        encoding="utf-8",
    )

    print(
        "[Image Generator] "
        "記事frontmatterを更新しました。"
    )

    print(
        f"  image：{image_url}"
    )

    print(
        "  titleLines："
        + " / ".join(
            article_title_lines
        )
    )

    print(
        "  cardTitleLines：削除"
    )


# =========================================================
# Article discovery
# =========================================================

def get_all_article_slugs() -> list[str]:
    """
    content/blog内の全MDXからslug一覧を取得する。
    """

    if not BLOG_DIR.exists():

        raise FileNotFoundError(
            "ブログディレクトリが"
            "見つかりません："
            f"{BLOG_DIR}"
        )

    slugs = sorted(
        path.stem
        for path in BLOG_DIR.glob(
            "*.mdx"
        )
        if path.is_file()
    )

    if not slugs:

        raise ValueError(
            "生成対象の記事がありません。"
        )

    return slugs


# =========================================================
# Console
# =========================================================

def print_article_info(
    article: dict[str, Any],
) -> None:
    """生成対象の記事情報を表示する。"""

    print()
    print(
        "===== ALSIVO Image Generation ====="
    )
    print()

    print(
        f"Slug：{article['slug']}"
    )

    print(
        f"Title：{article['title']}"
    )

    print(
        f"Category：{article['category']}"
    )

    tags = article.get(
        "tags",
        [],
    )

    if tags:

        print(
            "Tags："
            + ", ".join(
                tags
            )
        )

    print()


# =========================================================
# Single article
# =========================================================

def generate_images_for_slug(
    slug: str,
) -> tuple[
    Path,
    Path,
]:
    """
    1記事について

    1. 記事読込
    2. AI画像コピー生成
    3. AIタイトル・説明文改行
    4. Blog画像生成
    5. Instagram画像生成
    6. MDX frontmatter更新

    を行う。
    """

    cleaned_slug = validate_slug(
        slug
    )

    print(
        "[Image Generator] "
        f"記事を読み込み中：{cleaned_slug}"
    )

    article = load_article_by_slug(
        cleaned_slug
    )

    image_article = build_image_article(
        article
    )

    print_article_info(
        image_article
    )

    # -----------------------------------------------------
    # AIで画像専用コピーを生成
    # -----------------------------------------------------

    image_copy = generate_image_copy(
        image_article
    )

    image_article[
        "image_title"
    ] = image_copy[
        "image_title"
    ]

    image_article[
        "image_subtitle"
    ] = image_copy[
        "image_subtitle"
    ]

    # -----------------------------------------------------
    # AIで6種類の改行を決定
    # -----------------------------------------------------

    layout = generate_image_layout(
        image_article
    )

    # -----------------------------------------------------
    # 画像生成エンジンへ渡す
    # -----------------------------------------------------

    image_article[
        "blog_title_lines"
    ] = layout[
        "blog_title_lines"
    ]

    image_article[
        "instagram_title_lines"
    ] = layout[
        "instagram_title_lines"
    ]

    image_article[
        "blog_subtitle_lines"
    ] = layout[
        "blog_subtitle_lines"
    ]

    image_article[
        "instagram_subtitle_lines"
    ] = layout[
        "instagram_subtitle_lines"
    ]

    # -----------------------------------------------------
    # Blog + Instagram画像生成
    # -----------------------------------------------------

    blog_path, instagram_path = (
        generate_article_images(
            image_article
        )
    )

    # -----------------------------------------------------
    # MDX frontmatter更新
    # -----------------------------------------------------

    update_article_frontmatter(
        slug=cleaned_slug,
        blog_path=blog_path,
        article_title_lines=layout[
            "article_title_lines"
        ],
        card_title_lines=layout[
            "card_title_lines"
        ],
    )

    return (
        blog_path,
        instagram_path,
    )


# =========================================================
# All articles
# =========================================================

def generate_all_images() -> bool:
    """
    全記事について一括実行する。

    1記事失敗しても、
    残りの記事は続行する。
    """

    slugs = get_all_article_slugs()

    total = len(
        slugs
    )

    successful: list[str] = []

    failed: list[
        tuple[
            str,
            str,
        ]
    ] = []

    print()
    print(
        "=========================================="
    )

    print(
        " ALSIVO Phase C 一括画像・タイトル生成"
    )

    print(
        "=========================================="
    )

    print()

    print(
        f"対象記事数：{total}"
    )

    print()

    for index, slug in enumerate(
        slugs,
        start=1,
    ):

        print()
        print(
            "------------------------------------------"
        )

        print(
            f"[{index}/{total}] {slug}"
        )

        print(
            "------------------------------------------"
        )

        try:

            generate_images_for_slug(
                slug
            )

            successful.append(
                slug
            )

            print()
            print(
                f"[OK] {slug}"
            )

        except Exception as error:

            message = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            failed.append(
                (
                    slug,
                    message,
                )
            )

            print()
            print(
                f"[FAILED] {slug}"
            )

            print(
                message
            )

            print(
                "次の記事へ進みます。"
            )

    print()
    print()
    print(
        "=========================================="
    )

    print(
        " Phase C 一括処理結果"
    )

    print(
        "=========================================="
    )

    print()

    print(
        f"対象記事：{total}"
    )

    print(
        f"成功：{len(successful)}"
    )

    print(
        f"失敗：{len(failed)}"
    )

    if successful:

        print()
        print(
            "----- 成功 -----"
        )

        for slug in successful:

            print(
                f"[OK] {slug}"
            )

    if failed:

        print()
        print(
            "----- 失敗 -----"
        )

        for slug, message in failed:

            print(
                f"[FAILED] {slug}"
            )

            print(
                f"         {message}"
            )

    print()

    if failed:

        print(
            "Status：COMPLETED WITH ERRORS"
        )

        return False

    print(
        "Status：ALL GENERATED"
    )

    return True


# =========================================================
# CLI
# =========================================================

def print_usage() -> None:
    """CLIの使い方を表示する。"""

    print(
        "使い方："
    )

    print()

    print(
        "単体生成："
    )

    print(
        "python generate_images.py "
        "<article-slug>"
    )

    print()

    print(
        "全記事一括生成："
    )

    print(
        "python generate_images.py --all"
    )

    print()

    print(
        "例："
    )

    print(
        "python generate_images.py "
        "ai-search-recommendations"
    )


def main() -> None:
    """CLIエントリーポイント。"""

    try:

        args = sys.argv[
            1:
        ]

        if not args:

            print_usage()

            sys.exit(
                1
            )

        command = (
            args[0]
            .strip()
            .lower()
        )

        if command in {
            "--all",
            "-a",
            "all",
        }:

            success = generate_all_images()

            if not success:

                sys.exit(
                    1
                )

            return

        slug = command

        blog_path, instagram_path = (
            generate_images_for_slug(
                slug
            )
        )

        print()
        print(
            "===== Phase C 画像・タイトル生成完了 ====="
        )

        print()

        print(
            "Blog 16:9："
        )

        print(
            blog_path
        )

        print()

        print(
            "Instagram 4:5："
        )

        print(
            instagram_path
        )

        print()

        print(
            "Status：GENERATED"
        )

    except FileNotFoundError as error:

        print()
        print(
            "処理に失敗しました。"
        )

        print(
            str(error)
        )

        sys.exit(
            1
        )

    except ValueError as error:

        print()
        print(
            "処理に失敗しました。"
        )

        print(
            str(error)
        )

        sys.exit(
            1
        )

    except KeyboardInterrupt:

        print()
        print(
            "処理を中断しました。"
        )

        sys.exit(
            130
        )

    except Exception as error:

        print()
        print(
            "処理中に予期しない"
            "エラーが発生しました。"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        sys.exit(
            1
        )


if __name__ == "__main__":
    main()
