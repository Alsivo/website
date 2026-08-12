import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.title_optimizer import (
    optimize_title,
)
from engines.article_loader import (
    load_article_by_slug,
)
from engines.editorial_context import (
    get_queries_for_slug,
)


BASE_DIR = Path(__file__).resolve().parents[1]

BLOG_DIR = (
    BASE_DIR.parent
    / "content"
    / "blog"
)

BACKUP_DIR = (
    BASE_DIR
    / "data"
    / "title_optimization"
    / "backups"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "title_optimization"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "latest_result.json"
)


MIN_TITLE_LENGTH = 10
MAX_TITLE_LENGTH = 90


def validate_title(
    title: str,
) -> tuple[bool, str]:
    """生成されたタイトルを安全側で検証する。"""

    cleaned = title.strip()

    if not cleaned:
        return (
            False,
            "タイトルが空です。",
        )

    if len(cleaned) < MIN_TITLE_LENGTH:
        return (
            False,
            (
                "タイトルが短すぎます。"
                f" length={len(cleaned)}"
            ),
        )

    if len(cleaned) > MAX_TITLE_LENGTH:
        return (
            False,
            (
                "タイトルが長すぎます。"
                f" length={len(cleaned)}"
            ),
        )

    if "\n" in cleaned:
        return (
            False,
            "タイトルに改行が含まれています。",
        )

    if cleaned.count('"') % 2 != 0:
        return (
            False,
            "タイトル内のダブルクォートが不正です。",
        )

    return (
        True,
        "",
    )


def escape_yaml_string(
    value: str,
) -> str:
    """YAMLのダブルクォート文字列用にエスケープする。"""

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


def replace_frontmatter_title(
    raw_text: str,
    new_title: str,
) -> str:
    """MDX frontmatterのtitle行だけを置換する。"""

    parts = raw_text.split(
        "---",
        2,
    )

    if len(parts) < 3:
        raise ValueError(
            "記事のfrontmatter形式が不正です。"
        )

    frontmatter = parts[1]

    escaped_title = (
        escape_yaml_string(
            new_title
        )
    )

    pattern = re.compile(
        r'(?m)^title:\s*".*?"\s*$'
    )

    matches = pattern.findall(
        frontmatter
    )

    if len(matches) != 1:
        raise ValueError(
            "frontmatterのtitle行を"
            "1件だけ特定できませんでした。"
            f" count={len(matches)}"
        )

    updated_frontmatter = (
        pattern.sub(
            lambda _: (
                f'title: "{escaped_title}"'
            ),
            frontmatter,
            count=1,
        )
    )

    return (
        "---"
        + updated_frontmatter
        + "---"
        + parts[2]
    )


def backup_article(
    filepath: Path,
    slug: str,
) -> Path:
    """タイトル変更前の記事をバックアップする。"""

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
    old_title: str,
    new_title: str,
    changed: bool,
    reason: str,
    change_summary: str = "",
    target_queries: list[str] | None = None,
    backup_path: Path | None = None,
    filepath: Path | None = None,
) -> dict[str, Any]:
    """タイトル最適化結果を作る。"""

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status":
            status,
        "slug":
            slug,
        "changed":
            changed,
        "old_title":
            old_title,
        "new_title":
            new_title,
        "reason":
            reason,
        "change_summary":
            change_summary,
        "target_queries":
            target_queries or [],
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


def optimize_article_title(
    slug: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """指定記事のタイトルだけを最適化する。"""

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

    old_title = str(
        article.get(
            "title",
            "",
        )
    ).strip()

    if not old_title:
        raise ValueError(
            "現在のタイトルがありません。"
        )

    query_rows = (
        get_queries_for_slug(
            slug
        )
    )

    result = optimize_title(
        article,
        query_rows,
    )

    new_title = str(
        result.get(
            "new_title",
            "",
        )
    ).strip()

    reason = str(
        result.get(
            "reason",
            "",
        )
    ).strip()

    change_summary = str(
        result.get(
            "change_summary",
            "",
        )
    ).strip()

    raw_target_queries = (
        result.get(
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

    valid, validation_reason = (
        validate_title(
            new_title
        )
    )

    if not valid:
        return build_result(
            status="rejected",
            slug=slug,
            old_title=old_title,
            new_title=new_title,
            changed=False,
            reason=validation_reason,
            change_summary=
                change_summary,
            target_queries=
                target_queries,
            filepath=filepath,
        )

    if new_title == old_title:
        return build_result(
            status="unchanged",
            slug=slug,
            old_title=old_title,
            new_title=new_title,
            changed=False,
            reason=(
                reason
                or
                "現在のタイトルを維持します。"
            ),
            change_summary=
                change_summary,
            target_queries=
                target_queries,
            filepath=filepath,
        )

    raw_text = str(
        article.get(
            "raw_text",
            "",
        )
    )

    if not raw_text:
        raise ValueError(
            "記事本文を取得できません。"
        )

    updated_text = (
        replace_frontmatter_title(
            raw_text,
            new_title,
        )
    )

    if dry_run:
        return build_result(
            status="dry_run",
            slug=slug,
            old_title=old_title,
            new_title=new_title,
            changed=False,
            reason=reason,
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
        old_title=old_title,
        new_title=new_title,
        changed=True,
        reason=reason,
        change_summary=
            change_summary,
        target_queries=
            target_queries,
        backup_path=
            backup_path,
        filepath=filepath,
    )


def save_result(
    result: dict[str, Any],
) -> Path:
    """実行結果JSONを保存する。"""

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
    """実行結果を表示する。"""

    print(
        "\n===== Atlas Title Optimizer =====\n"
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
        "Old Title："
        f"{result.get('old_title', '')}"
    )

    print(
        "New Title："
        f"{result.get('new_title', '')}"
    )

    print(
        "Reason："
        f"{result.get('reason', '')}"
    )

    print()


def main() -> None:
    """Title Optimizer単体実行。"""

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
        optimize_article_title(
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