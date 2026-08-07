import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL = "gpt-5"

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

WEB_SEARCH_CONTEXT_SIZE = "medium"
MAX_WEB_SEARCH_CALLS = 5

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