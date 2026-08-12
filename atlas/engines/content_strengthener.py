import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.content_strengthener import (
    strengthen_article,
)
from engines.article_loader import (
    load_article_by_slug,
)
from engines.editorial_context import (
    get_queries_for_slug,
)


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "content_strengthening"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "latest_result.json"
)

BACKUP_DIR = (
    OUTPUT_DIR
    / "backups"
)


MIN_SECTION_TITLE_LENGTH = 4
MAX_SECTION_TITLE_LENGTH = 80

MIN_SECTION_CONTENT_LENGTH = 80
MAX_SECTION_CONTENT_LENGTH = 5000


def normalize_heading(
    value: str,
) -> str:
    """見出し比較用に文字列を簡易正規化する。"""

    return (
        value
        .strip()
        .lower()
        .replace(" ", "")
        .replace("　", "")
        .replace("・", "")
        .replace("/", "")
        .replace("／", "")
        .replace("-", "")
        .replace("_", "")
    )


def extract_h2_titles(
    content: str,
) -> list[str]:
    """Markdown本文からH2見出しを取得する。"""

    pattern = re.compile(
        r"(?m)^##\s+(.+?)\s*$"
    )

    return [
        match.strip()
        for match in pattern.findall(
            content
        )
        if match.strip()
    ]


def validate_strengthening(
    *,
    section_title: str,
    section_content: str,
    existing_content: str,
) -> tuple[bool, str]:
    """追加セクションを安全側で検証する。"""

    title = section_title.strip()

    content = section_content.strip()

    if not title:
        return (
            False,
            "section_titleが空です。",
        )

    if (
        len(title)
        < MIN_SECTION_TITLE_LENGTH
    ):
        return (
            False,
            (
                "section_titleが短すぎます。"
                f" length={len(title)}"
            ),
        )

    if (
        len(title)
        > MAX_SECTION_TITLE_LENGTH
    ):
        return (
            False,
            (
                "section_titleが長すぎます。"
                f" length={len(title)}"
            ),
        )

    if "\n" in title:
        return (
            False,
            "section_titleに改行があります。",
        )

    if title.startswith("#"):
        return (
            False,
            (
                "section_titleにはMarkdown見出し記号を"
                "含めないでください。"
            ),
        )

    if not content:
        return (
            False,
            "section_contentが空です。",
        )

    if (
        len(content)
        < MIN_SECTION_CONTENT_LENGTH
    ):
        return (
            False,
            (
                "section_contentが短すぎます。"
                f" length={len(content)}"
            ),
        )

    if (
        len(content)
        > MAX_SECTION_CONTENT_LENGTH
    ):
        return (
            False,
            (
                "section_contentが長すぎます。"
                f" length={len(content)}"
            ),
        )

    existing_h2 = (
        extract_h2_titles(
            existing_content
        )
    )

    normalized_title = (
        normalize_heading(
            title
        )
    )

    for heading in existing_h2:
        if (
            normalize_heading(
                heading
            )
            == normalized_title
        ):
            return (
                False,
                (
                    "同名のH2見出しが"
                    "すでに存在します。"
                ),
            )

    return (
        True,
        "",
    )


def build_section(
    section_title: str,
    section_content: str,
) -> str:
    """追加用Markdownセクションを作る。"""

    return (
        f"## {section_title.strip()}\n\n"
        f"{section_content.strip()}\n"
    )


def insert_before_summary(
    existing_content: str,
    section: str,
) -> str:
    """
    まとめ系H2の直前へ追加する。
    見つからない場合は本文末尾へ追加する。
    """

    summary_pattern = re.compile(
        (
            r"(?m)^##\s+"
            r"(まとめ|総まとめ|結論|"
            r"さいごに|最後に)"
            r"\s*$"
        )
    )

    match = summary_pattern.search(
        existing_content
    )

    if match is not None:
        position = match.start()

        before = (
            existing_content[
                :position
            ].rstrip()
        )

        after = (
            existing_content[
                position:
            ].lstrip()
        )

        return (
            before
            + "\n\n"
            + section.strip()
            + "\n\n"
            + after
        )

    return (
        existing_content.rstrip()
        + "\n\n"
        + section.strip()
        + "\n"
    )


def rebuild_article_text(
    raw_text: str,
    new_content: str,
) -> str:
    """frontmatterを維持して本文だけ差し替える。"""

    parts = raw_text.split(
        "---",
        2,
    )

    if len(parts) < 3:
        raise ValueError(
            "記事のfrontmatter形式が不正です。"
        )

    return (
        "---"
        + parts[1]
        + "---\n"
        + new_content.strip()
        + "\n"
    )


def backup_article(
    filepath: Path,
    slug: str,
) -> Path:
    """変更前記事をバックアップする。"""

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = (
        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    backup_path = (
        BACKUP_DIR
        / (
            f"{slug}_"
            f"{timestamp}.mdx"
        )
    )

    shutil.copy2(
        filepath,
        backup_path,
    )

    return backup_path


def build_result(
    *,
    status: str,
    slug: str,
    changed: bool,
    section_title: str,
    section_content: str,
    reason: str,
    change_summary: str,
    target_queries: list[str],
    filepath: Path | None = None,
    backup_path: Path | None = None,
) -> dict[str, Any]:
    """Content Strengthening結果を作る。"""

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status":
            status,
        "slug":
            slug,
        "changed":
            changed,
        "section_title":
            section_title,
        "section_content":
            section_content,
        "reason":
            reason,
        "change_summary":
            change_summary,
        "target_queries":
            target_queries,
        "filepath":
            (
                str(filepath)
                if filepath
                else ""
            ),
        "backup_path":
            (
                str(backup_path)
                if backup_path
                else ""
            ),
    }


def strengthen_existing_article(
    slug: str,
    reason: str = "",
    dry_run: bool = True,
) -> dict[str, Any]:
    """既存記事へ部分強化セクションを追加する。"""

    slug = slug.strip()

    if not slug:
        raise ValueError(
            "slugがありません。"
        )

    article = (
        load_article_by_slug(
            slug
        )
    )

    filepath = article.get(
        "filepath"
    )

    if not isinstance(
        filepath,
        Path,
    ):
        raise ValueError(
            "記事filepathを取得できません。"
        )

    existing_content = str(
        article.get(
            "content",
            "",
        )
    )

    raw_text = str(
        article.get(
            "raw_text",
            "",
        )
    )

    if not existing_content:
        raise ValueError(
            "記事本文がありません。"
        )

    if not raw_text:
        raise ValueError(
            "raw_textがありません。"
        )

    query_rows = (
        get_queries_for_slug(
            slug
        )
    )

    proposal = (
        strengthen_article(
            article=article,
            search_queries=
                query_rows,
            reason=reason,
        )
    )

    section_title = str(
        proposal.get(
            "section_title",
            "",
        )
    ).strip()

    section_content = str(
        proposal.get(
            "section_content",
            "",
        )
    ).strip()

    proposal_reason = str(
        proposal.get(
            "reason",
            "",
        )
    ).strip()

    change_summary = str(
        proposal.get(
            "change_summary",
            "",
        )
    ).strip()

    raw_target_queries = (
        proposal.get(
            "target_queries",
            [],
        )
    )

    target_queries = (
        [
            str(item).strip()
            for item in raw_target_queries
            if str(item).strip()
        ]
        if isinstance(
            raw_target_queries,
            list,
        )
        else []
    )

    available_queries = {
        str(
            row.get(
                "query",
                "",
            )
        ).strip()
        for row in query_rows
        if isinstance(
            row,
            dict,
        )
        and str(
            row.get(
                "query",
                "",
            )
        ).strip()
    }

    matched_target_queries = [
        query
        for query in target_queries
        if query in available_queries
    ]

    if not dry_run:
        if not query_rows:
            return build_result(
                status="rejected",
                slug=slug,
                changed=False,
                section_title=
                    section_title,
                section_content=
                    section_content,
                reason=(
                    "Search Console検索語が"
                    "取得できないため、"
                    "STRENGTHENを実行しません。"
                ),
                change_summary=
                    change_summary,
                target_queries=
                    target_queries,
                filepath=filepath,
            )

        if not target_queries:
            return build_result(
                status="rejected",
                slug=slug,
                changed=False,
                section_title=
                    section_title,
                section_content=
                    section_content,
                reason=(
                    "改善対象のSearch Console検索語が"
                    "特定されていないため、"
                    "STRENGTHENを実行しません。"
                ),
                change_summary=
                    change_summary,
                target_queries=
                    target_queries,
                filepath=filepath,
            )

        if not matched_target_queries:
            return build_result(
                status="rejected",
                slug=slug,
                changed=False,
                section_title=
                    section_title,
                section_content=
                    section_content,
                reason=(
                    "AIが指定した改善対象検索語が"
                    "実際のSearch Console検索語と"
                    "一致しないため、"
                    "STRENGTHENを実行しません。"
                ),
                change_summary=
                    change_summary,
                target_queries=
                    target_queries,
                filepath=filepath,
            )

    valid, validation_reason = (
        validate_strengthening(
            section_title=
                section_title,
            section_content=
                section_content,
            existing_content=
                existing_content,
        )
    )

    if not valid:
        return build_result(
            status="rejected",
            slug=slug,
            changed=False,
            section_title=
                section_title,
            section_content=
                section_content,
            reason=
                validation_reason,
            change_summary=
                change_summary,
            target_queries=
                target_queries,
            filepath=filepath,
        )

    section = build_section(
        section_title,
        section_content,
    )

    updated_content = (
        insert_before_summary(
            existing_content,
            section,
        )
    )

    updated_text = (
        rebuild_article_text(
            raw_text,
            updated_content,
        )
    )

    if dry_run:
        return build_result(
            status="dry_run",
            slug=slug,
            changed=False,
            section_title=
                section_title,
            section_content=
                section_content,
            reason=
                proposal_reason,
            change_summary=
                change_summary,
            target_queries=
                target_queries,
            filepath=filepath,
        )

    backup_path = (
        backup_article(
            filepath,
            slug,
        )
    )

    filepath.write_text(
        updated_text,
        encoding="utf-8",
    )

    return build_result(
        status="updated",
        slug=slug,
        changed=True,
        section_title=
            section_title,
        section_content=
            section_content,
        reason=
            proposal_reason,
        change_summary=
            change_summary,
        target_queries=
            target_queries,
        filepath=filepath,
        backup_path=
            backup_path,
    )


def save_result(
    result: dict[str, Any],
) -> Path:
    """結果JSONを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_result(
    result: dict[str, Any],
) -> None:
    """結果をコンソール表示する。"""

    print(
        "\n===== Atlas Content Strengthener =====\n"
    )

    print(
        "Status："
        f"{result.get('status', '')}"
    )

    print(
        "Slug："
        f"{result.get('slug', '')}"
    )

    print(
        "Changed："
        + (
            "YES"
            if result.get(
                "changed"
            )
            else "NO"
        )
    )

    print(
        "Section："
        f"{result.get('section_title', '')}"
    )

    print(
        "Reason："
        f"{result.get('reason', '')}"
    )

    print()


def main() -> None:
    """Content Strengthener単体実行。"""

    import sys

    slug = (
        sys.argv[1].strip()
        if len(sys.argv) >= 2
        else ""
    )

    if not slug:
        raise ValueError(
            "slugを指定してください。"
        )

    dry_run = (
        "--apply"
        not in sys.argv[2:]
    )

    result = (
        strengthen_existing_article(
            slug=slug,
            dry_run=dry_run,
        )
    )

    filepath = (
        save_result(
            result
        )
    )

    print_result(
        result
    )

    print(
        f"結果保存先：{filepath}"
    )

    if dry_run:
        print(
            "DRY RUNのため記事は変更していません。"
        )


if __name__ == "__main__":
    main()