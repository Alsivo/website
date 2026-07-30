from agents.planner import create_article_plan
from agents.writer import generate_article


def main() -> None:
    topic = input("テーマ：").strip()

    if not topic:
        print("テーマを入力してください。")
        return

    try:
        print("\n[Planner] 記事企画を作成中...\n")
        plan = create_article_plan(topic)

        print(f"仮タイトル：{plan['suggested_title']}")
        print(f"検索意図：{plan['search_intent']}")

        print("\n[Writer] 記事を執筆中...\n")
        article = generate_article(plan)

    except Exception as error:
        print(f"\n処理に失敗しました：{error}")
        return

    print("\n===== 記事完成 =====\n")
    print(f"タイトル：{article['title']}")
    print(f"説明文：{article['description']}")
    print(f"カテゴリー：{article['category']}")
    print(f"タグ：{', '.join(article['tags'])}")
    print("\n--- 本文 ---\n")
    print(article["content"])


if __name__ == "__main__":
    main()