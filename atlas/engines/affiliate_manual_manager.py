"""手動登録するAffiliate案件の追加・削除を一貫して行う。"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
PROGRAM_FILE = BASE_DIR / "data" / "affiliate_programs" / "program_research_results.json"
QUEUE_FILE = BASE_DIR / "data" / "affiliate_programs" / "human_approval_queue.json"
REGISTRY_FILE = BASE_DIR / "data" / "affiliate_links.json"
PROGRAMS_CSV_FILE = BASE_DIR / "data" / "affiliate_programs.csv"
BACKUP_DIR = BASE_DIR / "logs" / "deleted_affiliates"
STATUSES = {"approved_for_application", "applied", "approved", "rejected"}


def sync_csv(service: str, args: argparse.Namespace | None) -> None:
    """旧Affiliate同期との互換性を保つ。"""
    if not PROGRAMS_CSV_FILE.exists():
        return
    with PROGRAMS_CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    rows = [row for row in rows if str(row.get("tool_name", "")).strip() != service]
    if args is not None:
        status = {
            "approved_for_application": "none",
            "applied": "pending",
            "approved": "active",
            "rejected": "rejected",
        }[args.status]
        official_url = args.program_url.strip() or args.affiliate_url.strip()
        if official_url:
            rows.append(
                {
                    "tool_name": service,
                    "network": args.network.strip(),
                    "program_name": args.program_name.strip() or service,
                    "status": status,
                    "official_url": official_url,
                    "affiliate_url": args.affiliate_url.strip(),
                    "reward_type": "none",
                    "reward_value": "0",
                    "currency": "JPY",
                    "conversion_action": "",
                    "cookie_days": "0",
                    "approval_score": "0",
                    "article_match_score": "0",
                    "last_verified": date.today().isoformat(),
                    "notes": args.notes.strip(),
                }
            )
    with PROGRAMS_CSV_FILE.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upsert(items: list[dict[str, Any]], service: str, value: dict[str, Any]) -> None:
    for index, item in enumerate(items):
        if str(item.get("service", "")).strip() == service:
            items[index] = value
            return
    items.append(value)


def add_program(args: argparse.Namespace) -> None:
    service = args.service.strip()
    if not service:
        raise ValueError("サービス名が必要です。")
    if args.status == "approved" and not args.affiliate_url.strip():
        raise ValueError("承認済み案件には広告URLが必要です。")

    program_data = load_json(PROGRAM_FILE, {"programs": []})
    queue_data = load_json(QUEUE_FILE, {"programs": []})
    registry = load_json(REGISTRY_FILE, {})
    programs = program_data.setdefault("programs", [])
    queue = queue_data.setdefault("programs", [])
    if not isinstance(programs, list) or not isinstance(queue, list) or not isinstance(registry, dict):
        raise RuntimeError("Affiliate管理データ形式が不正です。")

    program = {
        "service": service,
        "program_found": True,
        "program_type": "affiliate",
        "program_name": args.program_name.strip() or service,
        "network": args.network.strip(),
        "program_url": args.program_url.strip(),
        "program_id": args.program_id.strip(),
        "commission": args.commission.strip(),
        "promotion_details": args.promotion_details.strip(),
        "cookie_duration": "",
        "target_country": "Japan",
        "application_required": True,
        "research_notes": "手動登録",
        "sources": [],
        "priority": 0,
        "source_articles": [],
        "verified_at": date.today().isoformat(),
    }
    approval = {
        "service": service,
        "priority": 0,
        "program_name": program["program_name"],
        "program_type": "affiliate",
        "network": program["network"],
        "program_url": program["program_url"],
        "program_id": program["program_id"],
        "commission": program["commission"],
        "promotion_details": program["promotion_details"],
        "cookie_duration": "",
        "target_country": "Japan",
        "application_required": True,
        "verified_at": program["verified_at"],
        "source_articles": [],
        "approval_status": args.status,
        "human_notes": args.notes.strip(),
    }
    affiliate_status = {
        "approved_for_application": "none",
        "applied": "pending",
        "approved": "active",
        "rejected": "rejected",
    }[args.status]
    existing = registry.get(service, {}) if isinstance(registry.get(service), dict) else {}
    registry[service] = {
        **existing,
        "official_url": args.program_url.strip(),
        "affiliate_url": args.affiliate_url.strip(),
        "network": args.network.strip(),
        "program_name": program["program_name"],
        "program_id": args.program_id.strip(),
        "promotion_details": args.promotion_details.strip(),
        "affiliate_status": affiliate_status,
        "cta_label": str(existing.get("cta_label", "")).strip() or f"{service}の詳細を確認する",
        "aliases": existing.get("aliases", [service]) or [service],
    }
    upsert(programs, service, program)
    upsert(queue, service, approval)
    save_json(PROGRAM_FILE, program_data)
    save_json(QUEUE_FILE, queue_data)
    save_json(REGISTRY_FILE, registry)
    sync_csv(service, args)
    print(f"案件を保存しました: {service}")


def delete_program(service: str) -> None:
    service = service.strip()
    program_data = load_json(PROGRAM_FILE, {"programs": []})
    queue_data = load_json(QUEUE_FILE, {"programs": []})
    registry = load_json(REGISTRY_FILE, {})
    program_items = program_data.get("programs", [])
    queue_items = queue_data.get("programs", [])
    backup = {
        "deleted_at": datetime.now().isoformat(),
        "service": service,
        "program": next((item for item in program_items if item.get("service") == service), None),
        "approval": next((item for item in queue_items if item.get("service") == service), None),
        "registry": registry.get(service),
    }
    if not any((backup["program"], backup["approval"], backup["registry"])):
        raise ValueError(f"案件が見つかりません: {service}")
    safe_name = re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龠_-]+", "_", service)[:80]
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{safe_name}.json"
    save_json(backup_path, backup)
    program_data["programs"] = [item for item in program_items if item.get("service") != service]
    queue_data["programs"] = [item for item in queue_items if item.get("service") != service]
    registry.pop(service, None)
    save_json(PROGRAM_FILE, program_data)
    save_json(QUEUE_FILE, queue_data)
    save_json(REGISTRY_FILE, registry)
    sync_csv(service, None)
    print(f"案件を削除しました: {service}\nバックアップ: {backup_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Affiliate案件を手動管理します。")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("--service", required=True)
    add.add_argument("--program-name", default="")
    add.add_argument("--network", default="")
    add.add_argument("--program-url", default="")
    add.add_argument("--program-id", default="")
    add.add_argument("--commission", default="")
    add.add_argument("--promotion-details", default="")
    add.add_argument("--status", choices=sorted(STATUSES), default="approved_for_application")
    add.add_argument("--affiliate-url", default="")
    add.add_argument("--notes", default="")
    delete = sub.add_parser("delete")
    delete.add_argument("--service", required=True)
    args = parser.parse_args()
    if args.command == "add":
        add_program(args)
    else:
        delete_program(args.service)


if __name__ == "__main__":
    main()
