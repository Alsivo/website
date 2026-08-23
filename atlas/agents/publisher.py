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
from engines.a8_submission_export import (
    export_a8_submission_csv,
)


BLOG_DIR = Path("../content/blog")


# =========================================================
# Basic escaping
# =========================================================

def escape_yaml_string(
    value: str,
) -> str:
    """YAMLのダブルクォート内で使えるように文字列を処理する。"""

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


def escape_markdown_text(
    value: str,
) -> str:
    """Markdownリンクの表示文字列を安全にする。"""

    return (
        value
        .replace(
            "[",
            "\\[",
        )
        .replace(
            "]",
            "\\]",
        )
        .strip()
    )


# =========================================================
# MDX safety
# =========================================================

def escape_mdx_placeholders(
    content: str,
) -> str:
    """
    MDXでJavaScript式やJSXタグとして誤認される
    プレースホルダーを安全化する。

    対応例：

    <<TEXT>>
    ↓
    &lt;&lt;TEXT&gt;&gt;

    {タイトル}
    ↓
    &#123;タイトル&#125;

    {章/ページ範囲}
    ↓
    &#123;章/ページ範囲&#125;

    fenced code block と inline code 内は変更しない。
    """

    angle_placeholder_pattern = re.compile(
        r"<<([^<>\r\n]{1,200})>>"
    )

    brace_placeholder_pattern = re.compile(
        r"\{([^{}\r\n]{1,300})\}"
    )

    def escape_segment(
        value: str,
    ) -> str:

        value = angle_placeholder_pattern.sub(
            lambda match: (
                "&lt;&lt;"
                + match.group(1)
                + "&gt;&gt;"
            ),
            value,
        )

        value = brace_placeholder_pattern.sub(
            lambda match: (
                "&#123;"
                + match.group(1)
                + "&#125;"
            ),
            value,
        )

        return value

    lines = content.splitlines(
        keepends=True,
    )

    result: list[str] = []

    in_fenced_code = False
    fence_marker = ""

    for line in lines:

        stripped = line.lstrip()

        # -------------------------------------------------
        # fenced code block
        # -------------------------------------------------

        if stripped.startswith(
            "```"
        ):

            marker = "```"

            if not in_fenced_code:

                in_fenced_code = True
                fence_marker = marker

            elif fence_marker == marker:

                in_fenced_code = False
                fence_marker = ""

            result.append(
                line
            )

            continue

        if stripped.startswith(
            "~~~"
        ):

            marker = "~~~"

            if not in_fenced_code:

                in_fenced_code = True
                fence_marker = marker

            elif fence_marker == marker:

                in_fenced_code = False
                fence_marker = ""

            result.append(
                line
            )

            continue

        if in_fenced_code:

            result.append(
                line
            )

            continue

        # -------------------------------------------------
        # inline code `...` の外側だけ処理
        # -------------------------------------------------

        parts = line.split(
            "`"
        )

        for index in range(
            0,
            len(parts),
            2,
        ):

            parts[index] = (
                escape_segment(
                    parts[index]
                )
            )

        result.append(
            "`".join(
                parts
            )
        )

    return "".join(
        result
    )


def remove_existing_affiliate_links(
    content: str,
) -> str:
    """
    AI本文に紛れ込んだAffiliateLinkを除去する。

    CTAはPublisherがcta_planを基に
    一元生成するため、本文側のAffiliateLinkは削除する。
    """

    pattern = re.compile(
        r"""
        <AffiliateLink
        \b[^>]*>
        .*?
        </AffiliateLink>
        """,
        flags=(
            re.DOTALL
            | re.VERBOSE
        ),
    )

    cleaned = pattern.sub(
        "",
        content,
    )

    cleaned = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned,
    )

    return cleaned.strip()


# =========================================================
# Source marker helpers
# =========================================================

SOURCE_MARKER_PATTERN = re.compile(
    r"""
    (?:
        \[
            \s*
            S\d+
            (?:
                \s*[,、]\s*S\d+
            )*
            \s*
        \]
        |
        ［
            \s*
            S\d+
            (?:
                \s*[,、]\s*S\d+
            )*
            \s*
        ］
    )
    """,
    flags=re.VERBOSE | re.IGNORECASE,
)


SINGLE_SOURCE_ID_PATTERN = re.compile(
    r"S\d+",
    flags=re.IGNORECASE,
)


def extract_source_ids(
    content: str,
) -> set[str]:
    """
    本文から内部出典IDを抽出する。

    対応例：

    [S1]
    [S1][S2]
    [S1, S2]
    [S1、S2]
    ［S1］
    ［S1, S2］
    """

    source_ids: set[str] = set()

    for marker_match in SOURCE_MARKER_PATTERN.finditer(
        content
    ):

        marker_text = (
            marker_match.group(0)
        )

        for source_match in (
            SINGLE_SOURCE_ID_PATTERN.finditer(
                marker_text
            )
        ):

            source_ids.add(
                source_match
                .group(0)
                .upper()
            )

    return source_ids


def remove_source_markers(
    content: str,
) -> str:
    """
    公開文章から内部用出典IDをすべて除去する。
    """

    cleaned = SOURCE_MARKER_PATTERN.sub(
        "",
        content,
    )

    cleaned = re.sub(
        r"[ \t]+([。、，．！？!?：:；;])",
        r"\1",
        cleaned,
    )

    cleaned = re.sub(
        r"([（(\[])[ \t]+",
        r"\1",
        cleaned,
    )

    cleaned = re.sub(
        r"[ \t]+([）)\]])",
        r"\1",
        cleaned,
    )

    cleaned = re.sub(
        r"[ \t]{2,}",
        " ",
        cleaned,
    )

    return cleaned


def assert_no_source_markers(
    content: str,
) -> None:
    """
    公開直前の最終安全チェック。
    """

    remaining_ids = (
        extract_source_ids(
            content
        )
    )

    if remaining_ids:

        ordered_ids = sorted(
            remaining_ids,
            key=lambda source_id: int(
                source_id[1:]
            ),
        )

        raise ValueError(
            "公開用MDXに内部出典IDが残っています："
            + ", ".join(
                ordered_ids
            )
        )


# =========================================================
# Sources
# =========================================================

def apply_source_citations(
    content: str,
    research: dict[str, Any],
    used_source_ids: list[str] | None = None,
) -> str:
    """
    本文中の[S1]形式の内部出典マーカーを削除し、
    実際に使用された出典だけを記事末尾の
    「参考情報」にまとめる。
    """

    sources = research.get(
        "sources"
    )

    if (
        not isinstance(
            sources,
            list,
        )
        or not sources
    ):

        raise ValueError(
            "記事に利用できる"
            "出典情報がありません。"
        )

    source_map: dict[
        str,
        dict[str, str],
    ] = {}

    for source in sources:

        if not isinstance(
            source,
            dict,
        ):

            continue

        source_id = (
            str(
                source.get(
                    "id",
                    "",
                )
            )
            .strip()
            .upper()
        )

        title = str(
            source.get(
                "title",
                "",
            )
        ).strip()

        url = str(
            source.get(
                "url",
                "",
            )
        ).strip()

        if (
            source_id
            and title
            and url
        ):

            source_map[
                source_id
            ] = {
                "title":
                    title,
                "url":
                    url,
            }

    marker_ids = (
        extract_source_ids(
            content
        )
    )

    if used_source_ids:

        for source_id in (
            used_source_ids
        ):

            cleaned_source_id = (
                str(
                    source_id
                )
                .strip()
                .upper()
            )

            if cleaned_source_id:

                marker_ids.add(
                    cleaned_source_id
                )

    if not marker_ids:

        raise ValueError(
            "本文、FAQ、比較表のいずれにも"
            "出典IDがありません。"
        )

    ordered_source_ids = sorted(
        marker_ids,
        key=lambda source_id: int(
            source_id[1:]
        ),
    )

    unknown_ids = [
        source_id
        for source_id
        in ordered_source_ids
        if source_id
        not in source_map
    ]

    if unknown_ids:

        raise ValueError(
            "本文、FAQ、比較表に"
            "存在しない出典IDがあります："
            + ", ".join(
                unknown_ids
            )
        )

    content = (
        remove_source_markers(
            content
        )
    )

    reference_lines = [
        "",
        "## 参考情報",
        "",
        "この記事の作成・確認に使用した主な情報源です。",
        "",
    ]

    for source_id in ordered_source_ids:

        source = source_map[
            source_id
        ]

        title = (
            escape_markdown_text(
                source[
                    "title"
                ]
            )
        )

        reference_lines.append(
            f"- [{title}]"
            f"({source['url']})"
        )

    result = (
        content.rstrip()
        + "\n\n"
        + "\n".join(
            reference_lines
        )
        + "\n"
    )

    assert_no_source_markers(
        result
    )

    return result


# =========================================================
# Comparison table
# =========================================================

def escape_markdown_table_cell(
    value: str,
) -> str:
    """Markdown表セル用に文字列を安全にする。"""

    return (
        value
        .replace(
            "|",
            "\\|",
        )
        .replace(
            "\n",
            " ",
        )
        .strip()
    )


def normalize_comparison_table(
    comparison_table: Any,
) -> dict[str, Any] | None:
    """
    AIが生成したcomparison_tableを
    Publisherへ渡す前に安全に補正する。
    """

    if comparison_table is None:
        return None

    if not isinstance(
        comparison_table,
        dict,
    ):

        print(
            "[Publisher] WARNING: "
            "comparison_tableの形式が不正なため、"
            "比較表をスキップします。"
        )

        return None

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
        or not isinstance(
            columns,
            list,
        )
        or not 2
        <= len(columns)
        <= 8
        or not isinstance(
            rows,
            list,
        )
        or not 2
        <= len(rows)
        <= 12
    ):

        print(
            "[Publisher] WARNING: "
            "comparison_tableの基本構造が不正なため、"
            "比較表をスキップします。"
        )

        return None

    cleaned_columns = [
        str(
            column
        ).strip()
        for column in columns
    ]

    if not all(
        cleaned_columns
    ):

        print(
            "[Publisher] WARNING: "
            "comparison_tableのcolumnsに空欄があるため、"
            "比較表をスキップします。"
        )

        return None

    expected_count = len(
        cleaned_columns
    )

    cleaned_rows: list[
        dict[str, Any]
    ] = []

    for index, row in enumerate(
        rows,
        start=1,
    ):

        if not isinstance(
            row,
            dict,
        ):

            print(
                "[Publisher] WARNING: "
                f"比較表の{index}行目が不正なため、"
                "比較表をスキップします。"
            )

            return None

        label = str(
            row.get(
                "label",
                "",
            )
        ).strip()

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
        ):

            print(
                "[Publisher] WARNING: "
                f"比較表の{index}行目の"
                "labelまたはvaluesが不正なため、"
                "比較表をスキップします。"
            )

            return None

        cleaned_values = [
            str(
                value
            ).strip()
            for value in values
        ]

        if (
            len(
                cleaned_values
            )
            == expected_count + 1
            and cleaned_values[0]
            == label
        ):

            print(
                "[Publisher] "
                f"比較表の{index}行目で"
                "labelがvalues先頭へ重複していたため"
                "自動補正しました。"
            )

            cleaned_values = (
                cleaned_values[
                    1:
                ]
            )

        if (
            len(
                cleaned_values
            )
            != expected_count
        ):

            print(
                "[Publisher] WARNING: "
                f"比較表の{index}行目で"
                f"columns={expected_count}件に対して"
                f"values={len(cleaned_values)}件でした。"
            )

            print(
                "[Publisher] WARNING: "
                "安全に自動補正できないため、"
                "比較表のみスキップして"
                "記事公開を継続します。"
            )

            return None

        if not all(
            cleaned_values
        ):

            print(
                "[Publisher] WARNING: "
                f"比較表の{index}行目に"
                "空欄があるため、"
                "比較表をスキップします。"
            )

            return None

        cleaned_rows.append(
            {
                "label":
                    label,
                "values":
                    cleaned_values,
            }
        )

    return {
        "title":
            title,
        "columns":
            cleaned_columns,
        "rows":
            cleaned_rows,
    }


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
        or not isinstance(
            columns,
            list,
        )
        or len(
            columns
        ) < 2
        or not isinstance(
            rows,
            list,
        )
        or not rows
    ):

        raise ValueError(
            "comparison_tableの内容が不足しています。"
        )

    cleaned_columns = [
        escape_markdown_table_cell(
            str(
                column
            )
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

        if not isinstance(
            row,
            dict,
        ):

            raise ValueError(
                "comparison_tableの"
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
            or len(
                values
            )
            != len(
                cleaned_columns
            )
        ):

            raise ValueError(
                "comparison_tableの列数が"
                f"一致していません：{index}行目"
            )

        cleaned_values = [
            escape_markdown_table_cell(
                str(
                    value
                )
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

    return "\n".join(
        lines
    )


# =========================================================
# Content helpers
# =========================================================

def insert_before_summary(
    content: str,
    section: str,
) -> tuple[
    str,
    bool,
]:
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

        before, after = (
            content.split(
                heading,
                1,
            )
        )

        updated_content = (
            before.rstrip()
            + "\n\n"
            + section.strip()
            + "\n\n"
            + heading
            + after
        )

        return (
            updated_content,
            True,
        )

    return (
        content.rstrip()
        + "\n\n"
        + section.strip(),
        False,
    )


def calculate_reading_time(
    content: str,
) -> str:
    """Markdown記号を除いた本文文字数から読了時間を計算する。"""

    plain_text = re.sub(
        r"```.*?```",
        "",
        content,
        flags=re.DOTALL,
    )

    plain_text = re.sub(
        r"`[^`]*`",
        "",
        plain_text,
    )

    plain_text = re.sub(
        r"!\[[^\]]*\]\([^)]+\)",
        "",
        plain_text,
    )

    plain_text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        plain_text,
    )

    plain_text = (
        remove_source_markers(
            plain_text
        )
    )

    plain_text = re.sub(
        r"[#>*_\-\n\r]",
        "",
        plain_text,
    )

    character_count = len(
        plain_text.strip()
    )

    minutes = max(
        1,
        math.ceil(
            character_count
            / 600
        ),
    )

    return (
        f"{minutes} min read"
    )


# =========================================================
# Validation
# =========================================================

def validate_article(
    article: dict[str, Any],
) -> None:
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

        value = article.get(
            field
        )

        if (
            not isinstance(
                value,
                str,
            )
            or not value.strip()
        ):

            raise ValueError(
                f"記事データの「{field}」が"
                "未入力です。"
            )

    category = (
        article[
            "category"
        ].strip()
    )

    if category not in CATEGORIES:

        allowed_categories = (
            ", ".join(
                CATEGORIES
            )
        )

        raise ValueError(
            "記事データのカテゴリーが"
            "許可されていません。"
            f"カテゴリー：{category} / "
            f"使用可能：{allowed_categories}"
        )

    tags = article.get(
        "tags"
    )

    if not isinstance(
        tags,
        list,
    ):

        raise ValueError(
            "記事データの「tags」は"
            "配列で指定してください。"
        )

    cleaned_tags = [
        tag.strip()
        for tag in tags
        if (
            isinstance(
                tag,
                str,
            )
            and tag.strip()
        )
    ]

    if (
        len(
            cleaned_tags
        )
        != len(
            tags
        )
    ):

        raise ValueError(
            "記事データの「tags」に"
            "空欄または不正な値があります。"
        )

    if (
        len(
            set(
                cleaned_tags
            )
        )
        != len(
            cleaned_tags
        )
    ):

        raise ValueError(
            "記事データの「tags」に"
            "重複があります。"
        )

    if not (
        MIN_TAGS
        <= len(
            cleaned_tags
        )
        <= MAX_TAGS
    ):

        raise ValueError(
            f"タグ数は{MIN_TAGS}個以上"
            f"{MAX_TAGS}個以下にしてください。"
        )

    new_tags = [
        tag
        for tag in cleaned_tags
        if tag not in CORE_TAGS
    ]

    if (
        len(
            new_tags
        )
        > MAX_NEW_TAGS
    ):

        raise ValueError(
            "共通タグに存在しない"
            "新規タグが多すぎます。"
            f"新規タグ：{', '.join(new_tags)} / "
            f"最大{MAX_NEW_TAGS}個"
        )

    article[
        "tags"
    ] = cleaned_tags

    faq_items = article.get(
        "faq"
    )

    if not isinstance(
        faq_items,
        list,
    ):

        raise ValueError(
            "記事データの「faq」は"
            "配列で指定してください。"
        )

    if not (
        3
        <= len(
            faq_items
        )
        <= 5
    ):

        raise ValueError(
            "FAQは3件以上5件以下にしてください。"
        )

    for index, item in enumerate(
        faq_items,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):

            raise ValueError(
                f"FAQの{index}件目の"
                "形式が不正です。"
            )

        question = item.get(
            "question"
        )

        answer = item.get(
            "answer"
        )

        if (
            not isinstance(
                question,
                str,
            )
            or not question.strip()
        ):

            raise ValueError(
                f"FAQの{index}件目の"
                "質問が未入力です。"
            )

        if (
            not isinstance(
                answer,
                str,
            )
            or not answer.strip()
        ):

            raise ValueError(
                f"FAQの{index}件目の"
                "回答が未入力です。"
            )

    recommended_tools = (
        article.get(
            "recommended_tools"
        )
    )

    if not isinstance(
        recommended_tools,
        list,
    ):

        raise ValueError(
            "recommended_toolsは"
            "配列で指定してください。"
        )

    if (
        len(
            recommended_tools
        )
        > 5
    ):

        raise ValueError(
            "recommended_toolsは最大5件です。"
        )

    if not all(
        isinstance(
            tool_name,
            str,
        )
        and tool_name.strip()
        for tool_name
        in recommended_tools
    ):

        raise ValueError(
            "recommended_toolsに"
            "不正な値があります。"
        )

    cleaned_recommended_tools = list(
        dict.fromkeys(
            tool_name.strip()
            for tool_name
            in recommended_tools
        )
    )

    registry = (
        load_affiliate_registry()
    )

    unknown_tools = [
        tool_name
        for tool_name
        in cleaned_recommended_tools
        if tool_name
        not in registry
    ]

    if unknown_tools:

        raise ValueError(
            "リンク台帳に存在しない"
            "サービスがあります："
            + ", ".join(
                unknown_tools
            )
        )

    article[
        "recommended_tools"
    ] = (
        cleaned_recommended_tools
    )

    cta_plan = article.get(
        "cta_plan"
    )

    if not isinstance(
        cta_plan,
        dict,
    ):

        raise ValueError(
            "cta_planは"
            "オブジェクトにしてください。"
        )

    primary_service = (
        cta_plan.get(
            "primary_service"
        )
    )

    placement = (
        cta_plan.get(
            "placement"
        )
    )

    cta_label = (
        cta_plan.get(
            "cta_label"
        )
    )

    reason = (
        cta_plan.get(
            "reason"
        )
    )

    if (
        primary_service
        is not None
        and (
            not isinstance(
                primary_service,
                str,
            )
            or not primary_service.strip()
        )
    ):

        raise ValueError(
            "cta_planのprimary_serviceが"
            "不正です。"
        )

    if placement != "after_toc":

        raise ValueError(
            "cta_planのplacementは"
            "after_tocを指定してください。"
        )

    if (
        cta_label
        is not None
        and (
            not isinstance(
                cta_label,
                str,
            )
            or not cta_label.strip()
        )
    ):

        raise ValueError(
            "cta_planのcta_labelが"
            "不正です。"
        )

    if (
        not isinstance(
            reason,
            str,
        )
        or not reason.strip()
    ):

        raise ValueError(
            "cta_planのreasonが"
            "未入力です。"
        )

    recommended_tools = (
        article.get(
            "recommended_tools",
            [],
        )
    )

    if (
        primary_service
        is not None
        and primary_service
        not in recommended_tools
    ):

        raise ValueError(
            "cta_planのprimary_serviceは"
            "recommended_toolsに含まれる"
            "サービスを指定してください。"
        )

    if (
        primary_service
        is None
        and cta_label
        is not None
    ):

        raise ValueError(
            "primary_serviceがnullの場合は"
            "cta_labelもnullにしてください。"
        )

    if (
        primary_service
        is not None
        and cta_label
        is None
    ):

        raise ValueError(
            "primary_serviceを設定する場合は"
            "cta_labelも設定してください。"
        )

    comparison_table = (
        article.get(
            "comparison_table"
        )
    )

    if (
        comparison_table
        is not None
    ):

        if not isinstance(
            comparison_table,
            dict,
        ):

            raise ValueError(
                "comparison_tableは"
                "オブジェクトまたはnullにしてください。"
            )

        title = (
            comparison_table.get(
                "title"
            )
        )

        columns = (
            comparison_table.get(
                "columns"
            )
        )

        rows = (
            comparison_table.get(
                "rows"
            )
        )

        if (
            not isinstance(
                title,
                str,
            )
            or not title.strip()
        ):

            raise ValueError(
                "comparison_tableのtitleが"
                "未入力です。"
            )

        if (
            not isinstance(
                columns,
                list,
            )
            or not 2
            <= len(
                columns
            )
            <= 8
        ):

            raise ValueError(
                "comparison_tableのcolumnsは"
                "2件以上8件以下にしてください。"
            )

        if not all(
            isinstance(
                column,
                str,
            )
            and column.strip()
            for column in columns
        ):

            raise ValueError(
                "comparison_tableのcolumnsに"
                "空欄または不正な値があります。"
            )

        if (
            not isinstance(
                rows,
                list,
            )
            or not 2
            <= len(
                rows
            )
            <= 12
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

            label = (
                row.get(
                    "label"
                )
            )

            values = (
                row.get(
                    "values"
                )
            )

            if (
                not isinstance(
                    label,
                    str,
                )
                or not label.strip()
            ):

                raise ValueError(
                    f"比較表の{index}行目の"
                    "labelが未入力です。"
                )

            if (
                not isinstance(
                    values,
                    list,
                )
                or len(
                    values
                )
                != len(
                    columns
                )
            ):

                raise ValueError(
                    f"比較表の{index}行目の"
                    "values数とcolumns数が"
                    "一致していません。"
                )

            if not all(
                isinstance(
                    value,
                    str,
                )
                and value.strip()
                for value in values
            ):

                raise ValueError(
                    f"比較表の{index}行目に"
                    "空欄または不正な値があります。"
                )


# =========================================================
# Publish
# =========================================================

def publish_article(
    article: dict[str, Any],
    research: dict[str, Any],
    original_date: str | None = None,
    is_rewrite: bool = False,
) -> Path:
    """記事データをMDXファイルとして保存する。"""

    article[
        "comparison_table"
    ] = (
        normalize_comparison_table(
            article.get(
                "comparison_table"
            )
        )
    )

    validate_article(
        article
    )

    BLOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    slug = (
        article[
            "slug"
        ]
        .strip()
        .lower()
    )

    filepath = (
        BLOG_DIR
        / f"{slug}.mdx"
    )

    title = (
        escape_yaml_string(
            article[
                "title"
            ]
        )
    )

    description = (
        escape_yaml_string(
            article[
                "description"
            ]
        )
    )

    category = (
        escape_yaml_string(
            article[
                "category"
            ]
        )
    )

    image = (
        escape_yaml_string(
            article[
                "image"
            ]
        )
    )

    # -----------------------------------------------------
    # 本文
    # -----------------------------------------------------

    full_content = (
        article[
            "content"
        ].strip()
    )

    # -----------------------------------------------------
    # AI本文に混入した既存CTAを除去
    #
    # CTAはPublisher側で一元生成する。
    # -----------------------------------------------------

    full_content = (
        remove_existing_affiliate_links(
            full_content
        )
    )

    # -----------------------------------------------------
    # Comparison table
    # -----------------------------------------------------

    comparison_section = (
        build_comparison_table(
            article.get(
                "comparison_table"
            )
        )
    )

    if comparison_section:

        full_content, _ = (
            insert_before_summary(
                full_content,
                comparison_section,
            )
        )

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

    cta_plan = article.get(
        "cta_plan",
        {},
    )

    placement = str(
        cta_plan.get(
            "placement",
            "after_toc",
        )
    ).strip()

    if placement != "after_toc":

        raise ValueError(
            "CTA placementは"
            "after_tocである必要があります。"
        )

    affiliate_section = (
        build_affiliate_section(
            article[
                "recommended_tools"
            ],
            cta_plan,
        )
    )

    if affiliate_section:

        full_content += (
            "\n\n"
            + affiliate_section.strip()
        )

    # -----------------------------------------------------
    # FAQ
    # -----------------------------------------------------

    faq_items = article[
        "faq"
    ]

    full_content += (
        "\n\n"
        "## よくある質問\n"
    )

    for item in faq_items:

        question = (
            item[
                "question"
            ].strip()
        )

        answer = (
            item[
                "answer"
            ].strip()
        )

        full_content += (
            f"\n### {question}\n\n"
            f"{answer}\n"
        )

    # -----------------------------------------------------
    # Reading time
    # -----------------------------------------------------

    reading_time = (
        calculate_reading_time(
            full_content
        )
    )

    # -----------------------------------------------------
    # FAQ JSON-LD
    # -----------------------------------------------------

    faq_frontmatter: list[
        dict[str, str]
    ] = []

    for item in faq_items:

        question = (
            item[
                "question"
            ].strip()
        )

        answer = (
            item[
                "answer"
            ].strip()
        )

        clean_answer = (
            remove_source_markers(
                answer
            )
            .strip()
        )

        faq_frontmatter.append(
            {
                "question":
                    question,
                "answer":
                    clean_answer,
            }
        )

    faq_json = json.dumps(
        faq_frontmatter,
        ensure_ascii=False,
    )

    # -----------------------------------------------------
    # Dates
    # -----------------------------------------------------

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

    verified_date = (
        date.today().isoformat()
    )

    # -----------------------------------------------------
    # Frontmatter
    # -----------------------------------------------------

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

    for tag in article[
        "tags"
    ]:

        escaped_tag = (
            escape_yaml_string(
                tag
            )
        )

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

    # -----------------------------------------------------
    # MDX安全化
    #
    # <<TEXT>>
    # {タイトル}
    # {章/ページ範囲}
    # などによるMDXエラーを防止する。
    # -----------------------------------------------------

    safe_content = (
        escape_mdx_placeholders(
            full_content
        )
    )

    # -----------------------------------------------------
    # Sources
    #
    # [S1]等を公開本文から除去し、
    # 記事末尾へ参考情報を生成する。
    # -----------------------------------------------------

    cited_content = (
        apply_source_citations(
            content=safe_content,
            research=research,
            used_source_ids=article.get(
                "used_source_ids",
                [],
            ),
        )
    )

    mdx = "\n".join(
        frontmatter_lines
    )

    mdx += cited_content

    # -----------------------------------------------------
    # 公開直前最終チェック
    # -----------------------------------------------------

    assert_no_source_markers(
        mdx
    )

    filepath.write_text(
        mdx,
        encoding="utf-8",
    )

    # 公開記事を毎回すべて再走査し、A8.net提出用CSVを更新する。
    export_a8_submission_csv()

    return filepath
