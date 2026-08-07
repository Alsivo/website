from engines.internal_linker import (
    build_internal_links,
    refine_internal_links_with_ai,
    save_internal_links,
)


def main() -> None:
    print(
        "\n[Internal Links] "
        "関連記事候補を抽出中...\n"
    )

    candidates = build_internal_links()

    print(
        "\n[Internal Links] "
        "AIによる最終選定中...\n"
    )

    refined = refine_internal_links_with_ai(
        candidates
    )

    save_internal_links(
        refined
    )

    print(
        "\n===== Internal Links 更新完了 ====="
    )
    print(
        "internal_links.jsonを更新しました。"
    )


if __name__ == "__main__":
    main()