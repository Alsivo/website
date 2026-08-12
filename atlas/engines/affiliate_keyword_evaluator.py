import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import (
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY,
)


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_article_candidates.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "affiliate_keyword_evaluations.json"
)

MAX_ARTICLE_CANDIDATES = 3


KEYWORD_EVALUATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "program_name": {
            "type": "string",
        },
        "evaluations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                    },
                    "search_intent": {
                        "type": "string",
                        "enum": [
                            "informational",
                            "commercial",
                            "transactional",
                            "mixed",
                        ],
                    },
                    "demand_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "competition_opportunity_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "commercial_intent_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "topic_fit_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "overall_score": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "recommended_action": {
                        "type": "string",
                        "enum": [
                            "QUEUE_ARTICLE",
                            "HOLD",
                            "REJECT",
                        ],
                    },
                    "reason": {
                        "type": "string",
                    },
                    "suggested_title": {
                        "type": "string",
                    },
                    "related_keywords": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "maxItems": 8,
                    },
                    "target_length": {
                        "type": "integer",
                        "minimum": 1500,
                        "maximum": 10000,
                    },
                },
                "required": [
                    "keyword",
                    "search_intent",
                    "demand_score",
                    "competition_opportunity_score",
                    "commercial_intent_score",
                    "topic_fit_score",
                    "overall_score",
                    "recommended_action",
                    "reason",
                    "suggested_title",
                    "related_keywords",
                    "target_length",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "program_name",
        "evaluations",
    ],
    "additionalProperties": False,
}


def load_candidates() -> list[dict[str, Any]]:

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "affiliate_article_candidates.json "
            f"が見つかりません：{INPUT_FILE}"
        )

    try:
        data = json.loads(
            INPUT_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "affiliate_article_candidates.json "
            "のJSON形式が不正です。"
        ) from error

    candidates = data.get(
        "candidates",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        raise ValueError(
            "candidates は配列にしてください。"
        )

    candidates = [
        item
        for item in candidates
        if isinstance(item, dict)
    ]

    candidates.sort(
        key=lambda item: int(
            item.get(
                "article_priority",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    return candidates[
        :MAX_ARTICLE_CANDIDATES
    ]


def evaluate_candidate(
    candidate: dict[str, Any],
) -> dict[str, Any]:

    program_name = str(
        candidate.get(
            "program_name",
            "",
        )
    ).strip()

    category = str(
        candidate.get(
            "offer_category",
            "",
        )
    ).strip()

    reward_value = float(
        candidate.get(
            "reward_value",
            0,
        )
        or 0
    )

    network = str(
        candidate.get(
            "network",
            "",
        )
    ).strip()

    keyword_candidates = (
        candidate.get(
            "keyword_candidates",
            [],
        )
    )

    if not isinstance(
        keyword_candidates,
        list,
    ):
        keyword_candidates = []

    print(
        "\n[Affiliate Keyword Evaluation] "
        f"{program_name} を評価中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        tools=[
            {
                "type": "web_search",
            }
        ],
        instructions=(
            "あなたは日本語メディアAlsivoの"
            "SEO・Affiliate記事企画担当です。"

            "与えられたAffiliate案件について、"
            "候補キーワードを実際のWeb検索結果を使って"
            "評価してください。"

            "検索ボリュームの具体的な数値を"
            "推測してはいけません。"

            "代わりに、検索結果の存在、"
            "関連検索ニーズ、競合サイトの種類、"
            "検索意図の明確さ等から"
            "需要の強さを0～100点で評価してください。"

            "competition_opportunity_scoreは、"
            "競合が弱くAlsivoが入り込めそうなほど"
            "高得点にしてください。"

            "commercial_intent_scoreは、"
            "比較、料金、評判、申込検討など"
            "成果につながりやすい検索意図ほど"
            "高得点にしてください。"

            "topic_fit_scoreは、"
            "AIツール・SaaS・生成AI・"
            "デジタル生産性を扱うAlsivoとの"
            "テーマ適合度です。"

            "overall_scoreは単純平均ではなく、"
            "Affiliate収益につながる可能性を重視して"
            "総合判断してください。"

            "目安として、"
            "80点以上はQUEUE_ARTICLE、"
            "60～79点はHOLD、"
            "59点以下はREJECTとしてください。"

            "ただし明確な収益機会があり、"
            "検索意図と案件が非常に一致する場合は、"
            "合理的な理由を示した上で"
            "80点未満でもQUEUE_ARTICLEとして構いません。"

            "同一案件について似たキーワードが"
            "カニバリゼーションを起こす場合は、"
            "最も強い1キーワードを主軸にし、"
            "他の語はrelated_keywordsへ統合してください。"

            "『評判』『口コミ』のように"
            "意図がほぼ同じキーワードは、"
            "可能なら1記事に統合してください。"

            "suggested_titleは日本語SEO記事として"
            "自然なタイトル案にしてください。"

            "target_lengthは競合内容と検索意図に応じて"
            "現実的な記事文字数を設定してください。"
        ),
        input=(
            "以下のAffiliate案件について"
            "新規記事候補を評価してください。\n\n"
            f"案件名：{program_name}\n"
            f"カテゴリ：{category}\n"
            f"ASP：{network}\n"
            f"成果報酬：{reward_value}円\n"
            "候補キーワード：\n"
            + "\n".join(
                f"- {keyword}"
                for keyword in keyword_candidates
            )
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "affiliate_keyword_evaluation",
                "schema": KEYWORD_EVALUATION_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            f"{program_name} のキーワード評価結果を"
            "取得できませんでした。"
        )

    try:
        return json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{program_name} の評価結果を"
            "JSON変換できませんでした。"
        ) from error


def flatten_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    flattened = []

    for result in results:

        program_name = str(
            result.get(
                "program_name",
                "",
            )
        )

        evaluations = result.get(
            "evaluations",
            [],
        )

        if not isinstance(
            evaluations,
            list,
        ):
            continue

        for item in evaluations:

            if not isinstance(
                item,
                dict,
            ):
                continue

            flattened.append(
                {
                    "program_name": program_name,
                    **item,
                }
            )

    flattened.sort(
        key=lambda item: int(
            item.get(
                "overall_score",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    return flattened


def save_results(
    results: list[dict[str, Any]],
    ranking: list[dict[str, Any]],
) -> Path:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "results": results,
                "ranking": ranking,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_ranking(
    ranking: list[dict[str, Any]],
) -> None:

    print(
        "\n===== Affiliate Keyword Ranking =====\n"
    )

    if not ranking:
        print(
            "記事化候補キーワードはありません。"
        )
        return

    for index, item in enumerate(
        ranking,
        start=1,
    ):

        print(
            f"[{index}] "
            f"{item['keyword']} "
            f"({item['overall_score']}点)"
        )

        print(
            "    program: "
            f"{item['program_name']}"
        )

        print(
            "    intent: "
            f"{item['search_intent']}"
        )

        print(
            "    demand: "
            f"{item['demand_score']}"
        )

        print(
            "    SEO opportunity: "
            f"{item['competition_opportunity_score']}"
        )

        print(
            "    commercial intent: "
            f"{item['commercial_intent_score']}"
        )

        print(
            "    topic fit: "
            f"{item['topic_fit_score']}"
        )

        print(
            "    action: "
            f"{item['recommended_action']}"
        )

        print(
            "    title: "
            f"{item['suggested_title']}"
        )

        print(
            "    target length: "
            f"{item['target_length']}"
        )

        print(
            "    reason: "
            f"{item['reason']}"
        )

        print()


def main() -> None:

    candidates = (
        load_candidates()
    )

    if not candidates:
        print(
            "\n===== Affiliate Keyword Ranking =====\n"
        )
        print(
            "評価対象のAffiliate記事候補はありません。"
        )
        return

    results = []

    for candidate in candidates:

        result = (
            evaluate_candidate(
                candidate
            )
        )

        results.append(
            result
        )

    ranking = (
        flatten_results(
            results
        )
    )

    filepath = (
        save_results(
            results,
            ranking,
        )
    )

    print_ranking(
        ranking
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()