import argparse
import json
import re
from pathlib import Path
from typing import Any

from agents.image_creator import (
    generate_article_image,
)
from agents.publisher import publish_article
from agents.researcher import research_topic
from agents.reviewer import review_article
from agents.writer import revise_article
from engines.affiliate_registry import (
    get_affiliate_tool_names,
)


ATLAS_DIR = Path(__file__).resolve().parent.parent
GITHUB_ROOT = ATLAS_DIR.parent.parent

DATA_CONTENT_ENGINE_DIR = (
    GITHUB_ROOT
    / "data-content-engine"
)

PREVIEW_DIR = (
    ATLAS_DIR
    / "data"
    / "content_bridge"
)

MAX_BRIDGE_REVISIONS = 2
MIN_BRIDGE_REVIEW_SCORE = 80


def read_markdown(
    source_path: Path,
) -> str:
    """Data Content Engineの記事Markdownを読む。"""

    if not source_path.exists():
        raise FileNotFoundError(
            "記事ファイルが見つかりません："
            f"{source_path}"
        )

    text = source_path.read_text(
        encoding="utf-8",
    ).strip()

    if not text:
        raise ValueError(
            "記事ファイルが空です。"
        )

    return text


def extract_title(
    markdown: str,
) -> str:
    """先頭のH1からタイトルを取得する。"""

    match = re.search(
        r"^#\s+(.+?)\s*$",
        markdown,
        flags=re.MULTILINE,
    )

    if not match:
        raise ValueError(
            "記事本文からH1タイトルを"
            "取得できませんでした。"
        )

    return match.group(1).strip()


def remove_h1(
    markdown: str,
) -> str:
    """Atlas本文用にH1を削除する。"""

    return re.sub(
        r"^#\s+.+?\s*\n+",
        "",
        markdown,
        count=1,
        flags=re.MULTILINE,
    ).strip()


def extract_description(
    markdown_without_h1: str,
) -> str:
    """導入文から仮descriptionを作る。"""

    paragraphs = re.split(
        r"\n\s*\n",
        markdown_without_h1,
    )

    for paragraph in paragraphs:
        cleaned = paragraph.strip()

        if not cleaned:
            continue

        if cleaned.startswith("#"):
            continue

        if cleaned.startswith("- "):
            continue

        one_line = re.sub(
            r"\s+",
            " ",
            cleaned,
        ).strip()

        if not one_line:
            continue

        if len(one_line) <= 120:
            return one_line

        return one_line[:117].rstrip() + "..."

    raise ValueError(
        "description候補となる導入文を"
        "取得できませんでした。"
    )


def extract_faq(
    markdown: str,
) -> tuple[list[dict[str, str]], str]:
    """
    FAQをarticle.faqへ分離し、
    本文からFAQセクションを削除する。
    """

    section_match = re.search(
        (
            r"(?ms)^##\s+"
            r"(?:よくある質問|FAQ)"
            r".*?\n"
            r"(.*?)(?=^##\s+|\Z)"
        ),
        markdown,
    )

    if not section_match:
        raise ValueError(
            "FAQセクションが見つかりません。"
        )

    faq_body = section_match.group(1)

    qa_pattern = re.compile(
        (
            r"(?ms)^Q\d*[:：]\s*(.+?)\n"
            r"A\d*[:：]\s*(.+?)"
            r"(?=^Q\d*[:：]|\Z)"
        )
    )

    faq_items: list[
        dict[str, str]
    ] = []

    for match in qa_pattern.finditer(
        faq_body
    ):
        question = re.sub(
            r"\s+",
            " ",
            match.group(1),
        ).strip()

        answer = re.sub(
            r"\s+",
            " ",
            match.group(2),
        ).strip()

        if (
            question
            and answer
        ):
            faq_items.append(
                {
                    "question": question,
                    "answer": answer,
                }
            )

    if len(faq_items) < 3:
        raise ValueError(
            "FAQを3件以上取得できませんでした。"
        )

    # AtlasはFAQ最大5件
    faq_items = faq_items[:5]

    content_without_faq = (
        markdown[
            :section_match.start()
        ]
        + markdown[
            section_match.end():
        ]
    )

    content_without_faq = (
        content_without_faq.strip()
    )

    return (
        faq_items,
        content_without_faq,
    )


def build_initial_article(
    keyword: str,
    service: str,
    markdown: str,
) -> dict[str, Any]:
    """
    Data Content Engine記事を
    Atlas Reviewerへ渡すための
    仮article形式へ変換する。
    """

    registered_tools = (
        get_affiliate_tool_names()
    )

    if service not in registered_tools:
        raise ValueError(
            f"{service} がAffiliate Registryに"
            "登録されていません。"
        )

    title = extract_title(
        markdown
    )

    content = remove_h1(
        markdown
    )

    description = extract_description(
        content
    )

    faq, content = extract_faq(
        content
    )

    article = {
        "title": title,
        "description": description,

        # revise_article()で
        # 正式な英語slugへ修正させる
        "slug": (
            "temporary-import-article"
        ),

        # revise_article()で
        # Atlasの正式カテゴリーへ修正
        "category": "AIツール",

        # revise_article()で
        # 正式タグへ修正
        "tags": [
            "生成AI",
            "AIツール",
        ],

        # 初期記事にはまだ
        # Atlas形式の[S1]出典がない
        "used_source_ids": [],

        "content": content,

        "recommended_tools": [
            service,
        ],

        "comparison_table": None,

        "cta_plan": {
            "primary_service": service,
            "placement": "before_faq",
            "cta_label": (
                f"{service}の"
                "公式サイトを確認する"
            ),
            "reason": (
                "記事テーマの対象サービスについて、"
                "最新の公式情報を確認するため"
            ),
        },

        "faq": faq,
    }

    return article


def build_review_plan(
    keyword: str,
    title: str,
) -> dict[str, Any]:
    """Reviewerへ渡す簡易記事企画を作る。"""

    return {
        "suggested_title": title,
        "search_intent": (
            f"{keyword}を検索する読者が、"
            "サービスの実態、評判、料金、"
            "メリット・デメリットを確認し、"
            "利用すべきか判断できるようにする"
        ),
        "target_keyword": keyword,
    }


def print_review(
    review: dict[str, Any],
) -> None:
    """Reviewer結果を表示する。"""

    print(
        "\n===== Bridge Review =====\n"
    )

    print(
        "公開判定："
        + (
            "承認"
            if review.get("approved")
            else "要修正"
        )
    )

    print(
        "品質スコア："
        f"{review.get('score', 0)} / 100"
    )

    print(
        "講評："
        f"{review.get('summary', '')}"
    )

    issues = review.get(
        "issues",
        [],
    )

    if issues:
        print(
            "\n問題点:"
        )

        for issue in issues:
            print(
                f"- {issue}"
            )

    instructions = review.get(
        "improvement_instructions",
        [],
    )

    if instructions:
        print(
            "\n修正指示:"
        )

        for instruction in instructions:
            print(
                f"- {instruction}"
            )


def save_preview(
    payload: dict[str, Any],
) -> Path:
    """Bridge結果をJSON保存する。"""

    PREVIEW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    keyword = str(
        payload.get(
            "keyword",
            "untitled",
        )
    ).strip()

    safe_keyword = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        keyword,
    )

    safe_keyword = re.sub(
        r"\s+",
        "_",
        safe_keyword,
    ).strip("._")

    if not safe_keyword:
        safe_keyword = "untitled"

    output_path = (
        PREVIEW_DIR
        / f"{safe_keyword}.json"
    )

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return output_path


def publish_approved_preview(
    preview_path: Path,
) -> Path:
    """
    APPROVED済みPreviewを読み込み、
    Research/Reviewを再実行せず公開する。
    """

    if not preview_path.exists():
        raise FileNotFoundError(
            "Previewファイルが見つかりません："
            f"{preview_path}"
        )

    payload = json.loads(
        preview_path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "Preview JSONの形式が不正です。"
        )

    if payload.get("published"):
        raise ValueError(
            "このPreviewはすでに公開済みです。"
        )

    approved = bool(
        payload.get(
            "approved",
            False,
        )
    )

    review = payload.get(
        "review",
        {},
    )

    review_score = int(
        review.get(
            "score",
            0,
        )
    )

    if (
        not approved
        or review_score
        < MIN_BRIDGE_REVIEW_SCORE
    ):
        raise ValueError(
            "Reviewerの公開基準を"
            "満たしていないPreviewです。"
            f" approved={approved},"
            f" score={review_score}"
        )

    article = payload.get(
        "article"
    )

    research = payload.get(
        "research"
    )

    if not isinstance(
        article,
        dict,
    ):
        raise ValueError(
            "Previewにarticleがありません。"
        )

    if not isinstance(
        research,
        dict,
    ):
        raise ValueError(
            "Previewにresearchがありません。"
        )

    print(
        "\n===== Approved Preview Publish =====\n"
    )

    print(
        "keyword: "
        f"{payload.get('keyword', '')}"
    )

    print(
        "service: "
        f"{payload.get('service', '')}"
    )

    print(
        "review score: "
        f"{review_score}"
    )

    print(
        "\n[Publish 1/2] "
        "アイキャッチ画像を生成しています..."
    )

    image_url, image_file_path = (
        generate_article_image(
            article
        )
    )

    article["image"] = image_url

    print(
        f"画像URL：{image_url}"
    )

    print(
        "\n[Publish 2/2] "
        "CTA付きMDXを保存しています..."
    )

    filepath = publish_article(
        article,
        research,
    )

    payload["article"] = article
    payload["published"] = True
    payload["published_path"] = str(
        filepath
    )
    payload["image_url"] = image_url
    payload["image_file_path"] = (
        str(image_file_path)
        if image_file_path is not None
        else ""
    )

    preview_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\n===== Publish Result =====\n"
    )

    print(
        f"記事保存先：{filepath}"
    )

    print(
        f"Preview更新先：{preview_path}"
    )

    print(
        "\nローカルMDXへの反映が完了しました。"
    )

    print(
        "Gitへのcommit/pushは"
        "まだ行っていません。"
    )

    return filepath


def run_bridge(
    source_path: Path,
    keyword: str,
    service: str,
) -> dict[str, Any]:
    """Import→Research→Review→Revisionを実行する。"""

    print(
        "\n===== Data Content Article Bridge =====\n"
    )

    print(
        f"source: {source_path}"
    )

    print(
        f"keyword: {keyword}"
    )

    print(
        f"service: {service}"
    )

    print(
        "\n[1/4] Data Content Engine記事を"
        "読み込んでいます..."
    )

    markdown = read_markdown(
        source_path
    )

    article = build_initial_article(
        keyword=keyword,
        service=service,
        markdown=markdown,
    )

    plan = build_review_plan(
        keyword=keyword,
        title=article["title"],
    )

    print(
        "\n[2/4] Atlas Researcherで"
        "最新情報を調査しています..."
    )

    research = research_topic(
        keyword
    )

    sources = research.get(
        "sources",
        [],
    )

    print(
        "\n取得出典数："
        f"{len(sources)}"
    )

    if not sources:
        raise RuntimeError(
            "Web調査で出典を取得できなかったため、"
            "Bridge処理を停止します。"
        )

    print(
        "\n[3/4] Atlas Reviewerで"
        "事実・記事品質を確認しています..."
    )

    review = review_article(
        plan,
        article,
        research,
    )

    print_review(
        review
    )

    revision_count = 0

    while (
        (
            not review.get(
                "approved",
                False,
            )
            or int(
                review.get(
                    "score",
                    0,
                )
            )
            < MIN_BRIDGE_REVIEW_SCORE
        )
        and revision_count
        < MAX_BRIDGE_REVISIONS
    ):
        revision_count += 1

        print(
            "\n[4/4] Reviewer指摘と"
            "Web調査結果を使って修正します "
            f"({revision_count}/"
            f"{MAX_BRIDGE_REVISIONS})..."
        )

        article = revise_article(
            plan=plan,
            research=research,
            article=article,
            review=review,
        )

        review = review_article(
            plan,
            article,
            research,
        )

        print_review(
            review
        )

    final_approved = (
        bool(
            review.get(
                "approved",
                False,
            )
        )
        and int(
            review.get(
                "score",
                0,
            )
        )
        >= MIN_BRIDGE_REVIEW_SCORE
    )

    payload = {
        "source_path": str(
            source_path
        ),
        "keyword": keyword,
        "service": service,
        "approved": (
            final_approved
        ),
        "revision_count": (
            revision_count
        ),
        "plan": plan,
        "research": research,
        "review": review,
        "article": article,
    }

    preview_path = save_preview(
        payload
    )

    print(
        "\n===== Bridge Result =====\n"
    )

    print(
        "final status: "
        + (
            "APPROVED"
            if final_approved
            else "REVIEW_REQUIRED"
        )
    )

    print(
        "review score: "
        f"{review.get('score', 0)}"
    )

    print(
        "revisions: "
        f"{revision_count}"
    )

    print(
        "\nPreview保存先："
    )

    print(
        preview_path
    )

    print(
        "\nDRY RUNです。"
        "websiteの記事ファイルは"
        "変更していません。"
    )

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Data Content Engineの記事を"
            "AtlasのResearch/Reviewフローへ"
            "接続します。"
        )
    )

    parser.add_argument(
        "--source",
        required=False,
        help=(
            "Data Content Engineの"
            "生成済みMarkdownパス"
        ),
    )

    parser.add_argument(
        "--keyword",
        required=False,
        help="対象キーワード",
    )

    parser.add_argument(
        "--service",
        required=False,
        help=(
            "Affiliate Registry上の"
            "正式サービス名"
        ),
    )

    parser.add_argument(
        "--apply-preview",
        default="",
        help=(
            "APPROVED済みPreview JSONを"
            "Research/Reviewを再実行せず"
            "公開します。"
        ),
    )
    args = parser.parse_args()

    if args.apply_preview:
        preview_path = Path(
            args.apply_preview
        ).expanduser().resolve()

        publish_approved_preview(
            preview_path
        )

        return

    missing_arguments = []

    if not args.source:
        missing_arguments.append(
            "--source"
        )

    if not args.keyword:
        missing_arguments.append(
            "--keyword"
        )

    if not args.service:
        missing_arguments.append(
            "--service"
        )

    if missing_arguments:
        raise ValueError(
            "通常Bridge実行には次の引数が"
            "必要です："
            + ", ".join(
                missing_arguments
            )
        )

    source_path = Path(
        args.source
    ).expanduser().resolve()

    run_bridge(
        source_path=source_path,
        keyword=args.keyword.strip(),
        service=args.service.strip(),
    )


if __name__ == "__main__":
    main()