import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

AFFILIATE_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_links.json"
)

CONTENT_EXPANSION_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_decisions.json"
)

EXPANSION_HISTORY_FILE = (
    BASE_DIR
    / "data"
    / "automation"
    / "expansion_history.json"
)

DEFAULT_SERVICES = {
    "DeepL": {
        "official_url": "https://www.deepl.com/",
        "aliases": [
            "DeepL",
            "DeepL Pro",
        ],
    },
    "Perplexity": {
        "official_url": "https://www.perplexity.ai/",
        "aliases": [
            "Perplexity",
            "Perplexity AI",
        ],
    },
    "ChatPDF": {
        "official_url": "https://www.chatpdf.com/",
        "aliases": [
            "ChatPDF",
        ],
    },
}

def load_affiliate_links(
) -> dict[str, dict[str, Any]]:
    """affiliate_links.jsonを読み込む。"""

    if not AFFILIATE_LINKS_FILE.exists():
        return {}

    try:
        data = json.loads(
            AFFILIATE_LINKS_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "affiliate_links.jsonの"
            "JSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "affiliate_links.jsonの"
            "最上位はオブジェクトにしてください。"
        )

    return data

def load_expansion_topics(
) -> set[str]:
    """Expansion判断からサービス候補Topicを取得する。"""

    if not CONTENT_EXPANSION_FILE.exists():
        return set()

    try:
        data = json.loads(
            CONTENT_EXPANSION_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return set()

    decisions = data.get(
        "decisions",
        [],
    )

    if not isinstance(
        decisions,
        list,
    ):
        return set()

    topics: set[str] = set()

    for item in decisions:
        if not isinstance(
            item,
            dict,
        ):
            continue

        topic = str(
            item.get(
                "topic",
                "",
            )
        ).strip()

        if topic:
            topics.add(
                topic
            )

    return topics

def load_expansion_history_topics(
) -> set[str]:
    """記事化済みExpansion履歴からTopicを取得する。"""

    if not EXPANSION_HISTORY_FILE.exists():
        return set()

    try:
        data = json.loads(
            EXPANSION_HISTORY_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return set()

    history = data.get(
        "history",
        [],
    )

    if not isinstance(
        history,
        list,
    ):
        return set()

    topics: set[str] = set()

    for item in history:
        if not isinstance(
            item,
            dict,
        ):
            continue

        topic = str(
            item.get(
                "topic",
                "",
            )
        ).strip()

        if topic:
            topics.add(
                topic
            )

    return topics

def build_registry_item(
    service: str,
    official_url: str,
    aliases: list[str],
) -> dict[str, Any]:
    """新規サービスの初期Registry情報を作る。"""

    return {
        "official_url":
            official_url,
        "affiliate_url":
            "",
        "cta_label":
            f"{service}を公式サイトで確認する",
        "aliases":
            aliases,
        "affiliate_status":
            "none",
        "network":
            "",
        "program_name":
            "公式リンク",
        "reward_type":
            "none",
        "reward_value":
            0.0,
        "currency":
            "JPY",
        "conversion_action":
            "なし",
        "cookie_days":
            0,
        "program_score":
            0.0,
        "last_verified":
            "",
    }


def sync_service_registry(
) -> list[str]:
    """Expansion候補から未登録サービスをRegistryへ追加する。"""

    registry = (
        load_affiliate_links()
    )

    expansion_topics = (
        load_expansion_topics()
        | load_expansion_history_topics()
    )

    added_services: list[
        str
    ] = []

    for service, config in (
        DEFAULT_SERVICES.items()
    ):
        if service not in expansion_topics:
            continue

        if service in registry:
            continue

        registry[
            service
        ] = build_registry_item(
            service=service,
            official_url=str(
                config[
                    "official_url"
                ]
            ),
            aliases=list(
                config[
                    "aliases"
                ]
            ),
        )

        added_services.append(
            service
        )

    if added_services:
        AFFILIATE_LINKS_FILE.write_text(
            json.dumps(
                registry,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    return added_services

def main() -> None:
    added_services = (
        sync_service_registry()
    )

    print(
        "\n===== Service Registry Sync =====\n"
    )

    if not added_services:
        print(
            "新規Registry追加はありません。"
        )
        return

    for service in added_services:
        print(
            f"追加：{service}"
        )

    print(
        "\n保存先："
        f"{AFFILIATE_LINKS_FILE}"
    )


if __name__ == "__main__":
    main()