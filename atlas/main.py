from agents.planner import create_article_plan


def main() -> None:
    topic = input("テーマ：").strip()

    if not topic:
        print("テーマを入力してください。")
        return

    print("\n記事企画を作成中...\n")

    try:
        plan = create_article_plan(topic)
    except Exception as error:
        print(f"記事企画の作成に失敗しました：{error}")
        return

    print(f"メインキーワード：{plan['primary_keyword']}")
    print(f"検索意図：{plan['search_intent']}")
    print(f"想定読者：{plan['target_reader']}")
    print(f"読者の悩み：{plan['reader_problem']}")
    print(f"記事の目的：{plan['article_goal']}")
    print(f"仮タイトル：{plan['suggested_title']}")

    print("\n見出し構成")
    for index, heading in enumerate(plan["outline"], start=1):
        print(f"{index}. {heading}")

    print("\n関連キーワード")
    for keyword in plan["related_keywords"]:
        print(f"- {keyword}")


if __name__ == "__main__":
    main()