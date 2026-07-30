from pathlib import Path


ATLAS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ATLAS_DIR.parent

DATA_DIR = ATLAS_DIR / "data"
INVENTORY_DIR = DATA_DIR / "inventory"
PLANS_DIR = DATA_DIR / "plans"
ARTICLES_DIR = DATA_DIR / "articles"

DOCS_DIR = ATLAS_DIR / "docs"

BLOG_CONTENT_DIR = PROJECT_ROOT / "content" / "blog"


def create_required_directories() -> None:
    """
    Atlasが利用するフォルダを作成する。

    exist_ok=Trueのため、既にフォルダが存在していても
    エラーにはならない。
    """

    directories = [
        DATA_DIR,
        INVENTORY_DIR,
        PLANS_DIR,
        ARTICLES_DIR,
        DOCS_DIR,
        BLOG_CONTENT_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)