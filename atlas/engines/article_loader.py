import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

WEBSITE_DIR = BASE_DIR.parent

BLOG_DIR = (
    WEBSITE_DIR
    / "content"
    / "blog"
)


def parse_frontmatter_value(
    frontmatter: str,
    key: str,
) -> str:
    """Frontmatterの文字列項目を取得する。"""

    pattern = (
        rf'^{re.escape(key)}:\s*'
        rf'["\']?(.*?)["\']?\s*$'
    )

    match = re.search(
        pattern,
        frontmatter,
        flags=re.MULTILINE,
    )

    if not match:
        return ""

    return match.group(1).strip()


def parse_tags(
    frontmatter: str,
) -> list[str]:
    """Frontmatterのtags配列を取得する。"""

    lines = frontmatter.splitlines()

    tags: list[str] = []

    inside_tags = False

    for line in lines:
        if line.strip() == "tags:":
            inside_tags = True
            continue

        if inside_tags:
            stripped = line.strip()

            if stripped.startswith("- "):
                tag = (
                    stripped[2:]
                    .strip()
                    .strip('"\'')
                )

                if tag:
                    tags.append(tag)

                continue

            if stripped:
                break

    return tags


def parse_faq(
    frontmatter: str,
) -> list[dict[str, str]]:
    """Frontmatter内のfaq JSONを取得する。"""

    match = re.search(
        r"^faq:\s*(.+)$",
        frontmatter,
        flags=re.MULTILINE,
    )

    if not match:
        return []

    raw_value = match.group(1).strip()

    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    faq_items: list[dict[str, str]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        question = str(
            item.get("question", "")
        ).strip()

        answer = str(
            item.get("answer", "")
        ).strip()

        if question and answer:
            faq_items.append(
                {
                    "question": question,
                    "answer": answer,
                }
            )

    return faq_items


def load_article_by_slug(
    slug: str,
) -> dict[str, Any]:
    """slugから既存MDX記事を読み込む。"""

    filepath = (
        BLOG_DIR
        / f"{slug}.mdx"
    )

    if not filepath.exists():
        raise FileNotFoundError(
            "リライト対象の記事が"
            "見つかりません："
            f"{filepath}"
        )

    text = filepath.read_text(
        encoding="utf-8",
    )

    parts = text.split(
        "---",
        2,
    )

    if len(parts) < 3:
        raise ValueError(
            "記事のfrontmatter形式が不正です。"
        )

    frontmatter = parts[1]

    content = parts[2].strip()

    title = parse_frontmatter_value(
        frontmatter,
        "title",
    )

    description = (
        parse_frontmatter_value(
            frontmatter,
            "description",
        )
    )

    al_question = parse_frontmatter_value(frontmatter, "alQuestion")
    cibo_answer = parse_frontmatter_value(frontmatter, "ciboAnswer")

    category = parse_frontmatter_value(
        frontmatter,
        "category",
    )

    image = parse_frontmatter_value(
        frontmatter,
        "image",
    )

    date_value = parse_frontmatter_value(
        frontmatter,
        "date",
    )

    updated = parse_frontmatter_value(
        frontmatter,
        "updated",
    )

    reading_time = (
        parse_frontmatter_value(
            frontmatter,
            "readingTime",
        )
    )

    tags = parse_tags(
        frontmatter
    )

    faq = parse_faq(
        frontmatter
    )

    return {
        "filepath": filepath,
        "slug": slug,
        "title": title,
        "description": description,
        "alQuestion": al_question,
        "ciboAnswer": cibo_answer,
        "category": category,
        "image": image,
        "date": date_value,
        "updated": updated,
        "reading_time": reading_time,
        "tags": tags,
        "faq": faq,
        "content": content,
        "raw_frontmatter": frontmatter,
        "raw_text": text,
    }
