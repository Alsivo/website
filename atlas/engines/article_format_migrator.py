import argparse
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

BLOG_DIR = (
    BASE_DIR.parent
    / "content"
    / "blog"
)


def build_formatted_line(
    line: str,
) -> str | None:
    """
    箇条書きの
    「項目名：説明文」を
    「**項目名：** 説明文」へ変換する。
    """

    stripped = line.lstrip()

    if not stripped.startswith("- "):
        return None

    indent = line[
        : len(line) - len(stripped)
    ]

    body = stripped[2:]

    # 既に太字整形済み、または
    # Markdownリンクから始まる行は対象外
    if (
        body.startswith("**")
        or body.startswith("[")
    ):
        return None

    # -----------------------------------------------------
    # 最初の「括弧の外側」にあるコロンだけを探す
    # -----------------------------------------------------

    depth = 0
    colon_index = None

    opening_chars = "（("
    closing_chars = "）)"

    for index, char in enumerate(body):
        if char in opening_chars:
            depth += 1
            continue

        if char in closing_chars:
            depth = max(
                0,
                depth - 1,
            )
            continue

        if (
            char in "：:"
            and depth == 0
        ):
            colon_index = index
            break

    if colon_index is None:
        return None

    title = body[:colon_index].strip()
    colon = body[colon_index]
    description = body[
        colon_index + 1:
    ].strip()

    # -----------------------------------------------------
    # 安全策
    # -----------------------------------------------------

    if not title:
        return None

    if not description:
        return None

    # 長すぎるタイトルは
    # 普通の文章である可能性が高い
    if len(title) > 32:
        return None

    # URLやMarkdown記号を
    # タイトル部分に含む場合は除外
    if (
        "http://" in title
        or "https://" in title
        or "[" in title
        or "]" in title
        or "**" in title
    ):
        return None

    # 文末記号を含む場合は
    # 普通の文章である可能性が高い
    if any(
        mark in title
        for mark in [
            "。",
            "！",
            "？",
            "!",
            "?",
        ]
    ):
        return None

    return (
        f"{indent}- "
        f"**{title}{colon}** "
        f"{description}"
    )


def scan_file(
    filepath: Path,
) -> list[
    tuple[int, str, str]
]:
    """
    1ファイルを調査し、
    frontmatterを除外して
    変更候補を返す。
    """

    text = filepath.read_text(
        encoding="utf-8",
    )

    lines = text.splitlines()

    changes: list[
        tuple[int, str, str]
    ] = []

    in_frontmatter = False
    frontmatter_finished = False

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        if (
            line_number == 1
            and line.strip() == "---"
        ):
            in_frontmatter = True
            continue

        if (
            in_frontmatter
            and line.strip() == "---"
        ):
            in_frontmatter = False
            frontmatter_finished = True
            continue

        if in_frontmatter:
            continue

        formatted = build_formatted_line(
            line
        )

        if formatted is None:
            continue

        if formatted == line:
            continue

        changes.append(
            (
                line_number,
                line,
                formatted,
            )
        )

    return changes


def apply_changes(
    filepath: Path,
) -> int:
    """
    frontmatterを除外し、
    本文だけに変更を反映する。
    """

    text = filepath.read_text(
        encoding="utf-8",
    )

    lines = text.splitlines()

    changed_count = 0
    new_lines: list[str] = []

    in_frontmatter = False

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        if (
            line_number == 1
            and line.strip() == "---"
        ):
            in_frontmatter = True
            new_lines.append(line)
            continue

        if (
            in_frontmatter
            and line.strip() == "---"
        ):
            in_frontmatter = False
            new_lines.append(line)
            continue

        if in_frontmatter:
            new_lines.append(line)
            continue

        formatted = build_formatted_line(
            line
        )

        if (
            formatted is not None
            and formatted != line
        ):
            new_lines.append(
                formatted
            )
            changed_count += 1
        else:
            new_lines.append(
                line
            )

    ends_with_newline = (
        text.endswith("\n")
    )

    new_text = "\n".join(
        new_lines
    )

    if ends_with_newline:
        new_text += "\n"

    filepath.write_text(
        new_text,
        encoding="utf-8",
    )

    return changed_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "既存MDX記事の"
            "小項目タイトルを整形します。"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "実際にMDXファイルを更新します。"
            "指定しない場合はdry-runです。"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    apply_mode = args.apply

    print(
        "\n===== Article Format Migrator =====\n"
    )

    if apply_mode:
        print(
            "モード：APPLY"
        )

        print(
            "MDXファイルへ"
            "実際に変更を反映します。\n"
        )
    else:
        print(
            "モード：DRY RUN"
        )

        print(
            "実際のMDXファイルは"
            "変更しません。\n"
        )

    mdx_files = sorted(
        BLOG_DIR.glob("*.mdx")
    )

    total_changes = 0
    affected_files = 0

    for filepath in mdx_files:
        changes = scan_file(
            filepath
        )

        if not changes:
            continue

        affected_files += 1

        print(
            "--------------------------------"
        )

        print(
            f"FILE: {filepath.name}"
        )

        for (
            line_number,
            before,
            after,
        ) in changes:
            total_changes += 1

            print(
                f"\nL{line_number}"
            )

            print(
                "BEFORE:"
            )

            print(
                before
            )

            print(
                "AFTER:"
            )

            print(
                after
            )

        if apply_mode:
            changed_count = apply_changes(
                filepath
            )

            print(
                f"\nAPPLIED: "
                f"{changed_count} changes"
            )

    print(
        "\n================================"
    )

    print(
        f"対象記事数：{affected_files}"
    )

    print(
        f"変更候補数：{total_changes}"
    )

    if apply_mode:
        print(
            "※ MDXファイルへ"
            "変更を反映しました。"
        )
    else:
        print(
            "※ DRY RUNのため"
            "実ファイルは変更していません。"
        )

    print(
        "================================\n"
    )


if __name__ == "__main__":
    main()