import csv
import json
from pathlib import Path
from typing import Any


ATLAS_DIR = Path(__file__).resolve().parents[1]
WEBSITE_ROOT = ATLAS_DIR.parent
GITHUB_ROOT = WEBSITE_ROOT.parent

DATA_CONTENT_ENGINE_ROOT = (
    GITHUB_ROOT
    / "data-content-engine"
)

INPUT_FILE = (
    ATLAS_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_keyword_evaluations.json"
)

REQUIRED_COLUMNS = {
    "keyword",
    "target_length",
    "related_keywords",
    "search_intent",
}


def load_json(
    filepath: Path,
) -> dict[str, Any]:

    if not filepath.exists():
        raise FileNotFoundError(
            f"{filepath.name} が見つかりません："
            f"{filepath}"
        )

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{filepath.name} のJSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{filepath.name} の最上位は"
            "オブジェクトにしてください。"
        )

    return data


def find_keywords_csv() -> Path:
    """
    data-content-engine内から
    Keyword Queueが利用しているCSVを探す。
    """

    if not DATA_CONTENT_ENGINE_ROOT.exists():
        raise FileNotFoundError(
            "data-content-engineが見つかりません："
            f"{DATA_CONTENT_ENGINE_ROOT}"
        )

    candidates = []

    for csv_path in (
        DATA_CONTENT_ENGINE_ROOT.rglob(
            "*.csv"
        )
    ):
        try:
            with csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.DictReader(
                    file
                )

                columns = set(
                    reader.fieldnames
                    or []
                )

            if REQUIRED_COLUMNS.issubset(
                columns
            ):
                candidates.append(
                    csv_path
                )

        except (
            OSError,
            UnicodeDecodeError,
        ):
            continue

    if not candidates:
        raise FileNotFoundError(
            "必要な列を持つkeywords CSVが"
            "見つかりません。"
        )

    candidates.sort(
        key=lambda path: (
            len(
                path.parts
            ),
            str(
                path
            ).lower(),
        )
    )

    return candidates[0]


def load_existing_keywords(
    csv_path: Path,
) -> set[str]:

    result = set()

    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            keyword = str(
                row.get(
                    "keyword",
                    "",
                )
            ).strip()

            if keyword:
                result.add(
                    keyword.lower()
                )

    return result


def load_queue_articles() -> list[dict[str, Any]]:

    data = load_json(
        INPUT_FILE
    )

    ranking = data.get(
        "ranking",
        [],
    )

    if not isinstance(
        ranking,
        list,
    ):
        raise ValueError(
            "ranking は配列にしてください。"
        )

    result = []

    for item in ranking:

        if not isinstance(
            item,
            dict,
        ):
            continue

        if (
            item.get(
                "recommended_action"
            )
            != "QUEUE_ARTICLE"
        ):
            continue

        keyword = str(
            item.get(
                "keyword",
                "",
            )
        ).strip()

        if not keyword:
            continue

        related_keywords = (
            item.get(
                "related_keywords",
                [],
            )
        )

        if not isinstance(
            related_keywords,
            list,
        ):
            related_keywords = []

        result.append(
            {
                "keyword": keyword,
                "target_length": int(
                    item.get(
                        "target_length",
                        3000,
                    )
                    or 3000
                ),
                "related_keywords": [
                    str(
                        value
                    ).strip()
                    for value
                    in related_keywords
                    if str(
                        value
                    ).strip()
                ],
                "search_intent": str(
                    item.get(
                        "search_intent",
                        "commercial",
                    )
                ).strip(),
                "program_name": str(
                    item.get(
                        "program_name",
                        "",
                    )
                ).strip(),
                "overall_score": int(
                    item.get(
                        "overall_score",
                        0,
                    )
                    or 0
                ),
            }
        )

    return result


def append_keywords(
    csv_path: Path,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    existing_keywords = (
        load_existing_keywords(
            csv_path
        )
    )

    added = []

    # 既存CSVの末尾に改行がなければ補う
    raw_bytes = csv_path.read_bytes()

    if (
        raw_bytes
        and not raw_bytes.endswith(
            (b"\n", b"\r")
        )
    ):
        with csv_path.open(
            "ab"
        ) as file:
            file.write(
                b"\r\n"
            )

    for item in candidates:

        keyword = item[
            "keyword"
        ].strip()

        if (
            keyword.lower()
            in existing_keywords
        ):
            continue

        with csv_path.open(
            "a",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "keyword",
                    "target_length",
                    "related_keywords",
                    "search_intent",
                ],
            )

            writer.writerow(
                {
                    "keyword": keyword,
                    "target_length": (
                        item[
                            "target_length"
                        ]
                    ),
                    "related_keywords": (
                        ", ".join(
                            item[
                                "related_keywords"
                            ]
                        )
                    ),
                    "search_intent": (
                        item[
                            "search_intent"
                        ]
                    ),
                }
            )

        existing_keywords.add(
            keyword.lower()
        )

        added.append(
            item
        )

    return added


def print_result(
    csv_path: Path,
    candidates: list[dict[str, Any]],
    added: list[dict[str, Any]],
) -> None:

    print(
        "\n===== Affiliate Keyword Export =====\n"
    )

    print(
        "出力先："
        f"{csv_path}"
    )

    print(
        "QUEUE_ARTICLE候補："
        f"{len(candidates)}件"
    )

    print(
        "新規追加："
        f"{len(added)}件"
    )

    if added:

        print(
            "\n追加キーワード:"
        )

        for item in added:

            print(
                "- "
                f"{item['keyword']} "
                f"({item['overall_score']}点)"
            )

            print(
                "  target_length: "
                f"{item['target_length']}"
            )

            print(
                "  program: "
                f"{item['program_name']}"
            )

    else:
        print(
            "\n追加対象はありません。"
        )


def main() -> None:

    csv_path = (
        find_keywords_csv()
    )

    candidates = (
        load_queue_articles()
    )

    added = append_keywords(
        csv_path,
        candidates,
    )

    print_result(
        csv_path,
        candidates,
        added,
    )


if __name__ == "__main__":
    main()