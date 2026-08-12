import json
import shutil
from datetime import datetime
from pathlib import Path
import sys

from agents.publisher import (
    publish_article,
)
from agents.researcher import (
    research_topic,
)
from agents.reviewer import (
    review_article,
)
from agents.rewriter import (
    rewrite_article,
)
from config import (
    MAX_REWRITE_ATTEMPTS,
    REWRITE_BACKUP_DIR_NAME,
    REWRITE_MIN_REVIEW_SCORE,
)
from engines.article_loader import (
    load_article_by_slug,
)
from engines.editorial_context import (
    get_queries_for_slug,
)
from engines.rewrite_history import (
    record_rewrite,
)


BASE_DIR = Path(__file__).resolve().parent

DECISION_FILE = (
    BASE_DIR
    / "data"
    / "editorial"
    / "latest_decision.json"
)

BACKUP_DIR = (
    BASE_DIR
    / "data"
    / REWRITE_BACKUP_DIR_NAME
)


def load_editorial_decision() -> dict:
    """最新のAI編集長判断を読む。"""

    if not DECISION_FILE.exists():
        raise FileNotFoundError(
            "latest_decision.jsonがありません。"
            "先にpython editorial.pyを"
            "実行してください。"
        )

    return json.loads(
        DECISION_FILE.read_text(
            encoding="utf-8",
        )
    )


def backup_article(
    article: dict,
) -> Path:
    """リライト前のMDXをバックアップする。"""

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        BACKUP_DIR
        / (
            f"{article['slug']}"
            f"_{timestamp}.mdx"
        )
    )

    shutil.copy2(
        article["filepath"],
        backup_path,
    )

    return backup_path


def build_rewrite_topic(
    article: dict,
    decision: dict,
    query_rows: list[dict],
) -> str:
    """Researcherへ渡すリライト調査テーマを作る。"""

    query_text = ", ".join(
        str(
            row.get(
                "query",
                "",
            )
        )
        for row in query_rows
        if row.get(
            "query"
        )
    )

    return (
        f"既存記事タイトル：{article['title']}\n"
        f"主な強化キーワード："
        f"{decision.get('target_keyword', '')}\n"
        f"Search Console検索語："
        f"{query_text}\n"
        "既存記事を最新情報へ更新するため、"
        "料金・機能・仕様・提供条件・"
        "重要な変更点を一次情報中心に調査する"
    )


def main() -> None:
    try:
        args = sys.argv[1:]

        dry_run = (
            "--dry-run"
            in args
        )

        positional_args = [
            arg
            for arg in args
            if not arg.startswith("--")
        ]

        manual_slug = (
            positional_args[0].strip()
            if positional_args
            else ""
        )

        if manual_slug:
            decision = {
                "action":
                    "rewrite_article",
                "priority_score":
                    100,
                "reason":
                    "手動リライトテスト",
                "target_keyword":
                    "",
                "target_slug":
                    manual_slug,
                "target_title":
                    "",
                "search_intent":
                    "",
                "recommended_focus": [],
                "target_queries": [],
                "monetization_opportunity":
                    "",
                "expected_effect":
                    "",
            }
        else:
            decision = (
                load_editorial_decision()
            )

        if (
            decision.get("action")
            != "rewrite_article"
        ):
            print(
                "最新の編集判断は"
                "rewrite_articleではありません。"
            )
            return

        slug = str(
            decision.get(
                "target_slug",
                "",
            )
        ).strip()

        if not slug:
            raise ValueError(
                "target_slugがありません。"
            )

        print(
            f"\n[Rewrite] 対象記事：{slug}"
        )

        article = (
            load_article_by_slug(
                slug
            )
        )

        query_rows = (
            get_queries_for_slug(
                slug
            )
        )

        print(
            "[Rewrite] "
            "最新情報を再調査中..."
        )

        topic = build_rewrite_topic(
            article,
            decision,
            query_rows,
        )

        research = research_topic(
            topic
        )

        rewritten = rewrite_article(
            existing_article=article,
            editorial_decision=decision,
            search_queries=query_rows,
            research=research,
        )

        review = None

        for attempt in range(
            MAX_REWRITE_ATTEMPTS + 1
        ):
            print(
                "\n[Reviewer] "
                "リライト記事を確認中 "
                f"({attempt + 1}/"
                f"{MAX_REWRITE_ATTEMPTS + 1})..."
            )

            review_plan = {
                "suggested_title":
                    rewritten["title"],
                "search_intent":
                    decision.get(
                        "search_intent",
                        "",
                    ),
                "target_keyword":
                    decision.get(
                        "target_keyword",
                        "",
                    ),
            }

            review = review_article(
                review_plan,
                rewritten,
                research,
            )

            approved = (
                review["approved"]
                and review["score"]
                >= REWRITE_MIN_REVIEW_SCORE
            )

            print(
                "品質スコア："
                f"{review['score']} / 100"
            )

            if approved:
                break

            if (
                attempt
                >= MAX_REWRITE_ATTEMPTS
            ):
                break

            print(
                "[Rewrite] "
                "Reviewer指摘を反映して"
                "再リライトします..."
            )

            correction_decision = {
                **decision,
                "recommended_focus": (
                    review.get(
                        "improvement_instructions",
                        [],
                    )
                ),
            }

            rewritten = rewrite_article(
                existing_article=article,
                editorial_decision=
                    correction_decision,
                search_queries=
                    query_rows,
                research=research,
            )

        if review is None:
            raise RuntimeError(
                "Reviewer結果がありません。"
            )

        approved = (
            review["approved"]
            and review["score"]
            >= REWRITE_MIN_REVIEW_SCORE
        )

        if not approved:
            print(
                "\nリライト品質が基準未満のため、"
                "元記事は変更しません。"
            )
            sys.exit(1)

        if dry_run:
            print(
                "\n===== リライト DRY RUN 完了 ====="
            )

            print(
                f"記事：{slug}"
            )

            print(
                "品質スコア："
                f"{review['score']} / 100"
            )

            print(
                "改善内容："
                f"{rewritten['rewrite_summary']}"
            )

            print(
                "DRY RUNのため、"
                "元記事・リライト履歴は"
                "変更していません。"
            )

            return

        backup_path = backup_article(
            article
        )

        print(
            "\n[Rewrite] "
            "元記事をバックアップしました："
        )
        print(
            backup_path
        )

        rewritten["image"] = article[
            "image"
        ]

        # --------------------------------------------------------
        # リライト時のCTA Planを保証する
        # --------------------------------------------------------

        rewritten_cta_plan = rewritten.get(
            "cta_plan"
        )

        if not isinstance(
            rewritten_cta_plan,
            dict,
        ):
            existing_cta_plan = article.get(
                "cta_plan"
            )

            if isinstance(
                existing_cta_plan,
                dict,
            ):
                rewritten["cta_plan"] = (
                    existing_cta_plan
                )

            else:
                recommended_tools = (
                    rewritten.get(
                        "recommended_tools",
                        [],
                    )
                )

                primary_service = ""

                if (
                    isinstance(
                        recommended_tools,
                        list,
                    )
                    and recommended_tools
                ):
                    first_tool = (
                        recommended_tools[0]
                    )

                    if isinstance(
                        first_tool,
                        str,
                    ):
                        primary_service = (
                            first_tool.strip()
                        )

                comparison_table = (
                    rewritten.get(
                        "comparison_table"
                    )
                )

                has_comparison_table = (
                    isinstance(
                        comparison_table,
                        dict,
                    )
                    and bool(
                        comparison_table
                    )
                )

                placement = (
                    "after_comparison"
                    if has_comparison_table
                    else "before_faq"
                )

                rewritten["cta_plan"] = {
                    "primary_service":
                        primary_service,
                    "placement":
                        placement,
                    "cta_label":
                        (
                            f"{primary_service}の"
                            "公式サイトを確認する"
                            if primary_service
                            else ""
                        ),
                    "reason":
                        (
                            "リライト記事の"
                            "フォールバックCTA設定"
                        ),
                }

        filepath = publish_article(
            rewritten,
            research,
            original_date=article[
                "date"
            ],
            is_rewrite=True,
        )

        history_path = record_rewrite(
            slug=slug,
            title=str(
                rewritten.get(
                    "title",
                    article.get(
                        "title",
                        "",
                    ),
                )
            ).strip(),
            reason=str(
                decision.get(
                    "reason",
                    "",
                )
            ).strip(),
        )

        print(
            "\n===== リライト完了 ====="
        )

        print(
            f"記事：{filepath}"
        )

        print(
            f"リライト履歴：{history_path}"
        )

        print(
            "改善内容："
            f"{rewritten['rewrite_summary']}"
        )

    except Exception as error:
        print(
            "\nリライト処理に"
            f"失敗しました：{error}"
        )

        sys.exit(1)


if __name__ == "__main__":
    main()