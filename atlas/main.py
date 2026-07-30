from agents.planner import create_article_plan
from agents.publisher import publish_article
from agents.reviewer import review_article
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

        print("\n[Reviewer] 記事を確認中...\n")
        review = review_article(plan, article)

        print("\n===== 記事完成 =====\n")
        print(f"タイトル：{article['title']}")
        print(f"説明文：{article['description']}")
        print(f"カテゴリー：{article['category']}")
        print(f"タグ：{', '.join(article['tags'])}")

        print("\n===== レビュー結果 =====\n")
        print(f"公開判定：{'承認' if review['approved'] else '要修正'}")
        print(f"品質スコア：{review['score']} / 100")
        print(f"講評：{review['summary']}")

        if review["issues"]:
            print("\n問題点")
            for issue in review["issues"]:
                print(f"- {issue}")

        if review["improvement_instructions"]:
            print("\n修正指示")
            for instruction in review["improvement_instructions"]:
                print(f"- {instruction}")

        if review["approved"]:
            print("\n[Publisher] MDXファイルを保存中...")
            filepath = publish_article(article)

            print("\n===== 保存完了 =====")
            print(f"保存先：{filepath}")
        else:
            print("\n記事は要修正のため、保存しませんでした。")

    except Exception as error:
        print(f"\n処理に失敗しました：{error}")


if __name__ == "__main__":
    main()