"""新しく生成した記事のX・Instagram投稿を自動承認する。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
QUEUE_FILE = BASE_DIR / "data" / "social" / "social_approval_queue.json"
AUTO_PLATFORMS = {"x", "instagram"}


def auto_approve(slug: str) -> int:
    data: dict[str, Any] = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    queue = data.get("queue", [])
    if not isinstance(queue, list):
        raise RuntimeError("Social Approval Queue形式が不正です。")

    now = datetime.now().isoformat()
    approved = 0
    for item in queue:
        if not isinstance(item, dict):
            continue
        if (
            item.get("article_slug") == slug
            and item.get("platform") in AUTO_PLATFORMS
            and item.get("status") == "pending"
        ):
            item["status"] = "approved"
            item["approved_at"] = now
            item["rejected_at"] = ""
            item["updated_at"] = now
            item["decision_note"] = "ALSIVO自動公開"
            approved += 1

    data["updated_at"] = now
    data["total"] = len(queue)
    data["pending"] = sum(item.get("status") == "pending" for item in queue if isinstance(item, dict))
    data["approved"] = sum(item.get("status") == "approved" for item in queue if isinstance(item, dict))
    data["rejected"] = sum(item.get("status") == "rejected" for item in queue if isinstance(item, dict))
    QUEUE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return approved


def main() -> None:
    parser = argparse.ArgumentParser(description="記事のSNS投稿を自動承認します。")
    parser.add_argument("slug")
    args = parser.parse_args()
    count = auto_approve(args.slug.strip())
    print(f"X・Instagram投稿を{count}件自動承認しました。")


if __name__ == "__main__":
    main()
