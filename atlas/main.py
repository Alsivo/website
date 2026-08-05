from agents.image_creator import (
    generate_article_image,
)
from agents.planner import create_article_plan
from agents.publisher import publish_article
from agents.researcher import research_topic
from agents.reviewer import review_article
from agents.writer import generate_article, revise_article
from config import MAX_REVISION_ATTEMPTS, MIN_REVIEW_SCORE
from utils.git_publisher import publish_generated_files
from engines.keyword_queue import (
    STATE_FILE,
    KeywordItem,
    get_next_keyword_item,
    mark_keyword_processed,
)
from engines.affiliate_manager import (
    print_affiliate_selection,
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
        print(
            "\n[Affiliate Manager] "
            "広告案件を確認中...\n"
        )

        print_affiliate_selection()

        topic, keyword_item = select_topic()

        print("\n[Researcher] 最新情報を調査中...\n")
        research = research_topic(topic)

        print("\n===== Web調査結果 =====")
        print(research["summary"])

        print("\n===== 取得した出典 =====")

        if research["sources"]:
            for index, source in enumerate(
                research["sources"],
                start=1,
            ):
                print(
                    f"{index}. {source['title']}\n"
                    f"   {source['url']}"
                )
        else:
            print("出典URLを取得できませんでした。")

        print("\n[Planner] 記事企画を作成中...\n")
        plan = create_article_plan(topic)

        print(f"仮タイトル：{plan['suggested_title']}")
        print(f"検索意図：{plan['search_intent']}")

        print("\n[Writer] 記事を執筆中...\n")
        article = generate_article(
            plan,
            research,
        )

        review = None

        for attempt in range(MAX_REVISION_ATTEMPTS + 1):
            print(
                "\n[Reviewer] 記事を確認中 "
                f"({attempt + 1}/"
                f"{MAX_REVISION_ATTEMPTS + 1})...\n"
            )

            review = review_article(
                plan,
                article,
                research,
            )

            print("\n===== レビュー結果 =====\n")
            print(
                "公開判定："
                f"{'承認' if review['approved'] else '要修正'}"
            )
            print(
                f"品質スコア：{review['score']} / 100"
            )
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

            approved = (
                review["approved"]
                and review["score"] >= MIN_REVIEW_SCORE
            )

            if approved:
                break

            if attempt >= MAX_REVISION_ATTEMPTS:
                break

            print(
                "\n[Writer] 自動修正を開始します "
                f"({attempt + 1}/"
                f"{MAX_REVISION_ATTEMPTS})...\n"
            )

            article = revise_article(
                plan=plan,
                research=research,
                article=article,
                review=review,
            )

        if review is None:
            raise RuntimeError(
                "レビュー結果を取得できませんでした。"
            )

        approved = (
            review["approved"]
            and review["score"] >= MIN_REVIEW_SCORE
        )

        print("\n===== 最終記事 =====\n")
        print(f"タイトル：{article['title']}")
        print(f"説明文：{article['description']}")
        print(f"カテゴリー：{article['category']}")
        print(f"タグ：{', '.join(article['tags'])}")

        recommended_tools = article.get(
            "recommended_tools",
            [],
        )

        print(
            "紹介対象："
            + (
                ", ".join(recommended_tools)
                if recommended_tools
                else "なし"
            )
        )

        print(
            "使用出典："
            + ", ".join(article["used_source_ids"])
        )

        if not approved:
            print(
                "\n最大修正回数に達しました。"
                "記事は保存せず、"
                "キーワードも未処理のまま残します。"
            )
            return

        print(
            "\n[Image Agent] "
            "アイキャッチ画像を生成中..."
        )

        image_url, image_file_path = (
            generate_article_image(article)
        )

        article["image"] = image_url

        print(
            f"画像URL：{article['image']}"
        )

        print(
            "\n[Publisher] "
            "MDXファイルを保存中..."
        )

        filepath = publish_article(
            article,
            research,
        )

        if keyword_item is not None:
            mark_keyword_processed(
                keyword_item,
                filepath,
            )

        print("\n===== 保存完了 =====")
        print(f"保存先：{filepath}")

        print(
            "\n[Git Publisher] "
            "自動公開処理を確認中..."
        )

        state_path = (
            STATE_FILE
            if keyword_item is not None
            else None
        )

        pushed = publish_generated_files(
            article_path=filepath,
            image_path=image_file_path,
            state_path=state_path,
        )

        if pushed:
            print(
                "\n===== 自動公開完了 ====="
            )
            print(
                "GitHubへのPushが完了しました。"
            )
            print(
                "Vercelの自動デプロイ開始を"
                "確認してください。"
            )

    except Exception as error:
        print(f"\n処理に失敗しました：{error}")


if __name__ == "__main__":
    main()