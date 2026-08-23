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
        program_id = item.get(
            "program_id",
            "",
        )
        promotion_details = item.get(
            "promotion_details",
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

        if not isinstance(aliases, list):
            raise ValueError(
                f"{tool_name}のaliasesは"
                "配列にしてください。"
            )

        if not all(
            isinstance(alias, str)
            and alias.strip()
            for alias in aliases
        ):
            raise ValueError(
                f"{tool_name}のaliasesに"
                "不正な値があります。"
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

        if not isinstance(program_id, str):
            raise ValueError(
                f"{tool_name}のprogram_idが不正です。"
            )

        if not isinstance(promotion_details, str):
            raise ValueError(
                f"{tool_name}のpromotion_detailsが不正です。"
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
            "aliases": [
                alias.strip()
                for alias in aliases
            ],
            "affiliate_status": (
                affiliate_status.strip()
            ),
            "network": network.strip(),
            "program_name": (
                program_name.strip()
            ),
            "program_id": program_id.strip(),
            "promotion_details": promotion_details.strip(),
        }

    return validated


def get_affiliate_tool_names() -> list[str]:
    """Writerが選択できる登録済みツール名を返す。"""

    return list(
        load_affiliate_registry().keys()
    )


def build_affiliate_section(
    recommended_tools: list[str],
    cta_plan: dict[str, Any] | None = None,
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

    primary_service = None
    primary_cta_label = None
    cta_placement = "before_faq"

    if isinstance(
        cta_plan,
        dict,
    ):
        raw_primary_service = (
            cta_plan.get(
                "primary_service"
            )
        )

        raw_cta_label = (
            cta_plan.get(
                "cta_label"
            )
        )

        raw_placement = cta_plan.get(
            "placement"
        )

        if (
            isinstance(
                raw_primary_service,
                str,
            )
            and raw_primary_service.strip()
        ):
            primary_service = (
                raw_primary_service.strip()
            )

        if (
            isinstance(
                raw_cta_label,
                str,
            )
            and raw_cta_label.strip()
        ):
            primary_cta_label = (
                raw_cta_label.strip()
            )

        if raw_placement in {
            "after_toc",
            "after_comparison",
            "before_faq",
        }:
            cta_placement = raw_placement

    after_toc_links: list[str] = []
    footer_links: list[str] = []

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

        # cta_planで指定されたサービスをPrimaryにする。
        # 指定がない場合は最初の有効サービスをPrimaryにする。
        if primary_service is not None:
            cta_type = (
                "primary"
                if tool_name
                == primary_service
                else "secondary"
            )
        else:
            cta_type = (
                "primary"
                if valid_tool_count == 0
                else "secondary"
            )

        display_label = item[
            "cta_label"
        ]

        if (
            cta_type == "primary"
            and primary_cta_label
        ):
            display_label = (
                primary_cta_label
            )

        # ====================================================
        # CTA markup builder
        # ====================================================

        def build_link_markup(
            placement: str,
        ) -> str:
            return (
                "<AffiliateLink"
                f' href="{destination_url}"'
                f' service="{tool_name}"'
                f' linkType="{link_type}"'
                f' network="{network}"'
                f' ctaType="{cta_type}"'
                f' ctaPlacement="{placement}"'
                ">"
                f"{display_label}"
                "</AffiliateLink>"
            )

        # ====================================================
        # Primary CTA
        # 必ず「目次直後」と「記事後半」の2か所に配置する
        # ====================================================

        if cta_type == "primary":
            after_toc_links.append(
                build_link_markup(
                    "after_toc"
                )
            )

            # 後半CTAの配置場所は
            # cta_planの判断を利用する。
            # after_toc指定の場合はbefore_faqへ配置する。
            footer_placement = (
                "before_faq"
                if cta_placement == "after_toc"
                else cta_placement
            )

            footer_links.append(
                build_link_markup(
                    footer_placement
                )
            )

        # ====================================================
        # Secondary CTA
        # 記事後半だけに配置する
        # ====================================================

        else:
            footer_placement = (
                "before_faq"
                if cta_placement == "after_toc"
                else cta_placement
            )

            footer_links.append(
                build_link_markup(
                    footer_placement
                )
            )

        valid_tool_count += 1

    if valid_tool_count == 0:
        return ""

    sections: list[str] = []

    # 目次直後表示用。
    # page.tsxが抽出して本文から除去する。
    if after_toc_links:
        sections.append(
            "\n\n".join(
                after_toc_links
            )
        )

    # 記事後半にはprimary + secondaryをまとめて表示する
    if footer_links:
        sections.append(
            "## 公式情報を確認する"
            + "\n\n"
            + "\n\n".join(
                footer_links
            )
        )

    return (
        "\n\n".join(
            sections
        ).strip()
    )
