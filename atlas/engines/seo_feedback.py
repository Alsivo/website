import csv
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parents[1]

SEARCH_CONSOLE_DIR = (
    BASE_DIR
    / "data"
    / "search_console"
)

PAGE_FILE = (
    SEARCH_CONSOLE_DIR
    / "page_performance.csv"
)

PAGE_QUERY_FILE = (
    SEARCH_CONSOLE_DIR
    / "page_query_performance.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "seo_feedback"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "seo_feedback.json"
)


MIN_IMPRESSIONS_FOR_ACTION = 5
MIN_IMPRESSIONS_FOR_CTR = 20


def load_csv(
    filepath: Path,
) -> list[dict[str, str]]:
    """CSVを読み込む。"""

    if not filepath.exists():
        return []

    with filepath.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(
            csv.DictReader(file)
        )


def extract_slug(
    page_url: str,
) -> str:
    """記事URLからslugを取得する。"""

    try:
        parsed = urlparse(
            page_url
        )
    except ValueError:
        return ""

    path = (
        parsed.path
        or ""
    ).rstrip("/")

    prefix = "/blog/"

    if not path.startswith(
        prefix
    ):
        return ""

    slug = path[
        len(prefix):
    ].strip()

    return slug


def to_float(
    value: Any,
) -> float:
    """安全にfloatへ変換する。"""

    try:
        return float(
            value
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0


def build_query_map(
    page_query_rows: list[
        dict[str, str]
    ],
) -> dict[
    str,
    list[dict[str, Any]],
]:
    """slugごとの検索語データを作る。"""

    result: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for row in page_query_rows:
        page = str(
            row.get(
                "page",
                "",
            )
        ).strip()

        slug = extract_slug(
            page
        )

        if not slug:
            continue

        item = {
            "query": str(
                row.get(
                    "query",
                    "",
                )
            ).strip(),
            "clicks": to_float(
                row.get(
                    "clicks"
                )
            ),
            "impressions": to_float(
                row.get(
                    "impressions"
                )
            ),
            "ctr": to_float(
                row.get(
                    "ctr"
                )
            ),
            "position": to_float(
                row.get(
                    "position"
                )
            ),
        }

        result.setdefault(
            slug,
            [],
        ).append(
            item
        )

    for slug in result:
        result[
            slug
        ].sort(
            key=lambda item: (
                item[
                    "impressions"
                ],
                -item[
                    "position"
                ],
            ),
            reverse=True,
        )

    return result


def classify_page(
    impressions: float,
    clicks: float,
    ctr: float,
    position: float,
) -> tuple[str, int, str]:
    """
    SEO状態を安全側に判定する。

    action:
    - monitor
    - keep
    - strengthen
    - improve_ctr
    - improve_content
    - rethink
    """

    if impressions < (
        MIN_IMPRESSIONS_FOR_ACTION
    ):
        return (
            "monitor",
            20,
            (
                "表示回数が少なく、"
                "判断材料が不足しています。"
            ),
        )

    if (
        1 <= position <= 3
    ):
        return (
            "keep",
            30,
            (
                "上位表示できています。"
                "大幅な変更は避け、"
                "推移を監視します。"
            ),
        )

    if (
        4 <= position <= 10
    ):
        if (
            impressions
            >= MIN_IMPRESSIONS_FOR_CTR
            and ctr < 0.02
        ):
            return (
                "improve_ctr",
                85,
                (
                    "検索順位は良好ですが、"
                    "CTRが低いため"
                    "タイトル・description改善候補です。"
                ),
            )

        return (
            "strengthen",
            70,
            (
                "1ページ目に表示されています。"
                "検索意図との一致や"
                "内部リンク強化で"
                "上位化を狙える状態です。"
            ),
        )

    if (
        10 < position <= 30
    ):
        return (
            "improve_content",
            75,
            (
                "2〜3ページ目に位置しており、"
                "コンテンツ改善で"
                "上位化余地があります。"
            ),
        )

    if (
        30 < position <= 70
    ):
        return (
            "improve_content",
            55,
            (
                "検索露出はありますが、"
                "順位が低いため"
                "検索意図・構成・網羅性を"
                "再確認します。"
            ),
        )

    if position > 70:
        return (
            "rethink",
            45,
            (
                "検索露出はあるものの"
                "順位が非常に低いため、"
                "記事テーマや検索意図の"
                "再検討候補です。"
            ),
        )

    return (
        "monitor",
        20,
        "判断材料が不足しています。",
    )


def aggregate_page_rows(
    page_rows: list[
        dict[str, str]
    ],
) -> dict[
    str,
    dict[str, Any],
]:
    """同一slugのSearch Consoleデータを統合する。"""

    result: dict[
        str,
        dict[str, Any],
    ] = {}

    for row in page_rows:
        page = str(
            row.get(
                "page",
                "",
            )
        ).strip()

        slug = extract_slug(
            page
        )

        if not slug:
            continue

        clicks = to_float(
            row.get(
                "clicks"
            )
        )

        impressions = to_float(
            row.get(
                "impressions"
            )
        )

        position = to_float(
            row.get(
                "position"
            )
        )

        if slug not in result:
            result[
                slug
            ] = {
                "slug":
                    slug,
                "pages":
                    [],
                "clicks":
                    0.0,
                "impressions":
                    0.0,
                "position_weighted_sum":
                    0.0,
            }

        item = result[
            slug
        ]

        item[
            "pages"
        ].append(
            page
        )

        item[
            "clicks"
        ] += clicks

        item[
            "impressions"
        ] += impressions

        item[
            "position_weighted_sum"
        ] += (
            position
            * impressions
        )

    for item in result.values():
        impressions = item[
            "impressions"
        ]

        clicks = item[
            "clicks"
        ]

        item[
            "ctr"
        ] = (
            clicks
            / impressions
            if impressions
            else 0.0
        )

        item[
            "position"
        ] = (
            item[
                "position_weighted_sum"
            ]
            / impressions
            if impressions
            else 0.0
        )

        item.pop(
            "position_weighted_sum",
            None,
        )

    return result

def build_seo_feedback(
) -> list[dict[str, Any]]:
    """記事ごとのSEO Feedbackを作る。"""

    page_rows = load_csv(
        PAGE_FILE
    )

    page_query_rows = load_csv(
        PAGE_QUERY_FILE
    )

    query_map = build_query_map(
        page_query_rows
    )

    aggregated_pages = (
        aggregate_page_rows(
            page_rows
        )
    )

    feedback: list[
        dict[str, Any]
    ] = []

    for slug, item in (
        aggregated_pages.items()
    ):
        clicks = float(
            item.get(
                "clicks",
                0,
            )
        )

        impressions = float(
            item.get(
                "impressions",
                0,
            )
        )

        ctr = float(
            item.get(
                "ctr",
                0,
            )
        )

        position = float(
            item.get(
                "position",
                0,
            )
        )

        (
            action,
            priority,
            reason,
        ) = classify_page(
            impressions,
            clicks,
            ctr,
            position,
        )

        feedback.append(
            {
                "slug":
                    slug,
                "pages":
                    item.get(
                        "pages",
                        [],
                    ),
                "clicks":
                    clicks,
                "impressions":
                    impressions,
                "ctr":
                    ctr,
                "position":
                    position,
                "action":
                    action,
                "priority":
                    priority,
                "reason":
                    reason,
                "top_queries":
                    query_map.get(
                        slug,
                        [],
                    )[:10],
            }
        )

    feedback.sort(
        key=lambda item: (
            item[
                "priority"
            ],
            item[
                "impressions"
            ],
        ),
        reverse=True,
    )

    return feedback


def save_seo_feedback(
    feedback: list[
        dict[str, Any]
    ],
) -> Path:
    """SEO Feedbackを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "feedback":
                    feedback,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def main() -> None:
    feedback = (
        build_seo_feedback()
    )

    filepath = (
        save_seo_feedback(
            feedback
        )
    )

    print(
        "\n===== Atlas SEO Feedback =====\n"
    )

    if not feedback:
        print(
            "ブログ記事の"
            "Search Consoleデータは"
            "ありません。"
        )
        return

    for item in feedback:
        print(
            f"[{item['priority']}点] "
            f"{item['slug']}"
        )

        print(
            "  action: "
            f"{item['action']}"
        )

        print(
            "  impressions: "
            f"{item['impressions']}"
        )

        print(
            "  clicks: "
            f"{item['clicks']}"
        )

        print(
            "  position: "
            f"{item['position']:.2f}"
        )

        print(
            "  CTR: "
            f"{item['ctr']:.2%}"
        )

        print(
            "  reason: "
            f"{item['reason']}"
        )

        queries = item.get(
            "top_queries",
            [],
        )

        if queries:
            print(
                "  queries:"
            )

            for query in (
                queries[:5]
            ):
                print(
                    "    - "
                    f"{query['query']} "
                    f"(順位 "
                    f"{query['position']:.1f})"
                )

        print()

    print(
        "保存先："
        f"{filepath}"
    )


if __name__ == "__main__":
    main()