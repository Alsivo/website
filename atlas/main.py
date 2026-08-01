from agents.planner import create_article_plan
from agents.publisher import publish_article
from agents.reviewer import review_article
from agents.writer import generate_article
from engines.keyword_queue import (
    KeywordItem,
    get_next_keyword_item,
    mark_keyword_processed,
)


def select_topic() -> tuple[str, KeywordItem | None]:
    print("実行モードを選択してください。")
    print("1: テーマを手入力")
    print("2: data-content-engineから自動選択")

    mode = input("番号：").strip()

    if mode == "1":
        topic = input("テーマ：").strip()

        if not topic:
            raise ValueError("テーマを入力してください。")

        return topic, None

    if mode == "2":
        item = get_next_keyword_item()

        if item is None:
            raise RuntimeError(
                "未処理のキーワードがありません。"
            )

        print("\n===== 自動選択された記事企画 =====")
        print(f"キーワード：{item.keyword}")
        print(f"目安文字数：{item.target_length}")
        print(
            "関連キーワード："
            + ", ".join(item.related_keywords)
        )
        print(f"検索意図：{item.search_intent}")

        topic = (
            f"メインキーワード：{item.keyword}\n"
            f"目安文字数：{item.target_length}文字\n"
            f"関連キーワード："
            f"{', '.join(item.related_keywords)}\n"
            f"検索意図：{item.search_intent}"
        )

        return topic, item

    raise ValueError("1または2を入力してください。")


def main() -> None:
    try:
        topic, keyword_item = select_topic()

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
        print(
            "公開判定："
            f"{'承認' if review['approved'] else '要修正'}"
        )
        print(f"品質スコア：{review['score']} / 100")
        print(f"講評：{review['summary']}")

        if review["issues"]:
            print("\n問題点")
            for issue in review["issues"]:
                print(f"- {issue}")

        if review["improvement_instructions"]:
            print("\n修正指示")
            for instruction in review[
                "improvement_instructions"
            ]:
                print(f"- {instruction}")

        if not review["approved"]:
            print(
                "\n記事は要修正のため、"
                "保存・処理済み登録を行いませんでした。"
            )
            return

        print("\n[Publisher] MDXファイルを保存中...")
        filepath = publish_article(article)

        if keyword_item is not None:
            mark_keyword_processed(
                keyword_item,
                filepath,
            )

        print("\n===== 保存完了 =====")
        print(f"保存先：{filepath}")

    except Exception as error:
        print(f"\n処理に失敗しました：{error}")


if __name__ == "__main__":
    main()