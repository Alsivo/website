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

def escape_markdown_text(value: str) -> str:
    """Markdownリンクの表示文字列を安全にする。"""

    return (
        value.replace("[", "\\[")
        .replace("]", "\\]")
        .strip()
    )


def apply_source_citations(
    content: str,
    research: dict[str, Any],
    used_source_ids: list[str],
) -> str:
    """[S1]形式の引用をリンクへ変換し、参考情報を追加する。"""

    sources = research.get("sources")

    if not isinstance(sources, list) or not sources:
        raise ValueError(
            "記事に利用できる出典情報がありません。"
        )

    source_map: dict[str, dict[str, str]] = {}

    for source in sources:
        if not isinstance(source, dict):
            continue

        source_id = str(source.get("id", "")).strip()
        title = str(source.get("title", "")).strip()
        url = str(source.get("url", "")).strip()

        if source_id and title and url:
            source_map[source_id] = {
                "title": title,
                "url": url,
            }

    cleaned_source_ids = [
        source_id.strip()
        for source_id in used_source_ids
        if isinstance(source_id, str)
        and source_id.strip()
    ]

    if not cleaned_source_ids:
        raise ValueError(
            "used_source_idsが未入力です。"
        )

    unknown_ids = [
        source_id
        for source_id in cleaned_source_ids
        if source_id not in source_map
    ]

    if unknown_ids:
        raise ValueError(
            "存在しない出典IDが指定されています："
            + ", ".join(unknown_ids)
        )

    marker_ids = set(
        re.findall(
            r"\[(S\d+)\]",
            content,
        )
    )

    undeclared_ids = sorted(
        marker_ids - set(cleaned_source_ids)
    )

    if undeclared_ids:
        raise ValueError(
            "本文中の出典IDがused_source_idsにありません："
            + ", ".join(undeclared_ids)
        )

    missing_markers = [
        source_id
        for source_id in cleaned_source_ids
        if source_id not in marker_ids
    ]

    if missing_markers:
        raise ValueError(
            "used_source_idsの出典が本文中で使われていません："
            + ", ".join(missing_markers)
        )

    ordered_source_ids = list(
        dict.fromkeys(cleaned_source_ids)
    )

    for index, source_id in enumerate(
        ordered_source_ids,
        start=1,
    ):
        source = source_map[source_id]
        citation_link = (
            f"[[{index}]]({source['url']})"
        )

        content = content.replace(
            f"[{source_id}]",
            citation_link,
        )

    reference_lines = [
        "",
        "## 参考情報",
        "",
    ]

    for index, source_id in enumerate(
        ordered_source_ids,
        start=1,
    ):
        source = source_map[source_id]
        title = escape_markdown_text(
            source["title"]
        )

        reference_lines.append(
            f"{index}. [{title}]({source['url']})"
        )

    return (
        content.rstrip()
        + "\n"
        + "\n".join(reference_lines)
        + "\n"
    )

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
        "image",
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

    used_source_ids = article.get(
        "used_source_ids"
    )

    if (
        not isinstance(used_source_ids, list)
        or not used_source_ids
    ):
        raise ValueError(
            "記事データのused_source_idsが未入力です。"
        )

    if not all(
        isinstance(source_id, str)
        and source_id.strip()
        for source_id in used_source_ids
    ):
        raise ValueError(
            "used_source_idsに不正な値があります。"
        )

    faq_items = article.get("faq")

    if not isinstance(faq_items, list):
        raise ValueError(
            "記事データの「faq」は配列で指定してください。"
        )

    if not 3 <= len(faq_items) <= 5:
        raise ValueError(
            "FAQは3件以上5件以下にしてください。"
        )

    for index, item in enumerate(
        faq_items,
        start=1,
    ):
        if not isinstance(item, dict):
            raise ValueError(
                f"FAQの{index}件目の形式が不正です。"
            )

        question = item.get("question")
        answer = item.get("answer")

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                f"FAQの{index}件目の質問が未入力です。"
            )

        if (
            not isinstance(answer, str)
            or not answer.strip()
        ):
            raise ValueError(
                f"FAQの{index}件目の回答が未入力です。"
            )

def publish_article(
    article: dict[str, Any],
    research: dict[str, Any],
) -> Path:
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
    image = escape_yaml_string(
        article["image"]
    )

    # 本文とFAQを先にまとめる
    full_content = article["content"].strip()

    faq_items = article["faq"]

    full_content += "\n\n## よくある質問\n"

    for item in faq_items:
        question = item["question"].strip()
        answer = item["answer"].strip()

        full_content += (
            f"\n### {question}\n\n"
            f"{answer}\n"
        )

    # FAQを含めた全文から読了時間を計算
    reading_time = calculate_reading_time(
        full_content
    )

    # reading_timeを作った後でfrontmatterを作る
    frontmatter_lines = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        f'date: "{date.today().isoformat()}"',
        f'category: "{category}"',
        f'image: "{image}"',
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

    # 本文とFAQ内の出典IDをリンクへ変換
    cited_content = apply_source_citations(
        content=full_content,
        research=research,
        used_source_ids=article[
            "used_source_ids"
        ],
    )

    mdx = "\n".join(frontmatter_lines)
    mdx += cited_content

    filepath.write_text(
        mdx,
        encoding="utf-8",
    )

    return filepath