"""A8.netの広告掲載URL一括提出用CSVを生成する。"""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ATLAS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ATLAS_DIR.parent
BLOG_DIR = PROJECT_ROOT / "content" / "blog"
REGISTRY_FILE = ATLAS_DIR / "data" / "affiliate_links.json"
EXPORT_DIR = ATLAS_DIR / "exports"
SITE_URL = "https://www.alsivo.com"


def load_registry() -> dict[str, dict[str, Any]]:
    if not REGISTRY_FILE.exists():
        return {}
    data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("affiliate_links.jsonの形式が不正です。")
    return {
        str(service): item
        for service, item in data.items()
        if isinstance(item, dict)
    }


def is_published(mdx: str) -> bool:
    match = re.search(r"^published:\s*(.+?)\s*$", mdx, re.MULTILINE)
    return match is None or match.group(1).strip().lower() != "false"


def affiliate_services(mdx: str) -> set[str]:
    services: set[str] = set()
    for tag in re.findall(r"<AffiliateLink\b[\s\S]*?>", mdx):
        link_type = re.search(r'\blinkType=["\']([^"\']+)["\']', tag)
        service = re.search(r'\bservice=["\']([^"\']+)["\']', tag)
        if link_type and link_type.group(1) == "affiliate" and service:
            services.add(service.group(1).strip())
    return services


def collect_a8_submission_rows() -> list[tuple[str, str]]:
    registry = load_registry()
    rows: set[tuple[str, str]] = set()
    for filepath in BLOG_DIR.glob("*.mdx"):
        mdx = filepath.read_text(encoding="utf-8")
        if not is_published(mdx):
            continue
        article_url = f"{SITE_URL}/blog/{filepath.stem}"
        for service in affiliate_services(mdx):
            item = registry.get(service, {})
            network = str(item.get("network", "")).strip().lower()
            program_id = str(item.get("program_id", "")).strip()
            if network == "a8.net":
                if not program_id:
                    raise ValueError(
                        f"{service}はA8.net案件ですが、プログラムIDが未登録です。"
                    )
                rows.add((program_id, article_url))
    return sorted(rows)


def export_a8_submission_csv() -> Path:
    """既存・新規の公開記事をまとめた当日分CSVを保存する。"""
    rows = collect_a8_submission_rows()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    output = EXPORT_DIR / f"A8.net_{date.today():%Y%m%d}.csv"
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows(rows)
    return output


def main() -> None:
    output = export_a8_submission_csv()
    count = len(collect_a8_submission_rows())
    print(f"A8.net提出用CSVを作成しました: {output}\n対象URL: {count}件")


if __name__ == "__main__":
    main()
