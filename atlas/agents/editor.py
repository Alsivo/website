import json
from typing import Any

from openai import OpenAI

from config import (
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY
)


EDITORIAL_DECISION_SCHEMA: dict[
    str,
    Any,
] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "new_article",
                "rewrite_article",
                "wait",
            ],
        },
        "priority_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
        },
        "reason": {
            "type": "string",
        },
        "target_keyword": {
            "type": "string",
        },
        "target_slug": {
            "type": "string",
        },
        "target_title": {
            "type": "string",
        },
        "search_intent": {
            "type": "string",
        },
        "recommended_focus": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 8,
        },
        "target_queries": {
            "type": "array",
            "items": {
                "type": "string",
            },
            "minItems": 0,
            "maxItems": 10,
        },
        "monetization_opportunity": {
            "type": "string",
        },
        "expected_effect": {
            "type": "string",
        },
        "affiliate_service": {
            "type": "string",
        },
        "content_angle": {
            "type": "string",
        },
        "target_reader_problem": {
            "type": "string",
        },
        "reader_after_state": {
            "type": "string",
        },
    },
    "required": [
        "action",
        "priority_score",
        "reason",
        "target_keyword",
        "target_slug",
        "target_title",
        "search_intent",
        "recommended_focus",
        "target_queries",
        "monetization_opportunity",
        "expected_effect",
        "affiliate_service",
        "content_angle",
        "target_reader_problem",
        "reader_after_state",
    ],
    "additionalProperties": False,
}


def make_editorial_decision(
    editorial_context: dict[str, Any],
) -> dict[str, Any]:
    """サイト状況から次に行う施策をAIが判断する。"""

    context_text = json.dumps(
        editorial_context,
        ensure_ascii=False,
        indent=2,
    )

    print(
        "[Editor] "
        "次の編集施策を判断中..."
    )

    response = client.responses.create(
        model=MODEL,
        store=False,
        instructions=(
            "あなたはAIメディアAlsivoの編集長です。"
            "目的はPVを増やすだけではなく、"
            "検索ユーザーへ価値を提供しながら"
            "中長期的な検索流入と収益性を高めることです。"

            "渡されたSearch Consoleデータ、"
            "既存記事、未処理キーワード、"
            "アフィリエイト案件を総合して、"
            "次に行うべき施策を1つだけ選んでください。"

            "actionはnew_article、rewrite_article、waitの"
            "いずれかです。"

            "Search Consoleデータが少ない場合は、"
            "無理にリライトを選ばず、"
            "検索意図が明確な未処理キーワードから"
            "新規記事を優先してください。"

            "seo_action_planはSEO Feedback Engineが"
            "Search Console実績をもとに算出した"
            "安全側の改善判断です。"

            "seo_action_planでplanned_actionがwaitの"
            "記事は、SEOデータ不足を意味します。"
            "その記事をSearch Console上の理由だけで"
            "rewrite_articleに選ばないでください。"

            "planned_actionがrewriteの記事は、"
            "リライト候補として強く考慮してください。"

            "planned_actionがstrengthenの記事は、"
            "全面的な再設計よりも既存内容を活かした"
            "部分的改善が適しています。"

            "planned_actionがtitle_onlyの記事は、"
            "本文の全面リライトではなく、"
            "タイトルやdescription改善が"
            "主目的であることを考慮してください。"

            "seo_action_planがavailableの場合、"
            "既存記事をrewrite_articleに選択する際は、"
            "必ず対象slugのSEO Action Planを確認してください。"

            "対象slugのplanned_actionがwaitの場合は、"
            "Search Console上の順位や検索語が魅力的でも"
            "rewrite_articleを選択してはいけません。"

            "また、seo_action_planに対象slugが存在しない場合も、"
            "Search Consoleデータだけを理由として"
            "rewrite_articleを選択してはいけません。"

            "現段階でrewrite_articleを自動選択してよいのは、"
            "原則としてplanned_actionがrewriteの"
            "記事だけです。"

            "planned_actionがstrengthenまたはtitle_onlyの場合は、"
            "専用の部分改善処理が未実装のため、"
            "現時点ではrewrite_articleを選ばず、"
            "新規記事またはwaitを優先してください。"
            
            "既存記事が掲載順位4〜20位程度で、"
            "一定の表示回数がある場合は、"
            "リライトによって上位表示できる可能性を"
            "重視してください。"

            "表示回数が多いのにCTRが低い場合は、"
            "タイトルやdescription改善の価値を"
            "考慮してください。"

            "アフィリエイト案件があることだけを理由に、"
            "検索意図と無関係な記事を選ばないでください。"

            "priority_affiliate_candidatesは、"
            "管理画面へ登録されたアフィリエイト案件です。"
            "未記事化の承認済み案件を最優先し、"
            "次に未記事化の申請予定・申請中案件を優先してください。"
            "すでに記事化済みの案件も候補から外さず、"
            "covered_articlesと検索意図が重ならない"
            "別の悩み、対象読者、利用場面、判断課題を選び、"
            "新しい記事として展開してください。"

            "案件記事の切り口は、原則として"
            "『案件そのものの魅力を前向きに紹介する記事』または"
            "『その案件で解決できる具体的な悩みに着目する記事』の"
            "どちらかにしてください。"
            "競合サービスや代替案を紹介・推奨する企画は選ばないでください。"
            "事実性は維持しつつ、細かな不利条件を結論の中心に置かず、"
            "メリット、活用場面、向いている人、得られる変化を"
            "読者に役立つ形で具体化してください。"

            "アフィリエイト案件が1件以上ある場合、"
            "新規記事候補は原則としてその案件に関連するテーマを"
            "通常の未処理キーワードより優先してください。"
            "ただし、読者の具体的な悩みと検索意図が成立せず、"
            "既存記事とも明確に差別化できない場合は"
            "無理に記事を作らないでください。"

            "advertising_readyがfalseの案件も記事候補にできます。"
            "その場合は広告掲載を前提にせず、"
            "読者に役立つ通常記事として企画してください。"
            "承認後に広告を追加できる設計とします。"

            "同じ案件を連続して扱う場合は、"
            "タイトルだけを変えるのではなく、"
            "検索意図、target_reader_problem、content_angle、"
            "読者が記事後にできることを明確に変えてください。"

            "affiliate_serviceには選択した案件のtool_nameを入れてください。"
            "content_angleには既存記事と重複しない今回固有の切り口を、"
            "target_reader_problemには読者の具体的な悩みを、"
            "reader_after_stateには記事を読んだ後に判断・実行できることを"
            "それぞれ具体的に入れてください。"
            "案件を使わない判断の場合、これら4項目は空文字にしてください。"

            "収益性は判断要素の1つですが、"
            "読者価値と検索意図を優先してください。"

            "新規記事の場合はtarget_keywordへ"
            "未処理キーワード、または"
            "priority_affiliate_candidatesを基に作った、"
            "案件名と今回固有の切り口が分かる検索キーワードを"
            "1つ入れてください。"
            "target_slugは空文字にしてください。"

            "リライトの場合はtarget_slugへ"
            "既存記事のslugを入れてください。"
            "target_keywordは主に強化すべき検索語を"
            "入れてください。"

            "waitは、未処理キーワードもなく、"
            "改善に値するSearch Consoleデータも"
            "ない場合だけ選択してください。"

            "根拠のない検索ボリュームや売上予測を"
            "作らないでください。"
        ),
        input=(
            "以下が現在のAlsivoの状況です。\n\n"
            f"{context_text}"
        ),
        text={
            "format": {
                "type": "json_schema",
                "name":
                    "alsivo_editorial_decision",
                "schema":
                    EDITORIAL_DECISION_SCHEMA,
                "strict": True,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError(
            "編集判断を取得できませんでした。"
        )

    try:
        return json.loads(
            response.output_text
        )
    except json.JSONDecodeError as error:
        raise RuntimeError(
            "編集判断のJSON変換に"
            "失敗しました。"
        ) from error
