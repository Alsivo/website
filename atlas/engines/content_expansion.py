import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

WEBSITE_ROOT = (
    BASE_DIR.parent
)

BLOG_DIR = (
    WEBSITE_ROOT
    / "content"
    / "blog"
)

SEEDS_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "topic_seeds.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "content_gaps.json"
)

def extract_frontmatter_value(
    text: str,
    key: str,
) -> str:
    """MDX frontmatterから単一文字列を取得する。"""

    pattern = re.compile(
        rf'^{re.escape(key)}:\s*["\']?(.*?)["\']?\s*$',
        re.MULTILINE,
    )

    match = pattern.search(
        text
    )

    if match is None:
        return ""

    return match.group(
        1
    ).strip()


def load_existing_articles(
) -> list[dict[str, str]]:
    """現在公開済みのブログ記事一覧を取得する。"""

    if not BLOG_DIR.exists():
        raise FileNotFoundError(
            "ブログ記事フォルダが"
            "見つかりません："
            f"{BLOG_DIR}"
        )

    articles: list[
        dict[str, str]
    ] = []

    for filepath in sorted(
        BLOG_DIR.glob(
            "*.mdx"
        )
    ):
        text = filepath.read_text(
            encoding="utf-8",
        )

        title = (
            extract_frontmatter_value(
                text,
                "title",
            )
        )

        articles.append(
            {
                "slug":
                    filepath.stem,
                "title":
                    title,
                "content":
                    text,
            }
        )

    return articles

def load_topic_seeds(
) -> list[dict[str, Any]]:
    """記事拡張用Topic Seedを読み込む。"""

    if not SEEDS_FILE.exists():
        raise FileNotFoundError(
            "topic_seeds.jsonが"
            "見つかりません："
            f"{SEEDS_FILE}"
        )

    try:
        data = json.loads(
            SEEDS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "topic_seeds.jsonの"
            "JSON形式が不正です。"
        ) from error

    clusters = data.get(
        "clusters",
        [],
    )

    if not isinstance(
        clusters,
        list,
    ):
        raise ValueError(
            "clustersは配列にしてください。"
        )

    return [
        item
        for item in clusters
        if isinstance(
            item,
            dict,
        )
    ]

def normalize_text(
    value: str,
) -> str:
    """簡易比較用に文字列を正規化する。"""

    return (
        value
        .lower()
        .replace(" ", "")
        .replace("　", "")
        .replace("-", "")
        .replace("_", "")
        .replace("・", "")
        .replace("／", "")
        .replace("/", "")
    )


def topic_is_covered(
    topic: str,
    articles: list[dict[str, str]],
) -> bool:
    """
    Topicが既存記事で十分扱われている可能性があるか確認する。

    title / slug / 本文を対象に簡易判定する。
    """

    normalized_topic = (
        normalize_text(
            topic
        )
    )

    if not normalized_topic:
        return False

    for article in articles:
        title = normalize_text(
            article.get(
                "title",
                "",
            )
        )

        slug = normalize_text(
            article.get(
                "slug",
                "",
            )
        )

        content = normalize_text(
            article.get(
                "content",
                "",
            )
        )

        # タイトルまたはslugに含まれる場合は
        # 既存Topicとして扱う。
        if (
            normalized_topic in title
            or normalized_topic in slug
        ):
            return True

        # 本文に複数回登場する場合、
        # 既存記事ですでに一定程度扱っていると判断する。
        occurrence_count = (
            content.count(
                normalized_topic
            )
        )

        if occurrence_count >= 3:
            return True

    return False

def build_content_gaps(
    clusters: list[dict[str, Any]],
    articles: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """現在の記事群に不足しているTopicを抽出する。"""

    gaps: list[
        dict[str, Any]
    ] = []

    for cluster in clusters:
        cluster_name = str(
            cluster.get(
                "cluster",
                "",
            )
        ).strip()

        priority = int(
            cluster.get(
                "priority",
                0,
            )
            or 0
        )

        topics = cluster.get(
            "topics",
            [],
        )

        if not isinstance(
            topics,
            list,
        ):
            continue

        for topic in topics:
            if not isinstance(
                topic,
                str,
            ):
                continue

            topic = topic.strip()

            if not topic:
                continue

            covered = (
                topic_is_covered(
                    topic,
                    articles,
                )
            )

            gaps.append(
                {
                    "cluster":
                        cluster_name,
                    "topic":
                        topic,
                    "cluster_priority":
                        priority,
                    "covered":
                        covered,
                }
            )

    return gaps

def save_content_gaps(
    gaps: list[dict[str, Any]],
    articles: list[dict[str, str]],
) -> Path:
    """Content Gap結果を保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    uncovered = [
        item
        for item in gaps
        if not item[
            "covered"
        ]
    ]

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "article_count":
                    len(articles),
                "gap_count":
                    len(uncovered),
                "gaps":
                    gaps,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_content_gaps(
    gaps: list[dict[str, Any]],
    articles: list[dict[str, str]],
) -> None:
    """Content GapをCMDへ表示する。"""

    uncovered = [
        item
        for item in gaps
        if not item[
            "covered"
        ]
    ]

    uncovered.sort(
        key=lambda item: (
            item[
                "cluster_priority"
            ]
        ),
        reverse=True,
    )

    print(
        "\n===== Atlas Content Expansion =====\n"
    )

    print(
        "既存記事数："
        f"{len(articles)}"
    )

    print(
        "未カバーTopic数："
        f"{len(uncovered)}"
    )

    print(
        "\n--- 優先Content Gap ---"
    )

    for item in uncovered[
        :20
    ]:
        print(
            f"[{item['cluster_priority']}点] "
            f"{item['cluster']} / "
            f"{item['topic']}"
        )


def main() -> None:
    articles = (
        load_existing_articles()
    )

    clusters = (
        load_topic_seeds()
    )

    gaps = (
        build_content_gaps(
            clusters,
            articles,
        )
    )

    filepath = (
        save_content_gaps(
            gaps,
            articles,
        )
    )

    print_content_gaps(
        gaps,
        articles,
    )

    print(
        f"\n保存先：{filepath}"
    )


if __name__ == "__main__":
    main()