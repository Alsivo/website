import json
import re
from pathlib import Path
from typing import Any
from collections import Counter
from engines.affiliate_registry import (
    get_affiliate_tool_names,
)
from agents.internal_link_editor import (
    select_internal_links,
)

BASE_DIR = Path(__file__).resolve().parents[1]

BLOG_DIR = (
    BASE_DIR.parent
    / "content"
    / "blog"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "internal_links"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "internal_links.json"
)

GENERIC_TAGS = {
    "ai",
    "aiツール",
    "生成ai",
    "料金",
    "料金比較",
    "比較",
    "おすすめ",
    "仕事効率化",
    "業務効率化",
}

TOPIC_TERMS = {
    "コード生成",
    "コーディング",
    "メール",
    "文章作成",
    "ライティング",
    "画像生成",
    "動画生成",
    "プレゼン",
    "資料作成",
    "議事録",
    "文字起こし",
}

SERVICE_TOPICS = {
    "cursor": {
        "コード生成",
        "コーディング",
    },
    "claude": {
        "文章作成",
        "ライティング",
    },
    "chatgpt": {
        "文章作成",
        "ライティング",
    },
    "gemini": {
        "文章作成",
        "ライティング",
    },
    "canva": {
        "画像生成",
        "プレゼン",
        "資料作成",
    },
    "gamma": {
        "プレゼン",
        "資料作成",
    },
}

INTERNAL_LINK_SECTION_START = (
    "<!-- ALSIVO_INTERNAL_LINKS_START -->"
)

INTERNAL_LINK_SECTION_END = (
    "<!-- ALSIVO_INTERNAL_LINKS_END -->"
)

def normalize_text(value: str) -> str:
    """比較用に文字列を正規化する。"""

    return (
        value.strip()
        .lower()
        .replace("　", " ")
    )


def detect_services(
    article: dict[str, Any],
) -> set[str]:
    """タイトル・説明文からサービス名を検出する。"""

    text = normalize_text(
        " ".join(
            [
                str(
                    article.get(
                        "title",
                        "",
                    )
                ),
                str(
                    article.get(
                        "description",
                        "",
                    )
                ),
            ]
        )
    )

    detected: set[str] = set()

    for tool_name in (
        get_affiliate_tool_names()
    ):
        normalized_tool = (
            normalize_text(
                tool_name
            )
        )

        if (
            normalized_tool
            and normalized_tool in text
        ):
            detected.add(
                normalized_tool
            )

    return detected


def detect_topics(
    article: dict[str, Any],
) -> set[str]:
    """記事の具体テーマを検出する。"""

    text = normalize_text(
        " ".join(
            [
                str(
                    article.get(
                        "title",
                        "",
                    )
                ),
                str(
                    article.get(
                        "description",
                        "",
                    )
                ),
            ]
        )
    )

    detected: set[str] = set()

    # タイトル・説明文からテーマを検出
    for topic in TOPIC_TERMS:
        normalized_topic = (
            normalize_text(topic)
        )

        if normalized_topic in text:
            detected.add(
                normalized_topic
            )

    # 登場サービスからテーマを補完
    services = detect_services(
        article
    )

    for service in services:
        service_topics = (
            SERVICE_TOPICS.get(
                service,
                set(),
            )
        )

        for topic in service_topics:
            detected.add(
                normalize_text(topic)
            )

    return detected


def calculate_tag_frequency(
    articles: list[
        dict[str, Any]
    ],
) -> Counter[str]:
    """各タグが何記事で使われているか数える。"""

    frequency: Counter[str] = Counter()

    for article in articles:
        unique_tags = {
            normalize_text(tag)
            for tag in article.get(
                "tags",
                [],
            )
            if normalize_text(tag)
        }

        frequency.update(
            unique_tags
        )

    return frequency


def extract_frontmatter(
    filepath: Path,
) -> dict[str, Any]:
    """MDXのfrontmatterから必要情報を取得する。"""

    text = filepath.read_text(
        encoding="utf-8",
    )

    match = re.match(
        r"^---\s*\n(.*?)\n---",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return {}

    frontmatter = match.group(1)

    result: dict[str, Any] = {
        "slug": filepath.stem,
        "title": "",
        "description": "",
        "category": "",
        "tags": [],
    }

    current_list: str | None = None

    for raw_line in frontmatter.splitlines():
        line = raw_line.rstrip()

        if line.startswith("title:"):
            result["title"] = (
                line.split(":", 1)[1]
                .strip()
                .strip('"')
            )
            current_list = None

        elif line.startswith("description:"):
            result["description"] = (
                line.split(":", 1)[1]
                .strip()
                .strip('"')
            )
            current_list = None

        elif line.startswith("category:"):
            result["category"] = (
                line.split(":", 1)[1]
                .strip()
                .strip('"')
            )
            current_list = None

        elif line == "tags:":
            current_list = "tags"

        elif (
            current_list == "tags"
            and line.strip().startswith("- ")
        ):
            tag = (
                line.strip()[2:]
                .strip()
                .strip('"')
            )

            if tag:
                result["tags"].append(tag)

        elif line and not line.startswith(" "):
            current_list = None

    return result


def load_articles() -> list[dict[str, Any]]:
    """公開記事の基本情報を読み込む。"""

    if not BLOG_DIR.exists():
        raise FileNotFoundError(
            f"Blogフォルダがありません：{BLOG_DIR}"
        )

    articles = []

    for filepath in BLOG_DIR.glob("*.mdx"):
        article = extract_frontmatter(
            filepath
        )

        if (
            article.get("slug")
            and article.get("title")
        ):
            articles.append(article)

    return articles


def calculate_relation_score(
    source: dict[str, Any],
    target: dict[str, Any],
    tag_frequency: Counter[str],
    article_count: int,
) -> int:
    """2記事間の内部リンク関連度を計算する。"""

    if (
        source["slug"]
        == target["slug"]
    ):
        return 0

    score = 0

    # ========================================================
    # 1. サービス名
    # ========================================================

    source_services = (
        detect_services(source)
    )

    target_services = (
        detect_services(target)
    )

    common_services = (
        source_services
        & target_services
    )

    if common_services:
        score += 45

    # ========================================================
    # 2. 記事テーマ
    # ========================================================

    source_topics = (
        detect_topics(source)
    )

    target_topics = (
        detect_topics(target)
    )

    common_topics = (
        source_topics
        & target_topics
    )

    if common_topics:
        score += min(
            45,
            len(common_topics) * 25,
        )

    # ========================================================
    # 関連性の必須条件
    # ========================================================

    if (
        not common_services
        and not common_topics
    ):
        return 0

    # ========================================================
    # 3. タグ
    # ========================================================

    source_tags = {
        normalize_text(tag)
        for tag in source.get(
            "tags",
            [],
        )
    }

    target_tags = {
        normalize_text(tag)
        for tag in target.get(
            "tags",
            [],
        )
    }

    common_tags = (
        source_tags
        & target_tags
    )

    for tag in common_tags:
        if not tag:
            continue

        # 明示的な汎用タグ
        if tag in GENERIC_TAGS:
            score += 2
            continue

        frequency = (
            tag_frequency[tag]
        )

        ratio = (
            frequency / article_count
            if article_count
            else 1
        )

        # 多くの記事に付いているタグほど
        # 関連性判定への影響を弱くする
        if ratio >= 0.7:
            score += 2
        elif ratio >= 0.4:
            score += 5
        else:
            score += 12

    # ========================================================
    # 4. カテゴリー
    # ========================================================

    if (
        source.get("category")
        and source.get("category")
        == target.get("category")
    ):
        score += 5

    # ========================================================
    # 5. テーマが全く異なる場合は減点
    # ========================================================

    if (
        source_topics
        and target_topics
        and not common_topics
        and not common_services
    ):
        score -= 25

    return max(
        0,
        min(
            score,
            100,
        ),
    )


def create_anchor_text(
    target: dict[str, Any],
) -> str:
    """内部リンク用アンカーテキストを作る。"""

    title = str(
        target.get(
            "title",
            "",
        )
    ).strip()

    return title


def build_internal_links(
    max_links: int = 5,
    minimum_score: int = 20,
) -> dict[str, list[dict[str, Any]]]:
    """全記事の内部リンク候補を作る。"""

    articles = load_articles()

    tag_frequency = (
        calculate_tag_frequency(
            articles
        )
    )

    article_count = len(
        articles
    )

    result: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    for source in articles:
        candidates = []

        for target in articles:
            score = calculate_relation_score(
                source,
                target,
                tag_frequency,
                article_count,
            )

            if score < minimum_score:
                continue

            candidates.append(
                {
                    "slug":
                        target["slug"],
                    "title":
                        target["title"],
                    "anchor":
                        create_anchor_text(
                            target
                        ),
                    "score":
                        score,
                }
            )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        result[source["slug"]] = (
            candidates[:max_links]
        )

    return result


def save_internal_links(
    data: dict[str, list[dict[str, Any]]],
) -> None:
    """内部リンク候補をJSON保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_internal_link_section(
    links: list[dict[str, Any]],
) -> str:
    """内部リンク用のMarkdownブロックを作る。"""

    if not links:
        return ""

    lines = [
        INTERNAL_LINK_SECTION_START,
        "",
        "## あわせて読みたい",
        "",
    ]

    for link in links:
        slug = str(
            link.get(
                "slug",
                "",
            )
        ).strip()

        anchor = str(
            link.get(
                "anchor",
                "",
            )
        ).strip()

        if not slug or not anchor:
            continue

        lines.append(
            f"- [{anchor}](/blog/{slug})"
        )

    lines.extend(
        [
            "",
            INTERNAL_LINK_SECTION_END,
        ]
    )

    return "\n".join(lines)


def remove_existing_internal_link_section(
    content: str,
) -> str:
    """Atlasが追加した内部リンクブロックだけ削除する。"""

    pattern = (
        re.escape(
            INTERNAL_LINK_SECTION_START
        )
        + r".*?"
        + re.escape(
            INTERNAL_LINK_SECTION_END
        )
    )

    cleaned = re.sub(
        pattern,
        "",
        content,
        flags=re.DOTALL,
    )

    return cleaned.strip()

def insert_internal_link_section(
    content: str,
    section: str,
) -> str:
    """FAQ直前へ内部リンクブロックを挿入する。"""

    if not section:
        return content

    cleaned = (
        remove_existing_internal_link_section(
            content
        )
    )

    faq_heading = (
        "## よくある質問"
    )

    if faq_heading in cleaned:
        before, after = cleaned.split(
            faq_heading,
            1,
        )

        return (
            before.rstrip()
            + "\n\n"
            + section
            + "\n\n"
            + faq_heading
            + after
        )

    reference_heading = (
        "## 参考情報"
    )

    if reference_heading in cleaned:
        before, after = cleaned.split(
            reference_heading,
            1,
        )

        return (
            before.rstrip()
            + "\n\n"
            + section
            + "\n\n"
            + reference_heading
            + after
        )

    return (
        cleaned.rstrip()
        + "\n\n"
        + section
        + "\n"
    )


def split_mdx(
    text: str,
) -> tuple[str, str]:
    """MDXをfrontmatterと本文に分ける。"""

    match = re.match(
        r"^(---\s*\n.*?\n---\s*\n)(.*)$",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "MDXのfrontmatter形式が不正です。"
        )

    return (
        match.group(1),
        match.group(2),
    )


def apply_internal_links_to_articles(
    link_map: dict[
        str,
        list[dict[str, Any]],
    ],
) -> list[Path]:
    """AI選定済み内部リンクを各MDXへ反映する。"""

    updated_files: list[Path] = []

    for slug, links in link_map.items():
        filepath = (
            BLOG_DIR
            / f"{slug}.mdx"
        )

        if not filepath.exists():
            continue

        original_text = (
            filepath.read_text(
                encoding="utf-8",
            )
        )

        frontmatter, content = (
            split_mdx(
                original_text
            )
        )

        section = (
            build_internal_link_section(
                links
            )
        )

        if section:
            updated_content = (
                insert_internal_link_section(
                    content,
                    section,
                )
            )
        else:
            updated_content = (
                remove_existing_internal_link_section(
                    content
                )
            )

        new_text = (
            frontmatter
            + updated_content.strip()
            + "\n"
        )

        if new_text == original_text:
            continue

        filepath.write_text(
            new_text,
            encoding="utf-8",
        )

        updated_files.append(
            filepath
        )

    return updated_files


def print_internal_links(
    data: dict[str, list[dict[str, Any]]],
) -> None:
    """確認用に候補を表示する。"""

    print(
        "\n===== Internal Link Report ====="
    )

    for slug, links in data.items():
        print(
            f"\n[{slug}]"
        )

        if not links:
            print(
                "  関連記事候補なし"
            )
            continue

        for link in links:
            print(
                "  → "
                f"/blog/{link['slug']}"
            )

            print(
                f"     Anchor: "
                f"{link['anchor']}"
            )

            print(
                f"     Reason: "
                f"{link['reason']}"
            )


def refine_internal_links_with_ai(
    candidate_map: dict[
        str,
        list[dict[str, Any]],
    ],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    """ルール候補をAIで最終選定する。"""

    articles = load_articles()

    article_map = {
        article["slug"]: article
        for article in articles
    }

    refined: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    for slug, candidates in (
        candidate_map.items()
    ):
        source_article = (
            article_map.get(
                slug
            )
        )

        if source_article is None:
            refined[slug] = []
            continue

        if not candidates:
            refined[slug] = []
            continue

        print(
            "[Internal Link AI] "
            f"{slug} を判定中..."
        )

        selected = (
            select_internal_links(
                source_article,
                candidates,
            )
        )

        refined[slug] = (
            selected
        )

    return refined


def main() -> None:
    print(
        "[Internal Linker] "
        "記事間の関連性を解析中..."
    )

    candidate_data = (
        build_internal_links()
    )

    print(
        "\n[Internal Linker] "
        "AIによる最終判定を開始します..."
    )

    data = (
        refine_internal_links_with_ai(
            candidate_data
        )
    )

    save_internal_links(data)

    print_internal_links(data)

    print(
        "\n保存先："
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()