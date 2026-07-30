from typing import NotRequired, TypedDict


class TrendCandidate(TypedDict):
    """
    Trend Engineやdata-content-engineから出力される
    記事候補の共通データ形式。
    """

    topic: str
    keyword: str
    source: str
    source_url: NotRequired[str]

    trend_score: float
    competition_score: float
    monetization_score: float
    freshness_score: float

    reason: str


class ArticlePlan(TypedDict):
    """
    Planner Agentが作成し、Writer Agentへ渡す記事企画書。
    """

    topic: str
    primary_keyword: str
    secondary_keywords: list[str]

    title_candidate: str
    target_reader: str
    search_intent: str
    reader_problem: str
    article_goal: str

    category: str
    tags: list[str]
    outline: list[str]

    unique_value: str
    monetization_strategy: str
    internal_link_candidates: list[str]
    reference_queries: list[str]


class GeneratedArticle(TypedDict):
    """
    Writer Agentが生成する記事データ。
    """

    title: str
    description: str
    category: str
    tags: list[str]
    content: str


class ReviewIssue(TypedDict):
    """
    Reviewer Agentが検出した問題。
    """

    level: str
    category: str
    message: str
    suggestion: str


class ArticleReview(TypedDict):
    """
    Reviewer Agentによる記事評価結果。
    """

    approved: bool
    score: int
    issues: list[ReviewIssue]
    revised_article: NotRequired[GeneratedArticle]