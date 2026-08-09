import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

CONTENT_GAPS_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "content_gaps.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_queue.json"
)


COMMERCIAL_KEYWORDS = {
    "料金",
    "比較",
    "おすすめ",
    "使い方",
    "無料",
    "有料",
    "pro",
    "max",
    "ツール",
}

HIGH_COMMERCIAL_TOPICS = {
    "GitHub Copilot",
    "Claude Code",
    "Notta",
    "Otter",
    "Fireflies",
    "Adobe Firefly",
    "Midjourney",
    "Runway",
    "Gamma",
    "Canvaプレゼン",
    "ChatPDF",
    "DeepL",
    "Perplexity",
}


def load_content_gaps(
) -> list[dict[str, Any]]:
    """content_gaps.jsonから未カバーTopicを読み込む。"""

    if not CONTENT_GAPS_FILE.exists():
        raise FileNotFoundError(
            "content_gaps.jsonが"
            "見つかりません："
            f"{CONTENT_GAPS_FILE}"
        )

    try:
        data = json.loads(
            CONTENT_GAPS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "content_gaps.jsonの"
            "JSON形式が不正です。"
        ) from error

    gaps = data.get(
        "gaps",
        [],
    )

    if not isinstance(
        gaps,
        list,
    ):
        raise ValueError(
            "gapsは配列にしてください。"
        )

    return [
        item
        for item in gaps
        if (
            isinstance(
                item,
                dict,
            )
            and not item.get(
                "covered",
                False,
            )
        )
    ]

def build_article_title(
    topic: str,
    cluster: str,
) -> str:
    """Topicから仮の記事タイトルを作る。"""

    if topic.startswith("AI"):
        return (
            f"{topic}おすすめ比較｜"
            "料金・機能・使いやすさで選ぶ"
        )

    return (
        f"{topic}とは？"
        "料金・特徴・使い方をわかりやすく解説"
    )


def build_target_keyword(
    topic: str,
) -> str:
    """記事候補の主キーワードを作る。"""

    if topic.startswith("AI"):
        return (
            f"{topic} おすすめ"
        )

    return (
        f"{topic} 料金"
    )

def calculate_commercial_score(
    topic: str,
) -> int:
    """Topicの収益化しやすさを簡易評価する。"""

    if topic in HIGH_COMMERCIAL_TOPICS:
        return 20

    normalized = topic.lower()

    for keyword in COMMERCIAL_KEYWORDS:
        if keyword.lower() in normalized:
            return 15

    if not topic.startswith("AI"):
        # 固有サービス名である可能性が高い
        return 10

    return 5

def calculate_expansion_score(
    gap: dict[str, Any],
) -> int:
    """新記事候補の優先度を計算する。"""

    cluster_priority = int(
        gap.get(
            "cluster_priority",
            0,
        )
        or 0
    )

    topic = str(
        gap.get(
            "topic",
            "",
        )
    ).strip()

    commercial_score = (
        calculate_commercial_score(
            topic
        )
    )

    # cluster_priorityを80%、
    # 商用性を20点加算するイメージ
    score = (
        int(
            cluster_priority
            * 0.8
        )
        + commercial_score
    )

    return min(
        score,
        100,
    )

def build_expansion_queue(
    gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Content Gapから記事候補Queueを生成する。"""

    queue: list[
        dict[str, Any]
    ] = []

    for gap in gaps:
        topic = str(
            gap.get(
                "topic",
                "",
            )
        ).strip()

        cluster = str(
            gap.get(
                "cluster",
                "",
            )
        ).strip()

        if not topic:
            continue

        commercial_score = (
            calculate_commercial_score(
                topic
            )
        )

        expansion_score = (
            calculate_expansion_score(
                gap
            )
        )

        queue.append(
            {
                "topic":
                    topic,
                "cluster":
                    cluster,
                "target_keyword":
                    build_target_keyword(
                        topic
                    ),
                "suggested_title":
                    build_article_title(
                        topic,
                        cluster,
                    ),
                "cluster_priority":
                    int(
                        gap.get(
                            "cluster_priority",
                            0,
                        )
                        or 0
                    ),
                "commercial_score":
                    commercial_score,
                "expansion_score":
                    expansion_score,
                "status":
                    "candidate",
            }
        )

    queue.sort(
        key=lambda item: (
            item[
                "expansion_score"
            ]
        ),
        reverse=True,
    )

    return queue

def save_expansion_queue(
    queue: list[dict[str, Any]],
) -> Path:
    """記事拡張Queueを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "candidate_count":
                    len(queue),
                "candidates":
                    queue,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_expansion_queue(
    queue: list[dict[str, Any]],
) -> None:
    """記事候補を表示する。"""

    print(
        "\n===== Atlas Expansion Queue =====\n"
    )

    print(
        "新記事候補："
        f"{len(queue)}件"
    )

    print(
        "\n--- 優先記事候補 ---"
    )

    for item in queue[
        :20
    ]:
        print(
            f"[{item['expansion_score']}点] "
            f"{item['topic']}"
        )

        print(
            "  KW: "
            f"{item['target_keyword']}"
        )

        print(
            "  Cluster: "
            f"{item['cluster']}"
        )

        print(
            "  商用性: "
            f"{item['commercial_score']}"
        )

        print()


def main() -> None:
    gaps = (
        load_content_gaps()
    )

    queue = (
        build_expansion_queue(
            gaps
        )
    )

    filepath = (
        save_expansion_queue(
            queue
        )
    )

    print_expansion_queue(
        queue
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()