"""手動登録するAffiliate案件の追加・削除を一貫して行う。"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from engines.affiliate_ad_source import parse_ad_source


BASE_DIR = Path(__file__).resolve().parents[1]
PROGRAM_FILE = BASE_DIR / "data" / "affiliate_programs" / "program_research_results.json"
QUEUE_FILE = BASE_DIR / "data" / "affiliate_programs" / "human_approval_queue.json"
REGISTRY_FILE = BASE_DIR / "data" / "affiliate_links.json"
PROGRAMS_CSV_FILE = BASE_DIR / "data" / "affiliate_programs.csv"
BACKUP_DIR = BASE_DIR / "logs" / "deleted_affiliates"
STATUSES = {"approved_for_application", "applied", "approved", "rejected"}
STATUS_IMPORT_VALUES = {
    "申請予定": "approved_for_application",
    "申請中": "applied",
    "承認済み": "approved",
    "否認": "rejected",
    **{status: status for status in STATUSES},
}
IMPORT_HEADERS = [
    "サービス名",
    "ASP案件名",
    "ASP・運営元",
    "申請ページURL",
    "プログラムID",
    "状態",
    "広告ソース",
    "PR内容・掲載条件",
    "メモ",
]


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
        parsed_ad = parse_ad_source(args.ad_source) if args.ad_source.strip() else {}
        affiliate_url = str(parsed_ad.get("href", ""))
        official_url = args.program_url.strip() or affiliate_url
        if official_url:
            rows.append(
                {
                    "tool_name": service,
                    "network": args.network.strip(),
                    "program_name": args.program_name.strip() or service,
                    "status": status,
                    "official_url": official_url,
                    "affiliate_url": affiliate_url,
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
    parsed_ad = parse_ad_source(args.ad_source) if args.ad_source.strip() else {}
    if args.status == "approved" and not parsed_ad:
        raise ValueError("承認済み案件には広告ソースが必要です。")

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
        "official_url": args.program_url.strip() or str(parsed_ad.get("href", "")),
        "affiliate_url": str(parsed_ad.get("href", "")),
        "ad_source": args.ad_source.strip(),
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


def create_import_template(output_path: Path) -> None:
    """Excelで編集できる一括登録用CSVひな形を作る。"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(IMPORT_HEADERS)
    print(f"CSVフォーマットを作成しました:\n{output_path}")


def read_import_rows(csv_path: Path) -> list[dict[str, str]]:
    """UTF-8またはWindows標準のCSVを読み込んで検証する。"""

    if not csv_path.is_file():
        raise ValueError(f"CSVファイルが見つかりません: {csv_path}")

    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp932"):
        try:
            with csv_path.open("r", encoding=encoding, newline="") as file:
                reader = csv.DictReader(file)
                headers = [str(value).strip() for value in (reader.fieldnames or [])]
                missing = [header for header in IMPORT_HEADERS if header not in headers]
                if missing:
                    raise ValueError("CSVに必要な項目がありません: " + "、".join(missing))
                rows = [
                    {key: str(value or "").strip() for key, value in row.items() if key}
                    for row in reader
                    if any(str(value or "").strip() for value in row.values())
                ]
            return rows
        except UnicodeDecodeError as error:
            last_error = error

    raise ValueError("CSVの文字コードを読み取れません。UTF-8で保存してください。") from last_error


def import_programs_csv(csv_path: Path) -> None:
    """CSVの案件を、サービス名をキーとして一括追加・更新する。"""

    rows = read_import_rows(csv_path)
    if not rows:
        raise ValueError("CSVに案件データがありません。")

    program_data = load_json(PROGRAM_FILE, {"programs": []})
    queue_data = load_json(QUEUE_FILE, {"programs": []})
    registry = load_json(REGISTRY_FILE, {})
    existing_programs = {
        str(item.get("service", "")).strip(): item
        for item in program_data.get("programs", [])
        if isinstance(item, dict)
    }
    existing_queue = {
        str(item.get("service", "")).strip(): item
        for item in queue_data.get("programs", [])
        if isinstance(item, dict)
    }

    prepared: list[SimpleNamespace] = []
    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=2):
        service = row.get("サービス名", "").strip()
        if not service:
            raise ValueError(f"{line_number}行目: サービス名が必要です。")
        if service in seen:
            raise ValueError(f"{line_number}行目: サービス名「{service}」が重複しています。")
        seen.add(service)

        raw_status = row.get("状態", "").strip()
        status = STATUS_IMPORT_VALUES.get(raw_status)
        if status is None:
            raise ValueError(
                f"{line_number}行目: 状態は申請予定・申請中・承認済み・否認のいずれかにしてください。"
            )

        old_program = existing_programs.get(service, {})
        old_queue = existing_queue.get(service, {})
        old_registry = registry.get(service, {}) if isinstance(registry.get(service), dict) else {}

        def supplied(header: str, *fallbacks: Any) -> str:
            value = row.get(header, "").strip()
            if value:
                return value
            for fallback in fallbacks:
                text = str(fallback or "").strip()
                if text:
                    return text
            return ""

        args = SimpleNamespace(
            service=service,
            program_name=supplied("ASP案件名", old_program.get("program_name"), service),
            network=supplied("ASP・運営元", old_program.get("network"), old_registry.get("network")),
            program_url=supplied("申請ページURL", old_program.get("program_url"), old_registry.get("official_url")),
            program_id=supplied("プログラムID", old_program.get("program_id"), old_registry.get("program_id")),
            commission=str(old_program.get("commission", "")).strip(),
            promotion_details=supplied("PR内容・掲載条件", old_program.get("promotion_details"), old_registry.get("promotion_details")),
            status=status,
            ad_source=supplied("広告ソース", old_registry.get("ad_source")),
            notes=supplied("メモ", old_queue.get("human_notes")),
        )
        if args.program_url and not args.program_url.startswith("http"):
            raise ValueError(f"{line_number}行目: 申請ページURLはhttpから入力してください。")
        if status == "approved":
            try:
                parse_ad_source(args.ad_source)
            except ValueError as error:
                raise ValueError(f"{line_number}行目: 承認済み案件には正しい広告ソースが必要です。") from error
        if args.network.lower() == "a8.net" and status == "approved" and not args.program_id:
            raise ValueError(f"{line_number}行目: A8.netの承認済み案件にはプログラムIDが必要です。")
        prepared.append(args)

    tracked_files = [PROGRAM_FILE, QUEUE_FILE, REGISTRY_FILE, PROGRAMS_CSV_FILE]
    snapshots = {path: path.read_bytes() if path.exists() else None for path in tracked_files}
    try:
        for args in prepared:
            add_program(args)
    except Exception:
        for path, content in snapshots.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(content)
        raise

    print(f"CSVから{len(prepared)}件を登録・更新しました。")


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
    add.add_argument("--ad-source", default="")
    add.add_argument("--notes", default="")
    delete = sub.add_parser("delete")
    delete.add_argument("--service", required=True)
    import_csv = sub.add_parser("import-csv")
    import_csv.add_argument("--file", required=True, type=Path)
    template = sub.add_parser("template")
    template.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "add":
        add_program(args)
    elif args.command == "delete":
        delete_program(args.service)
    elif args.command == "import-csv":
        import_programs_csv(args.file)
    else:
        create_import_template(args.output)


if __name__ == "__main__":
    main()
