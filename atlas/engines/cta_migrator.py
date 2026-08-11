import argparse
import re
from pathlib import Path

from engines.affiliate_registry import (
    load_affiliate_registry,
)


BASE_DIR = Path(__file__).resolve().parents[1]

BLOG_DIR = (
    BASE_DIR.parent
    / "content"
    / "blog"
)


CTA_HEADING = (
    "## 紹介したサービスを確認する"
)

NEXT_SECTION_PATTERN = re.compile(
    r"^##\s+",
    re.MULTILINE,
)

MARKDOWN_LINK_PATTERN = re.compile(
    r"^\[(?P<label>.+?)\]"
    r"\((?P<url>https?://.+?)\)$"
)

AFFILIATE_LINK_PATTERN = re.compile(
    r'^<AffiliateLink\s+'
    r'href="(?P<url>[^"]+)"\s+'
    r'service="(?P<service>[^"]+)"'
    r'(?P<attrs>[^>]*)>'
    r'(?P<label>.*?)'
    r'</AffiliateLink>$'
)


def extract_cta_section(
    text: str,
) -> tuple[
    int,
    int,
    str,
] | None:
    """
    CTA見出しから次のH2直前までを取得する。
    """

    start = text.find(
        CTA_HEADING
    )

    if start == -1:
        return None

    search_start = (
        start
        + len(CTA_HEADING)
    )

    match = NEXT_SECTION_PATTERN.search(
        text,
        search_start,
    )

    end = (
        match.start()
        if match
        else len(text)
    )

    section = text[
        start:end
    ]

    return (
        start,
        end,
        section,
    )


def parse_cta_items(
    section: str,
) -> list[
    dict[str, str]
]:
    """
    CTAセクション内の
    サービス名とリンクを抽出する。
    """

    lines = section.splitlines()

    items: list[
        dict[str, str]
    ] = []

    current_service = ""

    for raw_line in lines:
        line = raw_line.strip()

        if line.startswith("### "):
            current_service = (
                line[4:].strip()
            )
            continue

        if not current_service:
            continue

        affiliate_match = (
            AFFILIATE_LINK_PATTERN.match(
                line
            )
        )

        if affiliate_match:
            attrs = (
                affiliate_match.group(
                    "attrs"
                )
            )

            cta_type_match = re.search(
                r'ctaType="([^"]+)"',
                attrs,
            )

            placement_match = re.search(
                r'ctaPlacement="([^"]+)"',
                attrs,
            )

            items.append(
                {
                    "service":
                        affiliate_match.group(
                            "service"
                        ),
                    "url":
                        affiliate_match.group(
                            "url"
                        ),
                    "label":
                        affiliate_match.group(
                            "label"
                        ),
                    "cta_type":
                        (
                            cta_type_match.group(1)
                            if cta_type_match
                            else ""
                        ),
                    "placement":
                        (
                            placement_match.group(1)
                            if placement_match
                            else ""
                        ),
                }
            )

            current_service = ""
            continue

        markdown_match = (
            MARKDOWN_LINK_PATTERN.match(
                line
            )
        )

        if markdown_match:
            items.append(
                {
                    "service":
                        current_service,
                    "url":
                        markdown_match.group(
                            "url"
                        ),
                    "label":
                        markdown_match.group(
                            "label"
                        ),
                    "cta_type": "",
                    "placement": "",
                }
            )

            current_service = ""
            continue

        if (
            line
            and not line.startswith("#")
            and "公式サイト" in line
        ):
            items.append(
                {
                    "service":
                        current_service,
                    "url": "",
                    "label": line,
                    "cta_type": "",
                    "placement": "",
                }
            )

            current_service = ""

    return items


def resolve_service_name(
    raw_service: str,
    registry: dict[
        str,
        dict,
    ],
) -> str | None:
    """
    registryの正式サービス名へ解決する。
    """

    if raw_service in registry:
        return raw_service

    normalized = (
        raw_service
        .replace(
            "（GmailのAI）",
            "",
        )
        .strip()
    )

    if normalized in registry:
        return normalized

    for service_name, item in (
        registry.items()
    ):
        aliases = item.get(
            "aliases",
            [],
        )

        if normalized in aliases:
            return service_name

    return None


def build_new_section(
    items: list[
        dict[str, str]
    ],
    registry: dict[
        str,
        dict,
    ],
) -> tuple[
    str | None,
    list[str],
]:
    """
    既存CTAを新AffiliateLink形式へ変換する。
    """

    converted: list[str] = []

    errors: list[str] = []

    valid_index = 0

    for item in items:
        service_name = (
            resolve_service_name(
                item["service"],
                registry,
            )
        )

        if service_name is None:
            errors.append(
                "サービス名を解決できません: "
                + item["service"]
            )
            continue

        registry_item = registry[
            service_name
        ]

        affiliate_status = str(
            registry_item.get(
                "affiliate_status",
                "none",
            )
        )

        affiliate_url = str(
            registry_item.get(
                "affiliate_url",
                "",
            )
        ).strip()

        official_url = str(
            registry_item.get(
                "official_url",
                "",
            )
        ).strip()

        network = str(
            registry_item.get(
                "network",
                "",
            )
        ).strip()

        use_affiliate = (
            affiliate_status
            == "active"
            and bool(
                affiliate_url
            )
        )

        existing_url = (
            item["url"].strip()
            if item["url"].strip().startswith(
                "http"
            )
            else ""
        )

        destination_url = (
            affiliate_url
            if use_affiliate
            else (
                existing_url
                if existing_url
                else official_url
            )
        )

        link_type = (
            "affiliate"
            if use_affiliate
            else "official"
        )

        network_value = (
            network
            if use_affiliate
            and network
            else "none"
        )

        cta_type = (
            item["cta_type"]
            if item["cta_type"]
            else (
                "primary"
                if valid_index == 0
                else "secondary"
            )
        )

        placement = (
            item["placement"]
            if item["placement"]
            else "before_faq"
        )

        label = (
            item["label"].strip()
            if item["label"].strip()
            else registry_item[
                "cta_label"
            ]
        )

        markup = (
            "<AffiliateLink"
            f' href="{destination_url}"'
            f' service="{service_name}"'
            f' linkType="{link_type}"'
            f' network="{network_value}"'
            f' ctaType="{cta_type}"'
            f' ctaPlacement="{placement}"'
            ">"
            f"{label}"
            "</AffiliateLink>"
        )

        converted.append(
            markup
        )

        valid_index += 1

    if errors:
        return (
            None,
            errors,
        )

    lines = [
        "## 公式情報を確認する",
        "",
    ]

    for markup in converted:
        lines.append(
            markup
        )
        lines.append("")

    return (
        "\n".join(
            lines
        ).rstrip(),
        [],
    )


def scan_file(
    filepath: Path,
    registry: dict[
        str,
        dict,
    ],
) -> dict | None:
    """
    1記事分のCTA変換候補を返す。
    """

    text = filepath.read_text(
        encoding="utf-8",
    )

    extracted = (
        extract_cta_section(
            text
        )
    )

    if extracted is None:
        return None

    start, end, section = (
        extracted
    )

    items = parse_cta_items(
        section
    )

    if not items:
        return {
            "file": filepath,
            "before": section,
            "after": None,
            "errors": [
                "CTA項目を抽出できません"
            ],
        }

    new_section, errors = (
        build_new_section(
            items,
            registry,
        )
    )

    return {
        "file": filepath,
        "before": section,
        "after": new_section,
        "errors": errors,
        "start": start,
        "end": end,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "既存記事のCTAを"
            "AffiliateLink形式へ移行します。"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="実ファイルへ変更を適用します。",
    )

    args = parser.parse_args()

    apply_changes = args.apply

    registry = (
        load_affiliate_registry()
    )

    print(
        "\n===== CTA Migrator =====\n"
    )

    if apply_changes:
        print("モード：APPLY")
        print(
            "実ファイルを変更します。\n"
        )
    else:
        print("モード：DRY RUN")
        print(
            "実ファイルは変更しません。\n"
        )

    files = sorted(
        BLOG_DIR.glob(
            "*.mdx"
        )
    )

    total_files = 0
    error_files = 0

    for filepath in files:
        result = scan_file(
            filepath,
            registry,
        )

        if result is None:
            continue

        total_files += 1

        print(
            "--------------------------------"
        )

        print(
            f"FILE: {filepath.name}"
        )

        if result["errors"]:
            error_files += 1

            print(
                "\nERROR:"
            )

            for error in (
                result["errors"]
            ):
                print(
                    "- "
                    + error
                )

            continue

        print(
            "\nBEFORE:"
        )

        print(
            result["before"].strip()
        )

        print(
            "\nAFTER:"
        )

        print(
            result["after"]
        )
        if apply_changes:
            original_text = (
                filepath.read_text(
                    encoding="utf-8",
                )
            )

            updated_text = (
                original_text[
                    :result["start"]
                ]
                + result["after"]
                + original_text[
                    result["end"]:
                ]
            )

            filepath.write_text(
                updated_text,
                encoding="utf-8",
            )

            print(
                "\nAPPLIED: "
                + filepath.name
            )

    print(
        "\n================================"
    )

    print(
        f"対象記事数：{total_files}"
    )

    print(
        f"エラー記事数：{error_files}"
    )

    if apply_changes:
        print(
            "変更を実ファイルへ"
            "適用しました。"
        )
    else:
        print(
            "※ DRY RUNのため"
            "実ファイルは変更していません。"
        )

    print(
        "================================\n"
    )


if __name__ == "__main__":
    main()