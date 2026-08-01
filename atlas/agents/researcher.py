from typing import Any

from openai import OpenAI

from config import (
    MAX_WEB_SEARCH_CALLS,
    MODEL,
    OPENAI_API_KEY,
    WEB_SEARCH_CONTEXT_SIZE,
)


client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=180.0,
    max_retries=2,
)


def extract_sources(response: Any) -> list[dict[str, str]]:
    """Responses APIのURL citationから出典一覧を取得する。"""

    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for output_item in response.output:
        if getattr(output_item, "type", None) != "message":
            continue

        for content_item in getattr(output_item, "content", []):
            annotations = getattr(content_item, "annotations", [])

            for annotation in annotations:
                if getattr(annotation, "type", None) != "url_citation":
                    continue

                url = getattr(annotation, "url", "")
                title = getattr(annotation, "title", "")

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                sources.append(
                    {
                        "title": title or url,
                        "url": url,
                    }
                )

    return sources


def research_topic(topic: str) -> dict[str, Any]:
    """記事テーマについてWeb検索し、執筆用の調査資料を作る。"""

    cleaned_topic = topic.strip()

    if not cleaned_topic:
        raise ValueError("調査テーマを入力してください。")

    print("[Researcher] Web検索を開始...")

    response = client.responses.create(
        model=MODEL,
        store=False,
        tools=[
            {
                "type": "web_search",
                "search_context_size": WEB_SEARCH_CONTEXT_SIZE,
                "user_location": {
                    "type": "approximate",
                    "country": "JP",
                    "timezone": "Asia/Tokyo",
                },
            }
        ],
        tool_choice="required",
        max_tool_calls=MAX_WEB_SEARCH_CALLS,
        instructions=(
            "あなたはAIメディアAlsivoの調査担当者です。"
            "記事作成前の事実調査を行ってください。"
            "可能な限り公式サイト、公式ドキュメント、"
            "公的機関、一次情報を優先してください。"
            "料金、機能、製品名、プラン名、提供条件、日付など、"
            "変更されやすい情報を重点的に確認してください。"
            "確認できない情報は推測せず、確認できないと明記してください。"
            "広告的な表現や根拠のない評価は避けてください。"
            "日本語で調査結果をまとめてください。"
        ),
        input=(
            "次のテーマの記事を作成するため、最新情報を調査してください。\n\n"
            f"テーマ：{cleaned_topic}\n\n"
            "以下の項目を整理してください。\n"
            "1. 現在確認できる主要事実\n"
            "2. 料金・プラン・機能・提供条件\n"
            "3. 初心者が注意すべき点\n"
            "4. 情報が変動する可能性が高い部分\n"
            "5. 記事で断定を避けるべき部分\n"
        ),
    )

    print("[Researcher] Web検索完了！")

    summary = response.output_text.strip()

    if not summary:
        raise RuntimeError("Web調査結果を取得できませんでした。")

    sources = extract_sources(response)

    if not sources:
        print(
            "[Researcher] 注意：出典URLを取得できませんでした。"
        )

    return {
        "summary": summary,
        "sources": sources,
    }