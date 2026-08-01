import math
import re
from datetime import date
from pathlib import Path
from typing import Any

from config import (
    CATEGORIES,
    CORE_TAGS,
    MAX_NEW_TAGS,
    MAX_TAGS,
    MIN_TAGS,
)

BLOG_DIR = Path("../content/blog")


def escape_yaml_string(value: str) -> str:
    """YAMLのダブルクォート内で使えるように文字列を処理する。"""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def calculate_reading_time(content: str) -> str:
    """Markdown記号を除いた本文文字数から読了時間を計算する。"""

    plain_text = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    plain_text = re.sub(r"`[^`]*`", "", plain_text)
    plain_text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", plain_text)
    plain_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain_text)
    plain_text = re.sub(r"[#>*_\-\n\r]", "", plain_text)

    character_count = len(plain_text.strip())

    # 日本語は1分あたり約600文字として計算
    minutes = max(
        1,
        math.ceil(character_count / 600),
    )

    return f"{minutes} min read"


def validate_article(article: dict[str, Any]) -> None:
    """Publisherが必要とする記事データを確認する。"""

    required_string_fields = [
        "title",
        "description",
        "slug",
        "category",
        "content",
    ]

    for field in required_string_fields:
        value = article.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"記事データの「{field}」が未入力です。"
            )

    category = article["category"].strip()

    if category not in CATEGORIES:
        allowed_categories = ", ".join(CATEGORIES)

        raise ValueError(
            "記事データのカテゴリーが許可されていません。"
            f"カテゴリー：{category} / "
            f"使用可能：{allowed_categories}"
        )

    tags = article.get("tags")

    if not isinstance(tags, list):
        raise ValueError(
            "記事データの「tags」は配列で指定してください。"
        )

    cleaned_tags = [
        tag.strip()
        for tag in tags
        if isinstance(tag, str) and tag.strip()
    ]

    if len(cleaned_tags) != len(tags):
        raise ValueError(
            "記事データの「tags」に空欄または不正な値があります。"
        )

    if len(set(cleaned_tags)) != len(cleaned_tags):
        raise ValueError(
            "記事データの「tags」に重複があります。"
        )

    if not MIN_TAGS <= len(cleaned_tags) <= MAX_TAGS:
        raise ValueError(
            f"タグ数は{MIN_TAGS}個以上"
            f"{MAX_TAGS}個以下にしてください。"
        )

    new_tags = [
        tag
        for tag in cleaned_tags
        if tag not in CORE_TAGS
    ]

    if len(new_tags) > MAX_NEW_TAGS:
        raise ValueError(
            "共通タグに存在しない新規タグが多すぎます。"
            f"新規タグ：{', '.join(new_tags)} / "
            f"最大{MAX_NEW_TAGS}個"
        )

    article["tags"] = cleaned_tags


def publish_article(article: dict[str, Any]) -> Path:
    """記事データをMDXファイルとして保存する。"""

    validate_article(article)

    BLOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    slug = article["slug"].strip().lower()
    filepath = BLOG_DIR / f"{slug}.mdx"

    title = escape_yaml_string(article["title"])
    description = escape_yaml_string(article["description"])
    category = escape_yaml_string(article["category"])
    reading_time = calculate_reading_time(article["content"])

    frontmatter_lines = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        f'date: "{date.today().isoformat()}"',
        f'category: "{category}"',
        f'readingTime: "{reading_time}"',
        "tags:",
    ]

    for tag in article["tags"]:
        escaped_tag = escape_yaml_string(tag)
        frontmatter_lines.append(
            f'  - "{escaped_tag}"'
        )

    frontmatter_lines.extend(
        [
            "published: true",
            "---",
            "",
        ]
    )

    mdx = "\n".join(frontmatter_lines)
    mdx += article["content"].strip()
    mdx += "\n"

    filepath.write_text(
        mdx,
        encoding="utf-8",
    )

    return filepath