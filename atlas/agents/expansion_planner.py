import json
from typing import Any

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY
)


def build_expansion_prompt(
    queue: list[dict[str, Any]],
    existing_articles: list[dict[str, str]],
) -> str:
    """記事拡張候補をAIに評価させるPromptを作る。"""

    queue_json = json.dumps(
        queue,
        ensure_ascii=False,
        indent=2,
    )

    articles_json = json.dumps(
        existing_articles,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
あなたはSEOメディアAlsivoの編集戦略担当です。

AlsivoはAIツール・生成AIサービスを扱う日本語メディアです。

目的は、
・検索流入を増やす
・記事数を増やす
・既存記事とのカニバリを避ける
・将来的なアフィリエイト収益につなげる
ことです。

以下が現在の記事拡張候補です。

【新記事候補】
{queue_json}

以下が既存記事です。

【既存記事】
{articles_json}

各候補について、次の4つから判断してください。

new_article
→ 独立した検索意図があり、新規記事にする価値が高い。

merge_existing
→ 既存記事へ追記した方がよい。

comparison_article
→ 単独記事より、複数サービス比較記事としてまとめるべき。

skip
→ 現時点では記事化優先度が低い。

特に以下を重視してください。

特に以下を重視してください。

1. 検索意図が独立しているか
2. 既存記事とのカニバリ可能性
3. 記事として十分な情報量を作れるか
4. 商用意図があるか
5. 有料SaaSや導入検討につながるか
6. Alsivoの既存記事群と内部リンクしやすいか
7. 単なる機能名ではなく、独立した記事テーマとして成立するか

重要な制約：

・検索ボリューム、競合数、CPCなどの実測データは与えていません。
・与えられていない検索ボリュームや市場規模を推測して、
  判断理由として断定しないでください。
・「検索ボリュームが高い」「検索数が多い」
  「市場規模が大きい」など、
  入力データに存在しない事実を理由にしてはいけません。
・priorityは、
  検索意図の独立性、
  既存記事との重複、
  商用意図、
  記事としての発展性、
  内部リンク可能性
  を中心に判断してください。
・不明な情報は不明として扱い、
  推測で補完しないでください。

出力はJSONのみ。

形式：

{{
  "decisions": [
    {{
      "topic": "例",
      "action": "new_article",
      "priority": 85,
      "target_keyword": "例 料金",
      "suggested_title": "記事タイトル案",
      "reason": "判断理由",
      "related_existing_slugs": [
        "existing-slug"
      ]
    }}
  ]
}}

priorityは0〜100。

記事数を増やすことは重要ですが、
薄い記事や既存記事とほぼ同じ記事を量産しないでください。
"""

def plan_content_expansion(
    queue: list[dict[str, Any]],
    existing_articles: list[dict[str, str]],
) -> dict[str, Any]:
    """AIに記事拡張方針を判断させる。"""

    prompt = build_expansion_prompt(
        queue,
        existing_articles,
    )

    print(
        "\n[Expansion Planner] "
        "新記事候補を評価中..."
    )

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    text = response.output_text.strip()

    if text.startswith("```"):
        text = text.strip("`")

        if text.startswith("json"):
            text = text[4:].strip()

    try:
        data = json.loads(
            text
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "Expansion Plannerの"
            "JSON解析に失敗しました。\n"
            f"AI応答：{text}"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Expansion Plannerの"
            "最上位JSONが不正です。"
        )

    decisions = data.get(
        "decisions"
    )

    if not isinstance(
        decisions,
        list,
    ):
        raise ValueError(
            "Expansion Plannerのdecisionsが"
            "配列ではありません。"
        )

    return data