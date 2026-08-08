import json
from typing import Any

from openai import OpenAI

from config import (
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY,
)


OPPORTUNITY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                    },
                    "service": {
                        "type": [
                            "string",
                            "null",
                        ],
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "action": {
                        "type": "string",
                        "enum": [
                            "find_program",
                            "wait",
                            "improve_content",
                            "no_opportunity",
                        ],
                    },
                    "reason": {
                        "type": "string",
                    },
                },
                "required": [
                    "slug",
                    "service",
                    "priority",
                    "action",
                    "reason",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "decisions",
    ],
    "additionalProperties": False,
}


def evaluate_affiliate_opportunities(
    opportunities: dict[str, Any],
) -> dict[str, Any]:
    """Affiliate Opportunity候補をAIで再評価する。"""

    print(
        "\n[Affiliate Opportunity AI] "
        "収益化候補を評価中...\n"
    )

    input_text = json.dumps(
        opportunities,
        ensure_ascii=False,
        indent=2,
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの"
            "アフィリエイト収益化担当編集者です。"

            "各記事について、"
            "アフィリエイト案件を探す価値があるかを"
            "慎重に評価してください。"

            "記事タイトル、対象サービス、"
            "ルールベースpriority、"
            "Search Consoleデータ、"
            "affiliate_statusを判断材料にしてください。"

            "料金、価格、プラン比較、サービス比較など、"
            "読者の導入・契約意図が強い記事は"
            "収益化候補として高く評価してください。"

            "ただし、検索表示やアクセスがまだ極端に少なくても、"
            "検索意図が非常に商用的であり、"
            "将来的な収益化価値が高い記事は"
            "find_programを選択して構いません。"

            "affiliate_statusがactiveの場合は、"
            "原則としてfind_programを選ばないでください。"

            "既に案件がactiveなら、"
            "waitまたはimprove_contentを選択してください。"

            "対象サービスが存在しない記事では、"
            "原則としてfind_programを選択しないでください。"

            "記事品質や検索流入改善を先に行うべき場合は"
            "improve_contentを選択してください。"

            "現時点で収益化価値が低い場合は"
            "no_opportunityを選択してください。"

            "serviceには、その記事で最も案件探索を"
            "優先すべきサービスを1つだけ指定してください。"

            "適切なサービスがない場合はnullにしてください。"

            "priorityは0〜100で評価してください。"

            "reasonには、判断理由を日本語で簡潔に記載してください。"

            "すべての記事について必ず1件ずつ判断を返してください。"

            "重要：アフィリエイト案件の存在有無を"
            "入力データにない知識から推測しないでください。"

            "affiliate_status、network、program_nameについては、"
            "渡されたAffiliate Opportunity候補内の情報だけを"
            "事実として扱ってください。"

            "affiliate_statusがnoneの場合は、"
            "案件が存在しないと断定するのではなく、"
            "『現時点の台帳では案件未登録』として扱ってください。"

            "find_programは、"
            "『案件が存在する』という意味ではありません。"
            "『案件の有無を外部調査する価値が高い』"
            "という意味で使用してください。"

            "入力データに存在しないサービス名を"
            "新しく提案しないでください。"

            "Jasper、Grammarly、Otter.aiなど、"
            "候補データに含まれていないサービスを"
            "reasonへ追加しないでください。"

            "現在のアフィリエイト制度についての"
            "外部知識や記憶をreasonへ書かないでください。"

                        "find_programの判定は厳格にしてください。"

            "すべての記事をfind_programにしないでください。"

            "Search Consoleデータがnullで、"
            "かつ単一サービスの料金・プラン比較記事でもない場合は、"
            "原則としてwaitまたはimprove_contentを選択してください。"

            "複数サービス比較記事でSearch Consoleデータがnullの場合は、"
            "原則としてimprove_contentを優先してください。"

            "単一サービスの料金・プラン比較記事は、"
            "Search Consoleデータがnullでも"
            "BOFU意図が明確なためfind_programを選択して構いません。"

            "Search Consoleで表示回数が少なく、"
            "順位も50位より下の場合は、"
            "案件探索よりコンテンツ改善を優先してください。"

            "search_consoleが存在し、"
            "表示回数やクリックが増え始めている記事は"
            "find_programの優先度を上げてください。"

            "find_programは全体の一部に限定してください。"
            "目安として全記事の30〜50%程度までにしてください。"

            "priorityはactionと整合させてください。"
            "find_programは原則70点以上、"
            "improve_contentは50〜79点、"
            "waitは30〜69点、"
            "no_opportunityは0〜49点を目安にしてください。"
        ),
        input=(
            "以下のAffiliate Opportunity候補を"
            "再評価してください。\n\n"
            f"{input_text}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": (
                    "affiliate_opportunity_decisions"
                ),
                "schema": OPPORTUNITY_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "Affiliate Opportunity AIの"
            "評価結果を取得できませんでした。"
        )

    try:
        return json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "Affiliate Opportunity AIの"
            "JSON変換に失敗しました。"
        ) from error