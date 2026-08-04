import json
from pathlib import Path
from typing import Any


AFFILIATE_LINKS_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "affiliate_links.json"
)


def load_affiliate_registry() -> dict[str, dict[str, Any]]:
    """公式・アフィリエイトリンク台帳を読み込む。"""

    if not AFFILIATE_LINKS_FILE.exists():
        raise FileNotFoundError(
            "affiliate_links.jsonが見つかりません："
            f"{AFFILIATE_LINKS_FILE}"
        )

    try:
        data = json.loads(
            AFFILIATE_LINKS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "affiliate_links.jsonのJSON形式が不正です。"
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "affiliate_links.jsonの最上位は"
            "オブジェクトにしてください。"
        )

    validated: dict[str, dict[str, Any]] = {}

    for tool_name, item in data.items():
        if (
            not isinstance(tool_name, str)
            or not tool_name.strip()
            or not isinstance(item, dict)
        ):
            raise ValueError(
                "リンク台帳に不正なデータがあります。"
            )

        official_url = item.get("official_url")
        affiliate_url = item.get(
            "affiliate_url",
            "",
        )
        cta_label = item.get("cta_label")
        aliases = item.get("aliases", [])

        if (
            not isinstance(official_url, str)
            or not official_url.startswith("http")
        ):
            raise ValueError(
                f"{tool_name}のofficial_urlが不正です。"
            )

        if (
            not isinstance(affiliate_url, str)
            or (
                affiliate_url
                and not affiliate_url.startswith("http")
            )
        ):
            raise ValueError(
                f"{tool_name}のaffiliate_urlが不正です。"
            )

        if (
            not isinstance(cta_label, str)
            or not cta_label.strip()
        ):
            raise ValueError(
                f"{tool_name}のcta_labelが未入力です。"
            )

        if not isinstance(aliases, list):
            raise ValueError(
                f"{tool_name}のaliasesは配列にしてください。"
            )

        validated[tool_name.strip()] = {
            "official_url": official_url.strip(),
            "affiliate_url": affiliate_url.strip(),
            "cta_label": cta_label.strip(),
            "aliases": aliases,
        }

    return validated


def get_affiliate_tool_names() -> list[str]:
    """Writerが選択できる登録済みツール名を返す。"""

    return list(
        load_affiliate_registry().keys()
    )


def build_affiliate_section(
    recommended_tools: list[str],
) -> str:
    """おすすめツールからMarkdownのCTA欄を作る。"""

    if not recommended_tools:
        return ""

    registry = load_affiliate_registry()

    selected_tools = list(
        dict.fromkeys(recommended_tools)
    )

    lines = [
        "",
        "## 紹介したサービスを確認する",
        "",
    ]

    has_affiliate_link = False
    valid_tool_count = 0

    for tool_name in selected_tools:
        item = registry.get(tool_name)

        if item is None:
            continue

        affiliate_url = item["affiliate_url"]
        official_url = item["official_url"]

        destination_url = (
            affiliate_url
            if affiliate_url
            else official_url
        )

        if affiliate_url:
            has_affiliate_link = True

        lines.extend(
            [
                f"### {tool_name}",
                "",
                f"[{item['cta_label']}]"
                f"({destination_url})",
                "",
            ]
        )

        valid_tool_count += 1

    if valid_tool_count == 0:
        return ""

    if has_affiliate_link:
        lines.extend(
            [
                "> 本ページには広告・"
                "アフィリエイトリンクが含まれます。",
                "",
            ]
        )

    return "\n".join(lines)