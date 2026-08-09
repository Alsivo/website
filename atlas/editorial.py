import json
from pathlib import Path

from agents.editor import (
    make_editorial_decision,
)
from engines.editorial_context import (
    build_editorial_context,
)
from engines.rewrite_history import (
    is_rewrite_allowed,
)


BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "editorial"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "latest_decision.json"
)


def main() -> None:
    try:
        print(
            "\n[Editorial] "
            "サイト状況を収集中...\n"
        )

        context = build_editorial_context()

        decision = (
            make_editorial_decision(
                context
            )
        )

        if (
            decision.get(
                "action"
            )
            == "rewrite_article"
        ):
            target_slug = str(
                decision.get(
                    "target_slug",
                    "",
                )
            ).strip()

            if target_slug:
                (
                    rewrite_allowed,
                    rewrite_cooldown_reason,
                ) = is_rewrite_allowed(
                    target_slug
                )

                decision[
                    "rewrite_allowed"
                ] = rewrite_allowed

                decision[
                    "rewrite_cooldown_reason"
                ] = (
                    rewrite_cooldown_reason
                )

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        OUTPUT_FILE.write_text(
            json.dumps(
                decision,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(
            "\n===== AI編集長の判断 =====\n"
        )

        print(
            f"施策：{decision['action']}"
        )

        print(
            "優先度："
            f"{decision['priority_score']}"
            " / 100"
        )

        print(
            f"理由：{decision['reason']}"
        )

        if decision["target_keyword"]:
            print(
                "対象キーワード："
                f"{decision['target_keyword']}"
            )

        if decision["target_title"]:
            print(
                "対象記事："
                f"{decision['target_title']}"
            )

        if decision["target_slug"]:
            print(
                "対象slug："
                f"{decision['target_slug']}"
            )

        if (
            decision.get(
                "action"
            )
            == "rewrite_article"
        ):
            rewrite_allowed = (
                decision.get(
                    "rewrite_allowed"
                )
            )

            rewrite_reason = str(
                decision.get(
                    "rewrite_cooldown_reason",
                    "",
                )
            )

            print(
                "リライト可否："
                f"{rewrite_allowed}"
            )

            if rewrite_reason:
                print(
                    "クールダウン判定："
                    f"{rewrite_reason}"
                )

        if decision[
            "recommended_focus"
        ]:
            print(
                "\n改善・執筆ポイント"
            )

            for item in decision[
                "recommended_focus"
            ]:
                print(
                    f"- {item}"
                )

        if decision["target_queries"]:
            print(
                "\n強化検索語"
            )

            for query in decision[
                "target_queries"
            ]:
                print(
                    f"- {query}"
                )

        print(
            "\n収益化観点："
            f"{decision['monetization_opportunity']}"
        )

        print(
            "期待効果："
            f"{decision['expected_effect']}"
        )

        print(
            "\n判断保存先："
            f"{OUTPUT_FILE}"
        )

    except Exception as error:
        print(
            "\nAI編集長の処理に"
            f"失敗しました：{error}"
        )


if __name__ == "__main__":
    main()