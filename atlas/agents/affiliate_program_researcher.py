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


PROGRAM_RESEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "service": {
            "type": "string",
        },
        "program_found": {
            "type": "boolean",
        },
        "program_type": {
            "type": [
                "string",
                "null",
            ],
            "enum": [
                "affiliate",
                "referral",
                "partner",
                "creator",
                "other",
                None,
            ],
        },
        "program_name": {
            "type": "string",
        },
        "network": {
            "type": "string",
        },
        "program_url": {
            "type": "string",
        },
        "commission": {
            "type": "string",
        },
        "cookie_duration": {
            "type": "string",
        },
        "target_country": {
            "type": "string",
        },
        "application_required": {
            "type": [
                "boolean",
                "null",
            ],
        },
        "research_notes": {
            "type": "string",
        },
        "sources": {
            "type": "array",
            "maxItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                    },
                    "url": {
                        "type": "string",
                    },
                    "source_type": {
                        "type": "string",
                        "enum": [
                            "official",
                            "affiliate_network",
                            "help",
                            "third_party",
                        ],
                    },
                },
                "required": [
                    "title",
                    "url",
                    "source_type",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "service",
        "program_found",
        "program_type",
        "program_name",
        "network",
        "program_url",
        "commission",
        "cookie_duration",
        "target_country",
        "application_required",
        "research_notes",
        "sources",
    ],
    "additionalProperties": False,
}


def research_affiliate_program(
    service: str,
    official_url: str = "",
    context: str = "",
) -> dict[str, Any]:
    """指定サービスのAffiliate ProgramをWeb調査する。"""

    print(
        "\n[Affiliate Program Research] "
        f"{service}を調査中..."
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
            "あなたはAlsivoのAffiliate Program調査担当です。"

            "指定されたサービスについて、"
            "現在利用可能なAffiliate Program、"
            "Referral Program、Partner Program、"
            "Creator Program等をWeb検索で調査してください。"

            "必ず実際のWeb検索結果を根拠にしてください。"

            "OpenAIモデルの記憶だけで"
            "案件の存在を断定しないでください。"

            "公式サイト、公式ヘルプ、"
            "公式Affiliate/Partnerページを最優先してください。"

            "次にImpact、PartnerStack、Awin、CJ、"
            "Rakuten Advertising等の"
            "アフィリエイトネットワーク情報を確認してください。"

            "第三者ブログだけを根拠に"
            "program_found=trueにしないでください。"

            "公式または信頼できるネットワーク上で"
            "現在利用可能な案件を確認できた場合のみ"
            "program_found=trueにしてください。"

            "案件が見つからなかった場合は"
            "program_found=falseにしてください。"

            "報酬、Cookie期間、対象国などが"
            "確認できない場合は空文字にしてください。"

            "推測で数値を補完しないでください。"

            "program_urlには申請・紹介制度を"
            "確認できる最も直接的なURLを入れてください。"

            "sourcesには実際に判断根拠として使った"
            "Webページだけを記録してください。"

            "サービス名が他社サービスと重複する場合は、"
            "公式URLと記事文脈を使って対象を特定してください。"

            "公式URLまたは記事文脈から対象サービスを"
            "一意に判断できる場合は、"
            "ユーザーへの確認を要求せず調査を続行してください。"
        ),
        input=(
            "以下のサービスについて、"
            "現在利用可能なアフィリエイトまたは"
            "紹介制度を調査してください。\n\n"
            f"サービス名：{service}\n"
            f"公式URL：{official_url or '未指定'}\n"
            f"記事文脈：{context or '未指定'}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "affiliate_program_research",
                "schema": PROGRAM_RESEARCH_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            f"{service}の案件調査結果を"
            "取得できませんでした。"
        )

    try:
        return json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{service}の案件調査結果を"
            "JSONへ変換できませんでした。"
        ) from error