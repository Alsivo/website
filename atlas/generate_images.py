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


def normalize_title(
    value: str,
) -> str:
    """
    改行前後でタイトル文字列が
    変わっていないか比較するために整える。
    """

    return re.sub(
        r"\s+",
        "",
        str(value),
    )


# =========================================================
# Article data
# =========================================================

def build_image_article(
    article: dict[str, Any],
) -> dict[str, Any]:
    """
    article_loaderで読み込んだ記事から、
    画像生成に必要な情報を取り出す。
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
    }


# =========================================================
# AI title layout
# =========================================================

TITLE_LAYOUT_SCHEMA: dict[str, Any] = {
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
        "article_title_lines",
        "card_title_lines",
    ],
    "additionalProperties": False,
}


def validate_title_lines(
    original_title: str,
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

    original = normalize_title(
        original_title
    )

    reconstructed = normalize_title(
        "".join(
            cleaned_lines
        )
    )

    if original != reconstructed:
        raise ValueError(
            f"{field_name}でタイトル文字列が"
            "変更されています。"
        )

    return cleaned_lines


def generate_title_layout(
    article: dict[str, Any],
) -> dict[str, list[str]]:
    """
    OpenAIにタイトルの意味を理解させ、
    表示場所ごとの自然な改行位置だけを決めさせる。
    """

    title = article[
        "title"
    ]

    print(
        "[Title Layout] "
        "AIがタイトルの自然な改行位置を解析中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたは日本語WebメディアAlsivoの"
            "編集者兼グラフィックデザイナーです。"
            "記事タイトルを画面へ読みやすく配置するため、"
            "改行位置だけを決定してください。"

            "最重要ルールです。"
            "元タイトルの文字を1文字も変更してはいけません。"
            "追加、削除、要約、言い換え、表記変更、"
            "句読点変更は禁止です。"
            "行をすべて連結すると、必ず元タイトルと"
            "完全に同じ文字列になるようにしてください。"

            "文字数だけで機械的に分割せず、"
            "日本語として意味のまとまりを理解してください。"
            "単語の途中で切らないでください。"
            "『選\\nび方』『使\\nい方』『おすすめ\\n8選』"
            "のような不自然な分割を避けてください。"
            "助詞だけが行頭または行末に孤立する分割も避けてください。"
            "『｜』『？』『！』『：』など、"
            "意味上の区切りになる記号は積極的に利用してください。"
            "1〜2文字だけの極端に短い行を作らないでください。"
            "行数を揃える必要はありません。"

            "blog_title_linesはブログ用16:9画像です。"
            "横幅が広いため、1〜3行で、"
            "不必要に細かく分割しないでください。"

            "instagram_title_linesは1080×1350のSNS画像です。"
            "横幅が比較的狭いため、1〜5行で、"
            "意味のまとまりを最優先してください。"
            "3行や4行を優先する必要はありません。"

            "article_title_linesは個別記事ページ上部のH1です。"
            "PCでは比較的横幅が広いため、"
            "原則1〜3行で読みやすくしてください。"
            "特に『｜』などタイトル前半と後半を分ける"
            "明確な区切りがある場合は、"
            "その位置での改行を強く検討してください。"

            "card_title_linesは記事一覧、検索結果、"
            "トップページ、関連記事カード用です。"
            "カード幅は十分にあるため、"
            "基本は2行でまとめてください。"
            "タイトルがかなり長い場合のみ3行まで許可します。"
            "不必要に細かく分割しないでください。"
            "『初心者向けAI検索おすすめ8選｜用途別の選び方と安全な使い方ガイド』"
            "のようなタイトルでは、"
            "『初心者向けAI検索おすすめ8選｜』"
            "『用途別の選び方と安全な使い方ガイド』"
            "の2行が望ましいです。"
            "『初心者向けAI検索』『おすすめ8選｜』のように、"
            "意味的につながっている前半を細かく分割しないでください。"
            "明確な区切り記号『｜』『？』『：』がある場合は、"
            "まずその位置で2行に分けられないか検討してください。"
            "各行の長さを完全に揃える必要はありません。"
        ),
        input=(
            "次の記事タイトルについて、"
            "4種類の表示場所ごとに"
            "自然な改行位置を決定してください。\n\n"
            f"タイトル：{title}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "alsivo_title_layout",
                "schema": TITLE_LAYOUT_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "タイトル改行結果を取得できませんでした。"
        )

    try:
        result = json.loads(
            response.output_text
        )

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "タイトル改行結果のJSON変換に失敗しました。"
        ) from error

    blog_lines = validate_title_lines(
        original_title=title,
        lines=result.get(
            "blog_title_lines"
        ),
        max_lines=3,
        field_name="blog_title_lines",
    )

    instagram_lines = validate_title_lines(
        original_title=title,
        lines=result.get(
            "instagram_title_lines"
        ),
        max_lines=5,
        field_name="instagram_title_lines",
    )

    article_lines = validate_title_lines(
        original_title=title,
        lines=result.get(
            "article_title_lines"
        ),
        max_lines=3,
        field_name="article_title_lines",
    )

    card_lines = validate_title_lines(
        original_title=title,
        lines=result.get(
            "card_title_lines"
        ),
        max_lines=3,
        field_name="card_title_lines",
    )

    print()
    print(
        "[Title Layout] Blog"
    )

    for line in blog_lines:
        print(
            f"  {line}"
        )

    print()
    print(
        "[Title Layout] Instagram"
    )

    for line in instagram_lines:
        print(
            f"  {line}"
        )

    print()
    print(
        "[Title Layout] Article"
    )

    for line in article_lines:
        print(
            f"  {line}"
        )

    print()
    print(
        "[Title Layout] Card"
    )

    for line in card_lines:
        print(
            f"  {line}"
        )

    print()

    return {
        "blog_title_lines":
            blog_lines,
        "instagram_title_lines":
            instagram_lines,
        "article_title_lines":
            article_lines,
        "card_title_lines":
            card_lines,
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
    article_title_lines: list[str],
    card_title_lines: list[str],
) -> None:
    """
    MDX frontmatterへ

    ・新しいBlog画像
    ・個別記事用タイトル改行
    ・カード用タイトル改行

    を反映する。
    """

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
    # 既存titleLines/cardTitleLinesを削除
    # -----------------------------------------------------

    frontmatter = remove_frontmatter_array(
        frontmatter,
        "titleLines",
    )

    frontmatter = remove_frontmatter_array(
        frontmatter,
        "cardTitleLines",
    )

    # -----------------------------------------------------
    # titleの直後へ追加
    # -----------------------------------------------------

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

    title_lines_yaml = build_yaml_string_array(
        "titleLines",
        article_title_lines,
    )

    card_lines_yaml = build_yaml_string_array(
        "cardTitleLines",
        card_title_lines,
    )

    insertion = (
        title_match.group(1)
        + "\n"
        + title_lines_yaml
        + "\n"
        + card_lines_yaml
    )

    frontmatter = title_pattern.sub(
        lambda _: insertion,
        frontmatter,
        count=1,
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
        "  cardTitleLines："
        + " / ".join(
            card_title_lines
        )
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
    2. AIタイトル改行
    3. Blog画像生成
    4. Instagram画像生成
    5. MDX frontmatter更新

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
    # AIで4種類の改行を決定
    # -----------------------------------------------------

    title_layout = generate_title_layout(
        image_article
    )

    # 画像生成エンジンが使用する2種類
    image_article[
        "blog_title_lines"
    ] = title_layout[
        "blog_title_lines"
    ]

    image_article[
        "instagram_title_lines"
    ] = title_layout[
        "instagram_title_lines"
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
        article_title_lines=title_layout[
            "article_title_lines"
        ],
        card_title_lines=title_layout[
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