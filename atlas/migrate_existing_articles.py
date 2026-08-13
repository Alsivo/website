import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BLOG_DIR = BASE_DIR.parent / "content" / "blog"


def inspect_article(filepath: Path) -> dict:
    """既存記事がPhase A/Bの新仕様へ移行済みか確認する。"""

    text = filepath.read_text(
        encoding="utf-8",
    )

    has_verified = bool(
        re.search(
            r'^verified:\s*["\']?\d{4}-\d{2}-\d{2}',
            text,
            flags=re.MULTILINE,
        )
    )

    has_reference_section = (
        "## 参考情報" in text
    )

    has_source_marker = bool(
        re.search(
            r"\[S\d+\]",
            text,
        )
    )

    has_after_toc_primary = bool(
        re.search(
            r'<AffiliateLink[^>]*'
            r'ctaType="primary"[^>]*'
            r'ctaPlacement="after_toc"',
            text,
        )
    )

    has_footer_primary = bool(
        re.search(
            r'<AffiliateLink[^>]*'
            r'ctaType="primary"[^>]*'
            r'ctaPlacement="(?:after_comparison|before_faq)"',
            text,
        )
    )

    has_faq = (
        "## よくある質問" in text
    )

    issues: list[str] = []

    if not has_verified:
        issues.append("verifiedなし")

    if not has_reference_section:
        issues.append("参考情報なし")

    if has_source_marker:
        issues.append("[Sx]が公開本文に残っている")

    if not has_faq:
        issues.append("FAQなし")

    # CTAは記事によって広告対象がない場合もあるため、
    # CTAがないだけでは移行失敗とは判定しない。
    has_any_affiliate_link = (
        "<AffiliateLink" in text
    )

    if has_any_affiliate_link:
        if not has_after_toc_primary:
            issues.append(
                "目次直後Primary CTAなし"
            )

        if not has_footer_primary:
            issues.append(
                "記事後半Primary CTAなし"
            )

    return {
        "slug": filepath.stem,
        "filepath": filepath,
        "has_verified": has_verified,
        "has_reference_section":
            has_reference_section,
        "has_source_marker":
            has_source_marker,
        "has_after_toc_primary":
            has_after_toc_primary,
        "has_footer_primary":
            has_footer_primary,
        "has_faq": has_faq,
        "issues": issues,
        "migrated": len(issues) == 0,
    }


def main() -> None:
    files = sorted(
        BLOG_DIR.glob("*.mdx")
    )

    if not files:
        raise RuntimeError(
            "content/blogにMDX記事がありません。"
        )

    print(
        "\n===== Phase A/B 既存記事チェック =====\n"
    )

    migrated_count = 0
    pending_count = 0

    for filepath in files:
        result = inspect_article(
            filepath
        )

        if result["migrated"]:
            migrated_count += 1

            print(
                f"[OK]   {result['slug']}"
            )

        else:
            pending_count += 1

            print(
                f"[TODO] {result['slug']}"
            )

            for issue in result["issues"]:
                print(
                    f"       - {issue}"
                )

    print(
        "\n===== 集計 ====="
    )
    print(
        f"記事数：{len(files)}"
    )
    print(
        f"移行済み：{migrated_count}"
    )
    print(
        f"要移行：{pending_count}"
    )


if __name__ == "__main__":
    main()