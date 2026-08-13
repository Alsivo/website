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
    本文中の[S1]形式の出典マーカーを削除し、
    実際に使用された出典だけを記事末尾の
    「参考情報」にまとめる。
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

    marker_ids = set(
        re.findall(
            r"\[(S\d+)\]",
            content,
        )
    )

    if used_source_ids:
        marker_ids.update(
            source_id
            for source_id in used_source_ids
            if source_id
        )

    if not marker_ids:
        raise ValueError(
            "本文またはFAQに出典IDがありません。"
        )

    ordered_source_ids = sorted(
        marker_ids,
        key=lambda source_id: int(
            source_id[1:]
        ),
    )

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

    # 公開本文では出典番号を表示しない
    content = re.sub(
        r"\s*\[S\d+\]",
        "",
        content,
    )

    reference_lines = [
        "",
        "## 参考情報",
        "",
        "この記事の作成・確認に使用した主な情報源です。",
        "",
    ]

    for source_id in ordered_source_ids:
        source = source_map[source_id]

        title = escape_markdown_text(
            source["title"]
        )

        reference_lines.append(
            f"- [{title}]({source['url']})"
        )

    return (
        content.rstrip()
        + "\n\n"
        + "\n".join(reference_lines)
        + "\n"
    )


def escape_markdown_table_cell(
    value: str,
) -> str:
    """Markdown表セル用に文字列を安全にする。"""

    return (
        value.replace("|", "\\|")
        .replace("\n", " ")
        .strip()
    )


def build_comparison_table(
    comparison_table: dict[str, Any] | None,
) -> str:
    """比較表データをMarkdown表へ変換する。"""

    if comparison_table is None:
        return ""

    if not isinstance(
        comparison_table,
        dict,
    ):
        raise ValueError(
            "comparison_tableの形式が不正です。"
        )

    title = str(
        comparison_table.get(
            "title",
            "",
        )
    ).strip()

    columns = comparison_table.get(
        "columns",
        [],
    )

    rows = comparison_table.get(
        "rows",
        [],
    )

    if (
        not title
        or not isinstance(columns, list)
        or len(columns) < 2
        or not isinstance(rows, list)
        or not rows
    ):
        raise ValueError(
            "comparison_tableの内容が不足しています。"
        )

    cleaned_columns = [
        escape_markdown_table_cell(
            str(column)
        )
        for column in columns
    ]

    lines = [
        f"## {title}",
        "",
        "| 比較項目 | "
        + " | ".join(
            cleaned_columns
        )
        + " |",
        "| --- | "
        + " | ".join(
            "---"
            for _ in cleaned_columns
        )
        + " |",
    ]

    for index, row in enumerate(
        rows,
        start=1,
    ):
        if not isinstance(row, dict):
            raise ValueError(
                f"comparison_tableの"
                f"{index}行目が不正です。"
            )

        label = (
            escape_markdown_table_cell(
                str(
                    row.get(
                        "label",
                        "",
                    )
                )
            )
        )

        values = row.get(
            "values",
            [],
        )

        if (
            not label
            or not isinstance(
                values,
                list,
            )
            or len(values)
            != len(cleaned_columns)
        ):
            raise ValueError(
                "comparison_tableの列数が"
                f"一致していません：{index}行目"
            )

        cleaned_values = [
            escape_markdown_table_cell(
                str(value)
            )
            for value in values
        ]

        lines.append(
            "| "
            + label
            + " | "
            + " | ".join(
                cleaned_values
            )
            + " |"
        )

    return "\n".join(lines)


def insert_before_summary(
    content: str,
    section: str,
) -> tuple[str, bool]:
    """
    「まとめ」系H2の直前へsectionを挿入する。
    見つからない場合は本文末尾へ追加する。
    """

    if not section:
        return content, False

    summary_headings = [
        "## まとめ",
        "## 結論",
        "## 最後に",
        "## さいごに",
    ]

    for heading in summary_headings:
        if heading not in content:
            continue

        before, after = content.split(
            heading,
            1,
        )

        updated_content = (
            before.rstrip()
            + "\n\n"
            + section.strip()
            + "\n\n"
            + heading
            + after
        )

        return updated_content, True

    return (
        content.rstrip()
        + "\n\n"
        + section.strip(),
        False,
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

    comparison_table = article.get(
        "comparison_table"
    )

    cta_plan = article.get(
        "cta_plan"
    )

    if not isinstance(
        cta_plan,
        dict,
    ):
        raise ValueError(
            "cta_planはオブジェクトにしてください。"
        )

    primary_service = cta_plan.get(
        "primary_service"
    )

    placement = cta_plan.get(
        "placement"
    )

    cta_label = cta_plan.get(
        "cta_label"
    )

    reason = cta_plan.get(
        "reason"
    )

    if (
        primary_service is not None
        and (
            not isinstance(
                primary_service,
                str,
            )
            or not primary_service.strip()
        )
    ):
        raise ValueError(
            "cta_planのprimary_serviceが不正です。"
        )

    if placement not in {
        "after_toc",
        "after_comparison",
        "before_faq",
    }:
        raise ValueError(
            "cta_planのplacementが不正です。"
        )

    if (
        cta_label is not None
        and (
            not isinstance(
                cta_label,
                str,
            )
            or not cta_label.strip()
        )
    ):
        raise ValueError(
            "cta_planのcta_labelが不正です。"
        )

    if (
        not isinstance(reason, str)
        or not reason.strip()
    ):
        raise ValueError(
            "cta_planのreasonが未入力です。"
        )

    recommended_tools = article.get(
        "recommended_tools",
        [],
    )

    if (
        primary_service is not None
        and primary_service
        not in recommended_tools
    ):
        raise ValueError(
            "cta_planのprimary_serviceは"
            "recommended_toolsに含まれる"
            "サービスを指定してください。"
        )

    comparison_table = article.get(
        "comparison_table"
    )

    if (
        placement == "after_comparison"
        and comparison_table is None
    ):
        raise ValueError(
            "comparison_tableがない記事では"
            "after_comparisonを指定できません。"
        )

    if (
        primary_service is None
        and cta_label is not None
    ):
        raise ValueError(
            "primary_serviceがnullの場合は"
            "cta_labelもnullにしてください。"
        )

    if (
        primary_service is not None
        and cta_label is None
    ):
        raise ValueError(
            "primary_serviceを設定する場合は"
            "cta_labelも設定してください。"
        )

    if comparison_table is not None:
        if not isinstance(
            comparison_table,
            dict,
        ):
            raise ValueError(
                "comparison_tableは"
                "オブジェクトまたはnullにしてください。"
            )

        title = comparison_table.get(
            "title"
        )

        columns = comparison_table.get(
            "columns"
        )

        rows = comparison_table.get(
            "rows"
        )

        if (
            not isinstance(title, str)
            or not title.strip()
        ):
            raise ValueError(
                "comparison_tableのtitleが"
                "未入力です。"
            )

        if (
            not isinstance(columns, list)
            or not 2 <= len(columns) <= 8
        ):
            raise ValueError(
                "comparison_tableのcolumnsは"
                "2件以上8件以下にしてください。"
            )

        if not all(
            isinstance(column, str)
            and column.strip()
            for column in columns
        ):
            raise ValueError(
                "comparison_tableのcolumnsに"
                "空欄または不正な値があります。"
            )

        if (
            not isinstance(rows, list)
            or not 2 <= len(rows) <= 12
        ):
            raise ValueError(
                "comparison_tableのrowsは"
                "2件以上12件以下にしてください。"
            )

        for index, row in enumerate(
            rows,
            start=1,
        ):
            if not isinstance(
                row,
                dict,
            ):
                raise ValueError(
                    f"比較表の{index}行目の"
                    "形式が不正です。"
                )

            label = row.get(
                "label"
            )

            values = row.get(
                "values"
            )

            if (
                not isinstance(label, str)
                or not label.strip()
            ):
                raise ValueError(
                    f"比較表の{index}行目の"
                    "labelが未入力です。"
                )

            if (
                not isinstance(values, list)
                or len(values)
                != len(columns)
            ):
                raise ValueError(
                    f"比較表の{index}行目の"
                    "values数とcolumns数が"
                    "一致していません。"
                )

            if not all(
                isinstance(value, str)
                and value.strip()
                for value in values
            ):
                raise ValueError(
                    f"比較表の{index}行目に"
                    "空欄または不正な値があります。"
                )

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

    # CTA Planを取得する
    cta_plan = article.get(
        "cta_plan",
        {},
    )

    placement = str(
        cta_plan.get(
            "placement",
            "before_faq",
        )
    ).strip()

    # 比較表を作成する
    comparison_section = (
        build_comparison_table(
            article.get(
                "comparison_table"
            )
        )
    )

    # CTAを作成する
    affiliate_section = (
        build_affiliate_section(
            article["recommended_tools"],
            cta_plan,
        )
    )

    # ========================================================
    # after_comparison
    # 比較表 → CTA → まとめ
    # ========================================================

    if (
        placement == "after_comparison"
        and comparison_section
    ):
        combined_section = (
            comparison_section
        )

        if affiliate_section:
            combined_section += (
                "\n\n"
                + affiliate_section.strip()
            )

        full_content, _ = (
            insert_before_summary(
                full_content,
                combined_section,
            )
        )

    # ========================================================
    # before_faq
    # 比較表 → まとめ → CTA → FAQ
    # ========================================================

    else:
        if comparison_section:
            full_content, _ = (
                insert_before_summary(
                    full_content,
                    comparison_section,
                )
            )

        if affiliate_section:
            full_content += (
                "\n\n"
                + affiliate_section.strip()
            )

    # FAQを追加する
    faq_items = article["faq"]

    full_content += (
        "\n\n## よくある質問\n"
    )

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

    verified_date = date.today().isoformat()

    # reading_timeを作った後でfrontmatterを作る
    frontmatter_lines = [
        "---",
        f'title: "{title}"',
        f'description: "{description}"',
        f'date: "{published_date}"',
        f'verified: "{verified_date}"',
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
        used_source_ids=article.get(
            "used_source_ids",
            [],
        ),
    )

    mdx = "\n".join(frontmatter_lines)
    mdx += cited_content

    filepath.write_text(
        mdx,
        encoding="utf-8",
    )

    return filepath