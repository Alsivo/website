import json
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
from engines.affiliate_registry import (
    build_affiliate_section,
    load_affiliate_registry,
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
    used_source_ids: list[str] | None = None,
) -> str:
    """
    本文中の[S1]形式の引用をリンクへ変換し、
    実際に本文で使われた出典だけを参考情報へ追加する。

    used_source_idsは既存コードとの互換性のため受け取るが、
    出典判定には使用しない。
    """

    sources = research.get("sources")

    if not isinstance(sources, list) or not sources:
        raise ValueError(
            "記事に利用できる出典情報がありません。"
        )

    source_map: dict[str, dict[str, str]] = {}

    for source in sources:
        if not isinstance(source, dict):
            continue

        source_id = str(
            source.get("id", "")
        ).strip()

        title = str(
            source.get("title", "")
        ).strip()

        url = str(
            source.get("url", "")
        ).strip()

        if source_id and title and url:
            source_map[source_id] = {
                "title": title,
                "url": url,
            }

    # 本文とFAQで実際に使われた出典IDを抽出
    marker_ids = set(
        re.findall(
            r"\[(S\d+)\]",
            content,
        )
    )

    if not marker_ids:
        raise ValueError(
            "本文またはFAQに出典IDがありません。"
        )

    # S1、S2、S10のように数字順へ並べる
    ordered_source_ids = sorted(
        marker_ids,
        key=lambda source_id: int(
            source_id[1:]
        ),
    )

    # Researcherが取得していないIDが本文にないか確認
    unknown_ids = [
        source_id
        for source_id in ordered_source_ids
        if source_id not in source_map
    ]

    if unknown_ids:
        raise ValueError(
            "本文またはFAQに存在しない出典IDがあります："
            + ", ".join(unknown_ids)
        )

    # [S1]を[[1]](URL)へ変換
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

    recommended_tools = article.get(
        "recommended_tools"
    )

    if not isinstance(
        recommended_tools,
        list,
    ):
        raise ValueError(
            "recommended_toolsは配列で指定してください。"
        )

    if len(recommended_tools) > 5:
        raise ValueError(
            "recommended_toolsは最大5件です。"
        )

    if not all(
        isinstance(tool_name, str)
        and tool_name.strip()
        for tool_name in recommended_tools
    ):
        raise ValueError(
            "recommended_toolsに不正な値があります。"
        )

    cleaned_recommended_tools = list(
        dict.fromkeys(
            tool_name.strip()
            for tool_name in recommended_tools
        )
    )

    registry = load_affiliate_registry()

    unknown_tools = [
        tool_name
        for tool_name in cleaned_recommended_tools
        if tool_name not in registry
    ]

    if unknown_tools:
        raise ValueError(
            "リンク台帳に存在しないサービスがあります："
            + ", ".join(unknown_tools)
        )

    article[
        "recommended_tools"
    ] = cleaned_recommended_tools

def publish_article(
    article: dict[str, Any],
    research: dict[str, Any],
    original_date: str | None = None,
    is_rewrite: bool = False,
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

    # 本文を準備する
    full_content = article["content"].strip()

    # 記事で紹介したサービスのCTAを追加する
    affiliate_section = build_affiliate_section(
        article["recommended_tools"]
    )

    if affiliate_section:
        full_content += (
            "\n"
            + affiliate_section
        )

    # CTAの後ろへFAQを追加する
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

    faq_frontmatter = []

    for item in faq_items:
        question = item["question"].strip()
        answer = item["answer"].strip()

        # JSON-LD用データには[S1]などの内部IDを残さない
        clean_answer = re.sub(
            r"\[S\d+\]",
            "",
            answer,
        ).strip()

        faq_frontmatter.append(
            {
                "question": question,
                "answer": clean_answer,
            }
        )

    faq_json = json.dumps(
        faq_frontmatter,
        ensure_ascii=False,
    )

    published_date = (
        original_date
        if original_date
        else date.today().isoformat()
    )

    updated_date = (
        date.today().isoformat()
        if is_rewrite
        else ""
    )

    # reading_timeを作った後でfrontmatterを作る
    frontmatter_lines = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        f'date: "{published_date}"',
    ]

    if updated_date:
        frontmatter_lines.append(
            f'updated: "{updated_date}"'
        )

    frontmatter_lines.extend(
        [
            f'category: "{category}"',
            f'image: "{image}"',
            f'readingTime: "{reading_time}"',
            f"faq: {faq_json}",
            "tags:",
        ]
    )

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
    )

    mdx = "\n".join(frontmatter_lines)
    mdx += cited_content

    filepath.write_text(
        mdx,
        encoding="utf-8",
    )

    return filepath