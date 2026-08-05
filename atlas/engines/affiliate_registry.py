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

        affiliate_status = item.get(
            "affiliate_status",
            "none",
        )
        network = item.get(
            "network",
            "",
        )
        program_name = item.get(
            "program_name",
            "",
        )

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

        if not isinstance(
            affiliate_status,
            str,
        ):
            raise ValueError(
                f"{tool_name}のaffiliate_statusが不正です。"
            )

        if affiliate_status not in {
            "none",
            "pending",
            "active",
            "paused",
            "rejected",
        }:
            raise ValueError(
                f"{tool_name}のaffiliate_statusが"
                "許可されていません："
                f"{affiliate_status}"
            )

        if not isinstance(network, str):
            raise ValueError(
                f"{tool_name}のnetworkが不正です。"
            )

        if not isinstance(program_name, str):
            raise ValueError(
                f"{tool_name}のprogram_nameが不正です。"
            )

        if (
            affiliate_status == "active"
            and not affiliate_url
        ):
            raise ValueError(
                f"{tool_name}はactiveですが、"
                "affiliate_urlが未入力です。"
            )

        validated[tool_name.strip()] = {
            "official_url": official_url.strip(),
            "affiliate_url": affiliate_url.strip(),
            "cta_label": cta_label.strip(),
            "aliases": aliases,
            "affiliate_status": (
                affiliate_status.strip()
            ),
            "network": network.strip(),
            "program_name": (
                program_name.strip()
            ),
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
    """おすすめツールからMDX形式のCTA欄を作る。"""

    if not recommended_tools:
        return ""

    registry = load_affiliate_registry()

    selected_tools = list(
        dict.fromkeys(
            tool_name.strip()
            for tool_name in recommended_tools
            if isinstance(tool_name, str)
            and tool_name.strip()
        )
    )

    lines = [
        "",
        "## 紹介したサービスを確認する",
        "",
    ]

    valid_tool_count = 0

    for tool_name in selected_tools:
        item = registry.get(tool_name)

        if item is None:
            continue

        affiliate_url = str(
            item.get(
                "affiliate_url",
                "",
            )
        ).strip()

        official_url = str(
            item.get(
                "official_url",
                "",
            )
        ).strip()

        affiliate_status = str(
            item.get(
                "affiliate_status",
                "none",
            )
        ).strip()

        affiliate_network = str(
            item.get(
                "network",
                "",
            )
        ).strip()

        use_affiliate_link = (
            affiliate_status == "active"
            and bool(affiliate_url)
        )

        destination_url = (
            affiliate_url
            if use_affiliate_link
            else official_url
        )

        link_type = (
            "affiliate"
            if use_affiliate_link
            else "official"
        )

        network = (
            affiliate_network
            if use_affiliate_link
            and affiliate_network
            else "none"
        )

        link_markup = (
            "<AffiliateLink"
            f' href="{destination_url}"'
            f' service="{tool_name}"'
            f' linkType="{link_type}"'
            f' network="{network}"'
            ">"
            f"{item['cta_label']}"
            "</AffiliateLink>"
        )

        lines.extend(
            [
                f"### {tool_name}",
                "",
                link_markup,
                "",
            ]
        )

        valid_tool_count += 1

    if valid_tool_count == 0:
        return ""

    return "\n".join(lines)