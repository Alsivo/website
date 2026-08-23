"""LINE配信廃止に伴い、LINE候補を各Queueから除去する。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
FILES = (
    BASE_DIR / "data" / "social" / "social_queue.json",
    BASE_DIR / "data" / "social" / "social_approval_queue.json",
    BASE_DIR / "data" / "social" / "social_publish_routes.json",
)


def remove_line_items(path: Path) -> int:
    if not path.exists():
        return 0
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    list_key = "routes" if "routes" in data else "queue"
    items = data.get(list_key, [])
    if not isinstance(items, list):
        return 0
    kept = [item for item in items if not isinstance(item, dict) or item.get("platform") != "line"]
    removed = len(items) - len(kept)
    data[list_key] = kept
    data["updated_at"] = datetime.now().isoformat()
    data["total"] = len(kept)
    for status in ("pending", "approved", "published", "rejected"):
        if status in data:
            data[status] = sum(
                item.get("status") == status
                for item in kept
                if isinstance(item, dict)
            )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return removed


def main() -> None:
    total = sum(remove_line_items(path) for path in FILES)
    print(f"LINE配信候補を{total}件削除しました。")


if __name__ == "__main__":
    main()
