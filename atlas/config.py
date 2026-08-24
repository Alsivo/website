import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL = "gpt-5"

# Web検索は長時間化しやすいため、調査専用の軽量モデルを使う。
# 記事本文・レビューには従来どおりMODELを使用する。
RESEARCH_MODEL = "gpt-5-mini"

# ============================================================
# Site settings
# ============================================================

SITE_NAME = "Alsivo"
AUTHOR_NAME = "Alsivo"


# ============================================================
# Article settings
# ============================================================

MIN_ARTICLE_LENGTH = 2000


# ============================================================
# Category settings
# ============================================================

CATEGORIES = [
    "AI基礎",
    "AIツール",
    "仕事効率化",
    "AI副業",
    "プログラミング",
]

# ============================================================
# Tag settings
# ============================================================

CORE_TAGS = [
    "生成AI",
    "AI基礎",
    "AIツール",
    "ChatGPT",
    "Claude",
    "Gemini",
    "OpenAI",
    "Python",
    "プログラミング",
    "仕事効率化",
    "業務効率化",
    "自動化",
    "AI副業",
    "アフィリエイト",
    "SEO",
]

MIN_TAGS = 3
MAX_TAGS = 5
MAX_NEW_TAGS = 2

# ============================================================
# Web research settings
# ============================================================

WEB_SEARCH_CONTEXT_SIZE = "low"
# 5回ではWeb調査が長時間化し、Responses APIが180秒で
# タイムアウトする事例がある。一次情報の確認に必要な範囲で3回に抑える。
MAX_WEB_SEARCH_CALLS = 2

# ============================================================
# Review settings
# ============================================================

MAX_REVISION_ATTEMPTS = 2
MIN_REVIEW_SCORE = 80

# ============================================================
# Image generation settings
# ============================================================

IMAGE_MODEL = "gpt-image-1.5"
IMAGE_SIZE = "1536x1024"
IMAGE_QUALITY = "medium"
IMAGE_OUTPUT_FORMAT = "webp"

# ============================================================
# Git publishing settings
# ============================================================

AUTO_GIT_PUSH = True
GIT_REMOTE = "origin"

# ============================================================
# Google Search Console
# ============================================================

SEARCH_CONSOLE_SITE_URL = (
    "sc-domain:alsivo.com"
)

SEARCH_CONSOLE_LOOKBACK_DAYS = 28

SEARCH_CONSOLE_ROW_LIMIT = 25000

# ============================================================
# AI Editorial Director
# ============================================================

EDITORIAL_MIN_IMPRESSIONS = 20

EDITORIAL_REWRITE_POSITION_MIN = 4.0
EDITORIAL_REWRITE_POSITION_MAX = 20.0

EDITORIAL_LOW_CTR_THRESHOLD = 0.02

EDITORIAL_MAX_EXISTING_ARTICLES = 30

EDITORIAL_MAX_KEYWORDS = 30

# ============================================================
# Auto Rewrite
# ============================================================

MAX_REWRITE_ATTEMPTS = 2

REWRITE_BACKUP_DIR_NAME = (
    "rewrite_backups"
)

REWRITE_MIN_REVIEW_SCORE = 85

# ============================================================
# Atlas Automation
# ============================================================

ATLAS_AUTO_MODE = True

ATLAS_RUN_SEARCH_CONSOLE = True

ATLAS_RUN_AFFILIATE_MANAGER = True

ATLAS_USE_CACHED_SEARCH_CONSOLE_ON_ERROR = True

ATLAS_LOCK_TIMEOUT_HOURS = 6

ATLAS_LOG_RETENTION_DAYS = 30

# Atlas自動運転：GA4 Affiliate Click
ATLAS_RUN_GA4_AFFILIATE = True

# GA4取得失敗時、前回取得データで続行する
ATLAS_USE_CACHED_GA4_ON_ERROR = True

# Atlas自動運転：Revenue Summary
ATLAS_RUN_REVENUE_TRACKER = True

# Revenue集計失敗時、前回集計結果で続行する
ATLAS_USE_CACHED_REVENUE_ON_ERROR = True
