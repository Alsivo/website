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
            "maxItems": 10,
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
    """指定サービスの収益化案件をWeb横断調査する。"""

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
            "あなたは日本語メディアAlsivoの"
            "Affiliate Program調査担当です。"

            "目的は、指定サービスを日本のWebメディアから"
            "実際に収益化できる案件が現在存在するかを"
            "Web検索で確認することです。"

            "必ず実際のWeb検索結果を根拠にしてください。"
            "モデルの記憶だけで案件の存在を断定しないでください。"

            "調査は以下の順序で行ってください。"

            "【1. 公式直契約】"
            "サービス公式サイト、公式ヘルプ、"
            "Affiliate、Referral、Partner、Creator、"
            "Ambassador等の公式制度を確認してください。"

            "【2. 日本国内ASP】"
            "以下のASPに当該サービスまたは関連案件が"
            "存在する可能性を積極的に検索してください。"
            "A8.net、もしもアフィリエイト、"
            "バリューコマース、afb、"
            "アクセストレード、JANet、"
            "Link-A、レントラックス。"

            "検索時にはサービス名だけでなく、"
            "『サービス名 A8』"
            "『サービス名 A8.net』"
            "『サービス名 もしも』"
            "『サービス名 バリューコマース』"
            "『サービス名 afb』"
            "『サービス名 アクセストレード』"
            "『サービス名 アフィリエイト』"
            "『サービス名 ASP』"
            "等も確認してください。"

            "【3. 海外ネットワーク】"
            "Impact、PartnerStack、Awin、CJ、"
            "Rakuten Advertising、ShareASale等も"
            "必要に応じて確認してください。"

            "日本国内ASPについて、"
            "検索結果や公式公開ページから案件存在を"
            "十分に確認できない場合は、"
            "存在すると断定しないでください。"

            "ログイン後のASP管理画面でしか"
            "案件有無を確認できない可能性がある場合は、"
            "research_notesに"
            "『ASP管理画面で要確認』"
            "と明記してください。"

            "複数の案件候補が見つかった場合は、"
            "日本在住のAlsivo運営者が実際に利用しやすく、"
            "金銭報酬があり、"
            "現在申請可能である可能性が最も高い案件を"
            "代表案件として返してください。"

            "Referral Programでも、"
            "紹介者に現金・金銭相当の報酬がない場合は、"
            "通常のAffiliate Programより優先しないでください。"

            "企業向けReseller、Technology Partner、"
            "Agency Partner、Consulting Partner等で、"
            "一般Webメディアの成果報酬型紹介に"
            "利用できない制度は、"
            "通常のAffiliate案件として扱わないでください。"

            "第三者ブログだけを根拠に"
            "program_found=trueにしないでください。"

            "公式サイト、公式ASPページ、"
            "信頼できるAffiliate Network上で"
            "現在利用可能な案件を確認できた場合を"
            "program_found=trueの基本条件としてください。"

            "ただし、公式ASP管理画面内のみで"
            "確認可能と思われる案件については、"
            "公開Webで存在を裏付けられない限り"
            "program_found=falseとし、"
            "research_notesに"
            "『A8.net等のASP管理画面で要確認』"
            "と記載してください。"

            "報酬、Cookie期間、対象国、"
            "承認条件などが確認できない場合は"
            "空文字にしてください。"

            "推測で金額・割合・Cookie期間を"
            "補完しないでください。"

            "networkには、"
            "A8.net、もしもアフィリエイト、"
            "バリューコマース、Impact等、"
            "確認できた運営ネットワーク名を入れてください。"
            "公式直契約の場合は"
            "Directまたは公式制度名を入れても構いません。"

            "program_urlには、"
            "可能な限り申請ページまたは"
            "案件を確認できる最も直接的なURLを入れてください。"

            "sourcesには、"
            "実際に判断根拠として使ったページだけを"
            "記録してください。"

            "source_typeは、"
            "公式サイトならofficial、"
            "ASP・Affiliate Networkならaffiliate_network、"
            "公式ヘルプならhelp、"
            "その他はthird_partyとしてください。"

            "サービス名が他社サービスと重複する場合は、"
            "公式URLと記事文脈を使って対象を特定してください。"

            "公式URLまたは記事文脈から対象サービスを"
            "一意に判断できる場合は、"
            "ユーザーへの確認を要求せず調査を続行してください。"

            "research_notesには最後に必ず、"
            "『日本向け収益化判断：』として、"
            "次のいずれかを簡潔に記載してください。"
            "『申請候補』"
            "『ASP管理画面で要確認』"
            "『一般メディア向けではない』"
            "『現金報酬なし』"
            "『案件未発見』"
        ),
        input=(
            "以下のサービスについて、"
            "日本のWebメディアAlsivoが利用できる"
            "現在の収益化案件を調査してください。\n\n"
            f"サービス名：{service}\n"
            f"公式URL：{official_url or '未指定'}\n"
            f"記事文脈：{context or '未指定'}\n\n"
            "公式制度だけでなく、"
            "A8.net、もしもアフィリエイト、"
            "バリューコマース等の日本国内ASPも"
            "必ず調査対象に含めてください。"
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