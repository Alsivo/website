"""アフィリエイト記事とSNSの広告表示を判定する。"""

from __future__ import annotations

import re
from pathlib import Path


AFFILIATE_LINK_PATTERN = re.compile(
    r"<AffiliateLink\b(?=[^>]*\blinkType=[\"']affiliate[\"'])",
    re.IGNORECASE,
)


def content_has_affiliate_link(content: str) -> bool:
    """本文に実際のアフィリエイトリンクがある場合だけTrueを返す。"""

    return bool(AFFILIATE_LINK_PATTERN.search(content))


def article_has_affiliate_link(path: Path) -> bool:
    """MDX記事がアフィリエイト記事か判定する。"""

    try:
        return content_has_affiliate_link(path.read_text(encoding="utf-8"))
    except OSError:
        return False


def ensure_pr_prefix(text: str) -> str:
    """広告投稿の先頭へ、見落としにくいPR表示を付ける。"""

    cleaned = text.strip()
    if re.match(r"^(?:#PR|【PR】|PR\b)", cleaned, re.IGNORECASE):
        return cleaned
    return f"#PR\n{cleaned}"
