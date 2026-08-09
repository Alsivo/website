import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import (
    ATLAS_LOCK_TIMEOUT_HOURS,
    ATLAS_LOG_RETENTION_DAYS,
    ATLAS_RUN_AFFILIATE_MANAGER,
    ATLAS_RUN_SEARCH_CONSOLE,
    ATLAS_USE_CACHED_SEARCH_CONSOLE_ON_ERROR,
    ATLAS_RUN_GA4_AFFILIATE,
    ATLAS_USE_CACHED_GA4_ON_ERROR,
    ATLAS_RUN_REVENUE_TRACKER,
    ATLAS_USE_CACHED_REVENUE_ON_ERROR,
)
from utils.git_publisher import (
    publish_additional_files,
)

BASE_DIR = Path(__file__).resolve().parent

AUTOMATION_DIR = (
    BASE_DIR
    / "data"
    / "automation"
)

LOG_DIR = (
    BASE_DIR
    / "logs"
    / "atlas"
)

LOCK_FILE = (
    AUTOMATION_DIR
    / "atlas.lock"
)

LATEST_RUN_FILE = (
    AUTOMATION_DIR
    / "latest_run.json"
)

EDITORIAL_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "editorial"
    / "latest_decision.json"
)

INTERNAL_LINKS_FILE = (
    BASE_DIR
    / "data"
    / "internal_links"
    / "internal_links.json"
)

def ensure_directories() -> None:
    """自動運転に必要なフォルダを作る。"""

    AUTOMATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def create_log_file() -> Path:
    """今回の実行ログファイルを作る。"""

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return (
        LOG_DIR
        / f"{timestamp}.log"
    )


def log(
    message: str,
    log_file: Path,
) -> None:
    """コンソールとログファイルへ同時出力する。"""

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    line = (
        f"[{timestamp}] "
        f"{message}"
    )

    print(line)

    with log_file.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            line + "\n"
        )


def remove_old_logs() -> None:
    """保存期間を過ぎたログを削除する。"""

    cutoff = (
        datetime.now()
        - timedelta(
            days=ATLAS_LOG_RETENTION_DAYS
        )
    )

    for filepath in LOG_DIR.glob(
        "*.log"
    ):
        try:
            modified = datetime.fromtimestamp(
                filepath.stat().st_mtime
            )

            if modified < cutoff:
                filepath.unlink()

        except OSError:
            continue


def acquire_lock() -> None:
    """Atlasの二重実行を防ぐ。"""

    if LOCK_FILE.exists():
        try:
            lock_data = json.loads(
                LOCK_FILE.read_text(
                    encoding="utf-8",
                )
            )

            started_at = datetime.fromisoformat(
                lock_data["started_at"]
            )

            timeout = timedelta(
                hours=ATLAS_LOCK_TIMEOUT_HOURS
            )

            if (
                datetime.now()
                - started_at
                < timeout
            ):
                raise RuntimeError(
                    "Atlasはすでに実行中です。"
                )

        except (
            json.JSONDecodeError,
            KeyError,
            ValueError,
        ):
            pass

        LOCK_FILE.unlink(
            missing_ok=True
        )

    LOCK_FILE.write_text(
        json.dumps(
            {
                "started_at":
                    datetime.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def release_lock() -> None:
    """実行ロックを解除する。"""

    LOCK_FILE.unlink(
        missing_ok=True
    )


def run_python_script(
    script_name: str,
    log_file: Path,
    input_text: str | None = None,
    arguments: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """既存Pythonスクリプトを実行する。"""

    command = [
        sys.executable,
        str(
            BASE_DIR
            / script_name
        ),
    ]

    if arguments:
        command.extend(arguments)

    log(
        "実行："
        + " ".join(command),
        log_file,
    )

    env = dict(os.environ)

    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        input=input_text,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if result.stdout:
        for line in result.stdout.splitlines():
            log(
                f"  {line}",
                log_file,
            )

    if result.stderr:
        for line in result.stderr.splitlines():
            log(
                f"  [stderr] {line}",
                log_file,
            )

    return result


def sync_affiliate_manager(
    log_file: Path,
) -> None:
    """Affiliate Managerを同期する。"""

    if not ATLAS_RUN_AFFILIATE_MANAGER:
        log(
            "Affiliate Manager同期：SKIP",
            log_file,
        )
        return

    log(
        "Affiliate Managerを同期します。",
        log_file,
    )

    code = (
        "from engines.affiliate_manager "
        "import print_affiliate_selection; "
        "print_affiliate_selection()"
    )

    env = dict(os.environ)

    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    if result.stdout:
        for line in result.stdout.splitlines():
            log(
                f"  {line}",
                log_file,
            )

    if result.returncode != 0:
        raise RuntimeError(
            "Affiliate Manager同期に"
            "失敗しました。"
        )


def update_search_console(
    log_file: Path,
) -> None:
    """Search Consoleデータを更新する。"""

    if not ATLAS_RUN_SEARCH_CONSOLE:
        log(
            "Search Console更新：SKIP",
            log_file,
        )
        return

    log(
        "Search Consoleデータを更新します。",
        log_file,
    )

    result = run_python_script(
        "search_console_report.py",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Search Console更新成功。",
            log_file,
        )
        return

    if (
        ATLAS_USE_CACHED_SEARCH_CONSOLE_ON_ERROR
    ):
        log(
            "Search Console更新に失敗しました。"
            "前回取得データを使用して続行します。",
            log_file,
        )
        return

    raise RuntimeError(
        "Search Console更新に"
        "失敗しました。"
    )

def update_ga4_affiliate_clicks(
    log_file: Path,
) -> None:
    """GA4のAffiliate Clickデータを更新する。"""

    if not ATLAS_RUN_GA4_AFFILIATE:
        log(
            "GA4 Affiliate Click更新：SKIP",
            log_file,
        )
        return

    log(
        "GA4 Affiliate Clickデータを更新します。",
        log_file,
    )

    result = run_python_script(
        "ga4_affiliate_report.py",
        log_file,
    )

    if result.returncode == 0:
        log(
            "GA4 Affiliate Click更新成功。",
            log_file,
        )
        return

    if ATLAS_USE_CACHED_GA4_ON_ERROR:
        log(
            "GA4 Affiliate Click更新に失敗しました。"
            "前回取得データを使用して続行します。",
            log_file,
        )
        return

    raise RuntimeError(
        "GA4 Affiliate Clickデータの"
        "更新に失敗しました。"
    )


def update_revenue_summary(
    log_file: Path,
) -> None:
    """Affiliate収益サマリーを更新する。"""

    if not ATLAS_RUN_REVENUE_TRACKER:
        log(
            "Revenue Summary更新：SKIP",
            log_file,
        )
        return

    log(
        "Revenue Summaryを更新します。",
        log_file,
    )

    result = run_python_script(
        "engines/revenue_tracker.py",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Revenue Summary更新成功。",
            log_file,
        )
        return

    if ATLAS_USE_CACHED_REVENUE_ON_ERROR:
        log(
            "Revenue Summary更新に失敗しました。"
            "前回集計結果を使用して続行します。",
            log_file,
        )
        return

    raise RuntimeError(
        "Revenue Summaryの"
        "更新に失敗しました。"
    )


def run_editorial_director(
    log_file: Path,
) -> dict[str, Any]:
    """AI編集長を実行し判断を読み込む。"""

    log(
        "AI編集長を実行します。",
        log_file,
    )

    result = run_python_script(
        "editorial.py",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "AI編集長の実行に"
            "失敗しました。"
        )

    if not EDITORIAL_DECISION_FILE.exists():
        raise FileNotFoundError(
            "AI編集長の判断ファイルが"
            "生成されませんでした。"
        )

    decision = json.loads(
        EDITORIAL_DECISION_FILE.read_text(
            encoding="utf-8",
        )
    )

    return decision


def run_new_article(
    decision: dict[str, Any],
    log_file: Path,
) -> None:
    """新規記事を生成し、MDX作成まで確認する。"""

    target_keyword = str(
        decision.get(
            "target_keyword",
            "",
        )
    ).strip()

    log(
        "新規記事生成を開始します。"
        f"編集長候補：{target_keyword}",
        log_file,
    )

    blog_dir = (
        BASE_DIR.parent
        / "content"
        / "blog"
    )

    before_files = {
        path.resolve()
        for path in blog_dir.glob("*.mdx")
    }

    result = run_python_script(
        "main.py",
        log_file,
        input_text="2\n",
    )

    if result.returncode != 0:
        raise RuntimeError(
            "main.pyが異常終了しました。"
        )

    after_files = {
        path.resolve()
        for path in blog_dir.glob("*.mdx")
    }

    new_files = (
        after_files
        - before_files
    )

    if not new_files:
        raise RuntimeError(
            "main.pyは正常終了しましたが、"
            "新しいMDX記事が生成されませんでした。"
        )

    for filepath in sorted(new_files):
        log(
            "新規記事を確認："
            f"{filepath.name}",
            log_file,
        )


def run_rewrite(
    decision: dict[str, Any],
    log_file: Path,
) -> Path:
    """AI編集長が選択した記事をリライトする。"""

    slug = str(
        decision.get(
            "target_slug",
            "",
        )
    ).strip()

    if not slug:
        raise ValueError(
            "rewrite_articleですが、"
            "target_slugがありません。"
        )

    log(
        "リライトを開始します："
        f"{slug}",
        log_file,
    )

    result = run_python_script(
        "rewrite.py",
        log_file,
        arguments=[
            slug,
        ],
    )

    if result.returncode != 0:
        raise RuntimeError(
            "記事リライトに失敗しました。"
        )
    article_path = (
        BASE_DIR.parent
        / "content"
        / "blog"
        / f"{slug}.mdx"
    )

    if not article_path.exists():
        raise FileNotFoundError(
            "リライト記事が見つかりません："
            f"{article_path}"
        )

    return article_path


def save_latest_run(
    status: str,
    action: str,
    message: str,
) -> None:
    """最新の自動運転結果を保存する。"""

    LATEST_RUN_FILE.write_text(
        json.dumps(
            {
                "finished_at":
                    datetime.now().isoformat(),
                "status":
                    status,
                "action":
                    action,
                "message":
                    message,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ensure_directories()

    remove_old_logs()

    log_file = create_log_file()

    action = ""

    rewritten_article_path: Path | None = None

    try:
        acquire_lock()

        log(
            "================================",
            log_file,
        )

        log(
            "Atlas自動運転を開始します。",
            log_file,
        )

        log(
            "================================",
            log_file,
        )

        sync_affiliate_manager(
            log_file
        )

        update_search_console(
            log_file
        )

        update_ga4_affiliate_clicks(
            log_file
        )

        update_revenue_summary(
            log_file
        )

        decision = (
            run_editorial_director(
                log_file
            )
        )

        action = str(
            decision.get(
                "action",
                "",
            )
        )

        priority_score = (
            decision.get(
                "priority_score",
                0,
            )
        )

        reason = str(
            decision.get(
                "reason",
                "",
            )
        )

        # ----------------------------------------------------
        # リライトクールダウン確認
        # ----------------------------------------------------

        if action == "rewrite_article":
            rewrite_allowed = (
                decision.get(
                    "rewrite_allowed",
                    True,
                )
            )

            rewrite_cooldown_reason = str(
                decision.get(
                    "rewrite_cooldown_reason",
                    "",
                )
            ).strip()

            if rewrite_allowed is False:
                target_slug = str(
                    decision.get(
                        "target_slug",
                        "",
                    )
                ).strip()

                log(
                    "リライト対象は"
                    "クールダウン中のため"
                    "今回は実行しません："
                    f"{target_slug}",
                    log_file,
                )

                if rewrite_cooldown_reason:
                    log(
                        "クールダウン理由："
                        f"{rewrite_cooldown_reason}",
                        log_file,
                    )

                action = "wait"

                decision[
                    "action"
                ] = "wait"

        log(
            "AI編集長判断："
            f"{action}",
            log_file,
        )

        log(
            "優先度："
            f"{priority_score}/100",
            log_file,
        )

        log(
            "理由："
            f"{reason}",
            log_file,
        )

        if action == "new_article":
            run_new_article(
                decision,
                log_file,
            )

        elif action == "rewrite_article":
            rewritten_article_path = (
                run_rewrite(
                    decision,
                    log_file,
                )
            )

        elif action == "wait":
            log(
                "本日は記事生成・リライトを"
                "行いません。",
                log_file,
            )

        else:
            raise ValueError(
                "AI編集長が不正なactionを"
                f"返しました：{action}"
            )

        if action in {
            "new_article",
            "rewrite_article",
        }:
            log(
                "AI関連記事を更新します。",
                log_file,
            )

            internal_link_result = (
                run_python_script(
                    "internal_links.py",
                    log_file,
                )
            )

            if (
                internal_link_result.returncode
                != 0
            ):
                raise RuntimeError(
                    "AI関連記事更新に"
                    "失敗しました。"
                )

            log(
                "AI関連記事更新完了。",
                log_file,
            )

            log(
                "更新コンテンツを"
                "GitHubへ反映します。",
                log_file,
            )

            publish_paths = [
                INTERNAL_LINKS_FILE,
            ]

            if (
                action == "rewrite_article"
                and rewritten_article_path
                is not None
            ):
                publish_paths.append(
                    rewritten_article_path
                )

            pushed = (
                publish_additional_files(
                    paths=publish_paths,
                    commit_prefix=(
                        "Update Atlas content"
                    ),
                )
            )

            if pushed:
                log(
                    "更新コンテンツの"
                    "GitHub Push完了。",
                    log_file,
                )
            else:
                log(
                    "更新コンテンツに"
                    "Git差分がないため、"
                    "Pushをスキップしました。",
                    log_file,
                )

        save_latest_run(
            status="success",
            action=action,
            message="Atlas自動運転完了",
        )

        log(
            "Atlas自動運転が完了しました。",
            log_file,
        )

    except Exception as error:
        save_latest_run(
            status="error",
            action=action,
            message=str(error),
        )

        log(
            "Atlas自動運転に失敗しました："
            f"{error}",
            log_file,
        )

        raise

    finally:
        release_lock()


if __name__ == "__main__":
    main()