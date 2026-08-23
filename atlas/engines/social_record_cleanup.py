"""記事単位でSNS配信記録を安全に削除する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
FILES = (
    (BASE_DIR / "data" / "social" / "social_queue.json", "queue"),
    (BASE_DIR / "data" / "social" / "social_approval_queue.json", "queue"),
    (BASE_DIR / "data" / "social" / "social_publish_routes.json", "routes"),
)


def save(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def remove_article_records(article_slug: str) -> int:
    """指定slugに完全一致する記録だけを削除する。"""
    if not article_slug or any(char in article_slug for char in ("/", "\\", "..")):
        raise ValueError("安全な記事IDを指定してください。")
    removed = 0
    for path, key in FILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get(key, [])
        if not isinstance(items, list):
            raise ValueError(f"{path.name}の形式が不正です。")
        kept = [
            item for item in items
            if not isinstance(item, dict)
            or str(item.get("article_slug", "")).strip() != article_slug
        ]
        removed += len(items) - len(kept)
        data[key] = kept
        data["total"] = len(kept)
        if key == "routes":
            data["ready"] = sum(1 for item in kept if item.get("route_status") == "ready")
            data["blocked"] = sum(1 for item in kept if item.get("route_status") == "blocked")
        else:
            for status in ("pending", "approved", "published", "rejected"):
                if status in data:
                    data[status] = sum(1 for item in kept if item.get("status") == status)
        save(path, data)
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("article_slug")
    args = parser.parse_args()
    count = remove_article_records(args.article_slug)
    print(f"{args.article_slug}のSNS記録を{count}件削除しました。")


if __name__ == "__main__":
    main()
