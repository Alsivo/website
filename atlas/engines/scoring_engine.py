from dataclasses import dataclass

from typing import Protocol


class KeywordItemLike(Protocol):
    keyword: str
    target_length: int
    related_keywords: list[str]
    search_intent: str


MONETIZATION_TERMS = {
    "おすすめ",
    "比較",
    "料金",
    "価格",
    "有料",
    "無料",
    "レビュー",
    "使い方",
    "導入",
    "副業",
    "アフィリエイト",
    "ツール",
    "サービス",
    "効率化",
}

OVERLY_BROAD_TERMS = {
    "AI",
    "生成AI",
    "ChatGPT",
    "Python",
    "プログラミング",
}


@dataclass(frozen=True)
class KeywordScore:
    total: int
    intent_score: int
    related_keyword_score: int
    length_score: int
    monetization_score: int
    specificity_score: int
    reasons: list[str]


def score_keyword_item(item: KeywordItemLike) -> KeywordScore:
    """キーワード候補を100点満点で簡易評価する。"""

    reasons: list[str] = []

    # 1. 検索意図：最大25点
    if len(item.search_intent) >= 30:
        intent_score = 25
        reasons.append("検索意図が具体的")
    elif len(item.search_intent) >= 15:
        intent_score = 18
        reasons.append("検索意図がある程度明確")
    elif item.search_intent:
        intent_score = 10
        reasons.append("検索意図が短い")
    else:
        intent_score = 0
        reasons.append("検索意図が未設定")

    # 2. 関連キーワード：最大20点
    related_count = len(item.related_keywords)
    related_keyword_score = min(related_count * 4, 20)

    if related_count >= 3:
        reasons.append(f"関連キーワードが{related_count}件ある")
    else:
        reasons.append("関連キーワードが少ない")

    # 3. 想定記事長：最大15点
    if 2000 <= item.target_length <= 5000:
        length_score = 15
        reasons.append("記事長が実用的")
    elif 1500 <= item.target_length <= 7000:
        length_score = 10
        reasons.append("記事長は許容範囲")
    else:
        length_score = 4
        reasons.append("記事長の設定を再確認したい")

    # 4. 収益性の可能性：最大20点
    searchable_text = " ".join(
        [
            item.keyword,
            item.search_intent,
            *item.related_keywords,
        ]
    )

    matched_monetization_terms = sorted(
        term
        for term in MONETIZATION_TERMS
        if term.lower() in searchable_text.lower()
    )

    monetization_score = min(
        len(matched_monetization_terms) * 5,
        20,
    )

    if matched_monetization_terms:
        reasons.append(
            "収益性候補語あり："
            + ", ".join(matched_monetization_terms)
        )
    else:
        reasons.append("明確な収益性候補語なし")

    # 5. テーマの具体性：最大20点
    normalized_keyword = item.keyword.strip()

    if normalized_keyword in OVERLY_BROAD_TERMS:
        specificity_score = 3
        reasons.append("テーマが広すぎる")
    elif len(normalized_keyword) >= 15:
        specificity_score = 20
        reasons.append("ロングテールで具体的")
    elif len(normalized_keyword) >= 8:
        specificity_score = 15
        reasons.append("テーマに一定の具体性がある")
    else:
        specificity_score = 8
        reasons.append("テーマがやや広い")

    total = (
        intent_score
        + related_keyword_score
        + length_score
        + monetization_score
        + specificity_score
    )

    return KeywordScore(
        total=total,
        intent_score=intent_score,
        related_keyword_score=related_keyword_score,
        length_score=length_score,
        monetization_score=monetization_score,
        specificity_score=specificity_score,
        reasons=reasons,
    )