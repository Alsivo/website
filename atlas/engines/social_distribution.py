import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from core.paths import (
    BLOG_CONTENT_DIR,
    SOCIAL_DIR,
    SOCIAL_QUEUE_FILE,
)


SITE_URL = "https://alsivo.com"

SUPPORTED_PLATFORMS = {
    "x",
    "instagram",
    "line",
}


def normalize_text(
    value: Any,
) -> str:
    """文字列を安全に正規化する。"""

    return str(
        value
        if value is not None
        else ""
    ).strip()


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}

    if not isinstance(
        data,
        dict,
    ):
        return {}

    return data


def extract_frontmatter(
    text: str,
) -> dict[str, str]:
    """MDXのfrontmatterから最低限の情報を取得する。"""

    if not text.startswith("---"):
        return {}

    parts = text.split(
        "---",
        2,
    )

    if len(parts) < 3:
        return {}

    frontmatter_text = parts[1]

    result: dict[str, str] = {}

    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(
            ":",
            1,
        )

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] in {
                '"',
                "'",
            }
            and value[-1]
            == value[0]
        ):
            value = value[1:-1]

        result[key] = value

    return result


def extract_first_paragraph(
    text: str,
) -> str:
    """本文冒頭からSNS要約候補を取得する。"""

    if text.startswith("---"):
        parts = text.split(
            "---",
            2,
        )

        if len(parts) >= 3:
            text = parts[2]

    lines = text.splitlines()

    paragraphs: list[str] = []
    current: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            if current:
                paragraphs.append(
                    " ".join(
                        current
                    )
                )
                current = []
            continue

        if line.startswith(
            (
                "#",
                "<",
                "{",
                "![",
                "- ",
                "* ",
                "|",
            )
        ):
            if current:
                paragraphs.append(
                    " ".join(
                        current
                    )
                )
                current = []
            continue

        current.append(
            line
        )

    if current:
        paragraphs.append(
            " ".join(
                current
            )
        )

    for paragraph in paragraphs:
        cleaned = re.sub(
            r"\[(.*?)\]\(.*?\)",
            r"\1",
            paragraph,
        )

        cleaned = re.sub(
            r"[`*_]",
            "",
            cleaned,
        ).strip()

        if len(cleaned) >= 20:
            return cleaned

    return ""


def load_article(
    slug: str,
) -> dict[str, str]:
    """slugから記事情報を取得する。"""

    filepath = (
        BLOG_CONTENT_DIR
        / f"{slug}.mdx"
    )

    if not filepath.exists():
        raise FileNotFoundError(
            "記事が見つかりません："
            f"{filepath}"
        )

    text = filepath.read_text(
        encoding="utf-8",
    )

    frontmatter = (
        extract_frontmatter(
            text
        )
    )

    title = normalize_text(
        frontmatter.get(
            "title",
            "",
        )
    )

    if not title:
        raise ValueError(
            "記事titleを取得できません："
            f"{slug}"
        )

    description = normalize_text(
        frontmatter.get(
            "description",
            "",
        )
    )

    if not description:
        description = (
            extract_first_paragraph(
                text
            )
        )

    return {
        "slug":
            slug,

        "title":
            title,

        "description":
            description,

        "url":
            (
                f"{SITE_URL}/blog/"
                f"{slug}"
            ),

        "filepath":
            str(filepath),
    }


def build_social_item(
    article: dict[str, str],
    platform: str,
) -> dict[str, Any]:
    """SNS配信候補を作成する。"""

    platform = (
        platform.strip().lower()
    )

    if (
        platform
        not in SUPPORTED_PLATFORMS
    ):
        raise ValueError(
            "未対応platformです："
            f"{platform}"
        )

    now = (
        datetime.now().isoformat()
    )

    return {
        "social_id":
            uuid.uuid4().hex[:12],

        "created_at":
            now,

        "updated_at":
            now,

        "status":
            "pending",

        "requires_approval":
            True,

        "approved":
            False,

        "published":
            False,

        "platform":
            platform,

        "language":
            "ja",

        "article_slug":
            article["slug"],

        "article_title":
            article["title"],

        "article_description":
            article[
                "description"
            ],

        "article_url":
            article["url"],

        "post_text":
            "",

        "media_path":
            "",

        "published_at":
            "",

        "external_post_id":
            "",

        "error":
            "",
    }


def build_identity_key(
    item: dict[str, Any],
) -> tuple[str, str, str]:
    """同一配信候補を判定する。"""

    return (
        normalize_text(
            item.get(
                "platform",
                "",
            )
        ).lower(),

        normalize_text(
            item.get(
                "language",
                "",
            )
        ).lower(),

        normalize_text(
            item.get(
                "article_slug",
                "",
            )
        ),
    )


def load_existing_queue(
) -> list[dict[str, Any]]:
    """既存Social Queueを読み込む。"""

    data = load_json(
        SOCIAL_QUEUE_FILE
    )

    queue = data.get(
        "queue",
        [],
    )

    if not isinstance(
        queue,
        list,
    ):
        return []

    return [
        item
        for item in queue
        if isinstance(
            item,
            dict,
        )
    ]


def add_candidate(
    queue: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    bool,
]:
    """重複を避けてQueueへ追加する。"""

    candidate_key = (
        build_identity_key(
            candidate
        )
    )

    for item in queue:
        if (
            build_identity_key(
                item
            )
            == candidate_key
        ):
            return (
                queue,
                False,
            )

    queue.append(
        candidate
    )

    return (
        queue,
        True,
    )


def refresh_candidate(
    queue: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    bool,
]:
    """
    同一記事・同一platformの未投稿候補を
    新しい候補へ置き換える。

    published済み候補は履歴として残す。
    """

    candidate_key = (
        build_identity_key(
            candidate
        )
    )

    refreshed_queue: list[
        dict[str, Any]
    ] = []

    replaced = False

    for item in queue:

        if (
            build_identity_key(
                item
            )
            != candidate_key
        ):
            refreshed_queue.append(
                item
            )
            continue

        published = bool(
            item.get(
                "published",
                False,
            )
        )

        status = normalize_text(
            item.get(
                "status",
                "",
            )
        ).lower()

        # 実投稿済みは履歴として残す
        if (
            published
            or status == "published"
        ):
            refreshed_queue.append(
                item
            )
            continue

        # 未投稿の旧候補は削除して
        # 新候補へ置き換える
        replaced = True

    refreshed_queue.append(
        candidate
    )

    return (
        refreshed_queue,
        replaced,
    )


def save_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """Social Queueを保存する。"""

    SOCIAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pending = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "pending"
    )

    approved = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "approved"
    )

    published = sum(
        1
        for item in queue
        if item.get(
            "status"
        )
        == "published"
    )

    payload = {
        "updated_at":
            datetime.now().isoformat(),

        "total":
            len(queue),

        "pending":
            pending,

        "approved":
            approved,

        "published":
            published,

        "queue":
            queue,
    }

    SOCIAL_QUEUE_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return SOCIAL_QUEUE_FILE


def create_distribution_queue(
    slug: str,
    refresh: bool = False,
) -> tuple[
    list[dict[str, Any]],
    int,
]:
    """1記事からSNS配信候補を生成する。"""

    article = load_article(
        slug
    )

    queue = (
        load_existing_queue()
    )

    added_count = 0

    for platform in [
        "x",
        "instagram",
        "line",
    ]:
        candidate = (
            build_social_item(
                article,
                platform,
            )
        )

        if refresh:

            (
                queue,
                _,
            ) = refresh_candidate(
                queue,
                candidate,
            )

            added_count += 1

        else:

            (
                queue,
                added,
            ) = add_candidate(
                queue,
                candidate,
            )

            if added:
                added_count += 1

    save_queue(
        queue
    )

    return (
        queue,
        added_count,
    )


def print_summary(
    slug: str,
    queue: list[dict[str, Any]],
    added_count: int,
) -> None:
    """実行結果を表示する。"""

    print(
        "\n===== Atlas Social Distribution =====\n"
    )

    print(
        f"Article：{slug}"
    )

    print(
        f"Added：{added_count}"
    )

    print(
        f"Queue Total：{len(queue)}"
    )

    print()

    for platform in [
        "x",
        "instagram",
        "line",
    ]:
        count = sum(
            1
            for item in queue
            if (
                item.get(
                    "platform"
                )
                == platform
            )
        )

        print(
            f"{platform}：{count}"
        )

    print()

    print(
        "保存先："
        f"{SOCIAL_QUEUE_FILE}"
    )


def main() -> None:
    """Social Distribution Queueを生成する。"""

    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "slug",
        help="配信候補を作成する記事slug",
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "同一記事の未投稿SNS候補を"
            "最新内容で置き換える"
        ),
    )

    args = parser.parse_args()

    queue, added_count = (
        create_distribution_queue(
            args.slug,
            refresh=args.refresh,
        )
    )

    print_summary(
        args.slug,
        queue,
        added_count,
    )


if __name__ == "__main__":
    main()