from engines.search_console import (
    print_search_console_report,
)


if __name__ == "__main__":
    try:
        print_search_console_report()
    except Exception as error:
        print(
            "\nSearch Consoleの取得に"
            f"失敗しました：{error}"
        )