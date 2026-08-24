import json
from html import escape
from pathlib import Path
from typing import Any

from engines.affiliate_ad_source import parse_ad_source


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
        ad_source = item.get(
            "ad_source",
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
            or (
                official_url
                and not official_url.startswith("http")
            )
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

        if not isinstance(ad_source, str):
            raise ValueError(
                f"{tool_name}のad_sourceが不正です。"
            )

        if not isinstance(program_id, str):
            raise ValueError(
                f"{tool_name}のprogram_idが不正です。"
            )

        if not isinstance(promotion_details, str):
            raise ValueError(
                f"{tool_name}のpromotion_detailsが不正です。"
            )

        parsed_ad: dict[str, Any] = {}
        if ad_source.strip():
            try:
                parsed_ad = parse_ad_source(ad_source)
            except ValueError as error:
                raise ValueError(
                    f"{tool_name}の広告ソース／紹介URLが不正です。"
                ) from error

        if affiliate_status == "active" and not parsed_ad and not affiliate_url:
            raise ValueError(
                f"{tool_name}はactiveですが、広告ソース／紹介URLが未入力です。"
            )

        validated[tool_name.strip()] = {
            "official_url": official_url.strip(),
            "affiliate_url": str(parsed_ad.get("href", affiliate_url)).strip(),
            "ad_source": ad_source.strip(),
            "banner_src": str(parsed_ad.get("banner_src", "")),
            "banner_width": int(parsed_ad.get("banner_width", 0) or 0),
            "banner_height": int(parsed_ad.get("banner_height", 0) or 0),
            "tracking_pixel_src": str(parsed_ad.get("tracking_pixel_src", "")),
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

    return [
        tool_name
        for tool_name, item in load_affiliate_registry().items()
        if item.get("official_url") or item.get("affiliate_url")
    ]


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

        banner_src = str(item.get("banner_src", "")).strip()
        banner_width = int(item.get("banner_width", 0) or 0)
        banner_height = int(item.get("banner_height", 0) or 0)
        tracking_pixel_src = str(item.get("tracking_pixel_src", "")).strip()

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
            banner_attributes = ""
            if use_affiliate_link and banner_src:
                banner_attributes = (
                    f' bannerSrc="{escape(banner_src, quote=True)}"'
                    f' bannerWidth="{banner_width}"'
                    f' bannerHeight="{banner_height}"'
                )
                if tracking_pixel_src:
                    banner_attributes += (
                        f' trackingPixelSrc="{escape(tracking_pixel_src, quote=True)}"'
                    )
            return (
                "<AffiliateLink"
                f' href="{escape(destination_url, quote=True)}"'
                f' service="{escape(tool_name, quote=True)}"'
                f' linkType="{link_type}"'
                f' network="{escape(network, quote=True)}"'
                f' ctaType="{cta_type}"'
                f' ctaPlacement="{placement}"'
                f"{banner_attributes}"
                ">"
                f"{escape(display_label)}"
                "</AffiliateLink>"
            )

        # ページ側が目次直後と各章の後へ同じCTAを表示するため、
        # MDXには抽出用のprimary CTAを1件だけ保存する。

        if cta_type == "primary":
            after_toc_links.append(
                build_link_markup(
                    "after_toc"
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

    # secondaryがある場合だけ、見出しを作らず抽出用に保存する。
    if footer_links:
        sections.append(
            "\n\n".join(
                footer_links
            )
        )

    return (
        "\n\n".join(
            sections
        ).strip()
    )
