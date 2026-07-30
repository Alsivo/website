from agents.writer import generate_article


def main() -> None:
    topic = input("テーマ：").strip()

    if not topic:
        print("テーマを入力してください。")
        return

    print("\nAI執筆中...\n")

    try:
        article = generate_article(topic)
    except Exception as error:
        print(f"記事生成に失敗しました：{error}")
        return

    print(f"タイトル：{article['title']}")
    print(f"説明文：{article['description']}")
    print(f"カテゴリー：{article['category']}")
    print(f"タグ：{', '.join(article['tags'])}")
    print("\n--- 本文 ---\n")
    print(article["content"])


if __name__ == "__main__":
    main()