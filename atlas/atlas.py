import argparse
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
from engines.expansion_history import (
    record_expansion_used,
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

EXPANSION_CANDIDATES_FILE = (
    BASE_DIR
    / "data"
    / "content_expansion"
    / "expansion_candidates.json"
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


def run_python_module(
    module_name: str,
    log_file: Path,
    arguments: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Pythonモジュールを -m 形式で実行する。"""

    command = [
        sys.executable,
        "-m",
        module_name,
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

def update_seo_feedback(
    log_file: Path,
) -> None:
    """SEO Feedbackと改善候補を更新する。"""

    log(
        "SEO Feedbackを更新します。",
        log_file,
    )

    result = run_python_script(
        "engines/seo_feedback.py",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SEO Feedbackの更新に失敗しました。"
        )

    result = run_python_script(
        "engines/seo_improvement_queue.py",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SEO Improvement Queueの"
            "更新に失敗しました。"
        )

    result = run_python_script(
        "engines/seo_action_planner.py",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SEO Action Planの"
            "更新に失敗しました。"
        )

    log(
        "SEO Feedback更新成功。",
        log_file,
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

    result = run_python_module(
        "engines.revenue_tracker",
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


def update_revenue_feedback(
    log_file: Path,
) -> None:
    """Revenue Feedbackを更新する。"""

    log(
        "Revenue Feedbackを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.revenue_feedback",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Revenue Feedback更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Revenue Feedbackの"
        "更新に失敗しました。"
    )


def update_revenue_action_queue(
    log_file: Path,
) -> None:
    """Revenue Action Queueを更新する。"""

    log(
        "Revenue Action Queueを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.revenue_action_queue",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Revenue Action Queue更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Revenue Action Queueの"
        "更新に失敗しました。"
    )


def update_domestic_asp_candidate_queue(
    log_file: Path,
) -> None:
    """国内ASP候補キューを更新する。"""

    log(
        "Domestic ASP Candidate Queueを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.domestic_asp_candidate_queue",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Domestic ASP Candidate Queue更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Domestic ASP Candidate Queueの"
        "更新に失敗しました。"
    )


def update_atlas_health(
    log_file: Path,
) -> None:
    """Atlas Health Statusを更新する。"""

    log(
        "Atlas Healthを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.atlas_health",
        log_file,
    )

    # atlas_health.py は
    # healthy=0 / error=1 / warning=2 を返す。
    # 1や2でもHealth JSON生成自体は成功している。
    if result.returncode in {
        0,
        1,
        2,
    }:
        log(
            "Atlas Health更新成功。"
            f" status_code={result.returncode}",
            log_file,
        )
        return

    raise RuntimeError(
        "Atlas Healthの更新処理自体に"
        "失敗しました。"
    )


def update_atlas_dashboard(
    log_file: Path,
) -> None:
    """Atlas Dashboardを更新する。"""

    log(
        "Atlas Dashboardを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.atlas_dashboard",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Atlas Dashboard更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Atlas Dashboardの"
        "更新に失敗しました。"
    )


def update_daily_report(
    log_file: Path,
) -> None:
    """Atlas Daily Reportを更新する。"""

    log(
        "Atlas Daily Reportを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.atlas_daily_report",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Atlas Daily Report更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Atlas Daily Reportの"
        "更新に失敗しました。"
    )


def update_performance_history(
    log_file: Path,
) -> None:
    """Performance Historyを更新する。"""

    log(
        "Performance Historyを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.performance_history",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Performance History更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Performance Historyの"
        "更新に失敗しました。"
    )


def update_performance_trend(
    log_file: Path,
) -> None:
    """Performance Trendを更新する。"""

    log(
        "Performance Trendを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.performance_trend",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Performance Trend更新成功。",
            log_file,
        )
        return


def update_optimization_decision(
    log_file: Path,
) -> bool:
    """Optimization Decisionを更新する。"""

    log(
        "Optimization Decisionを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.optimization_decision",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Optimization Decision更新成功。",
            log_file,
        )
        return True

    log(
        "Optimization Decisionの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_safe_executor(
    log_file: Path,
    apply_mode: bool = False,
) -> bool:
    """Safe Executorを更新する。"""

    log(
        "Safe Executorを更新します。",
        log_file,
    )

    arguments = (
        ["--apply"]
        if apply_mode
        else None
    )

    result = run_python_module(
        "engines.safe_executor",
        log_file,
        arguments=arguments,
    )

    if result.returncode == 0:
        log(
            "Safe Executor更新成功。",
            log_file,
        )
        return True

    log(
        "Safe Executorの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_optimization_history(
    log_file: Path,
) -> bool:
    """Optimization Historyを更新する。"""

    log(
        "Optimization Historyを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.optimization_history",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Optimization History更新成功。",
            log_file,
        )
        return True

    log(
        "Optimization Historyの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_optimization_outcome(
    log_file: Path,
) -> bool:
    """Optimization Outcomeを更新する。"""

    log(
        "Optimization Outcomeを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.optimization_outcome",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Optimization Outcome更新成功。",
            log_file,
        )
        return True

    log(
        "Optimization Outcomeの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_atlas_alert(
    log_file: Path,
) -> None:
    """Atlas Alertを更新する。"""

    log(
        "Atlas Alertを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.atlas_alert",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Atlas Alert更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Atlas Alertの"
        "更新に失敗しました。"
    )


def update_portfolio_plan(
    log_file: Path,
) -> None:
    """記事ポートフォリオ評価を更新する。"""

    log(
        "Portfolio Planを更新します。",
        log_file,
    )

    result = run_python_script(
        "engines/portfolio_optimizer.py",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Portfolio Plan更新成功。",
            log_file,
        )
        return

    raise RuntimeError(
        "Portfolio Planの"
        "更新に失敗しました。"
    )


def load_top_expansion_candidate(
) -> dict[str, Any] | None:
    """Expansion候補から最優先の新記事候補を返す。"""

    if not EXPANSION_CANDIDATES_FILE.exists():
        return None

    try:
        data = json.loads(
            EXPANSION_CANDIDATES_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return None

    candidates = data.get(
        "candidates",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        return None

    valid_candidates = [
        item
        for item in candidates
        if (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "status"
            )
            == "ready"
        )
    ]

    if not valid_candidates:
        return None

    valid_candidates.sort(
        key=lambda item: int(
            item.get(
                "priority",
                0,
            )
            or 0
        ),
        reverse=True,
    )

    return valid_candidates[0]

def mark_expansion_candidate_used(
    target_keyword: str,
) -> None:
    """使用したExpansion候補を完了状態にする。"""

    target_keyword = (
        target_keyword.strip()
    )

    if not target_keyword:
        return

    if not EXPANSION_CANDIDATES_FILE.exists():
        return

    try:
        data = json.loads(
            EXPANSION_CANDIDATES_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError:
        return

    candidates = data.get(
        "candidates",
        [],
    )

    if not isinstance(
        candidates,
        list,
    ):
        return

    updated = False

    for item in candidates:
        if not isinstance(
            item,
            dict,
        ):
            continue

        keyword = str(
            item.get(
                "target_keyword",
                "",
            )
        ).strip()

        if (
            keyword
            == target_keyword
            and item.get(
                "status"
            )
            == "ready"
        ):
            item[
                "status"
            ] = "used"

            item[
                "used_at"
            ] = datetime.now().isoformat()

            updated = True
            break

    if not updated:
        return

    EXPANSION_CANDIDATES_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

def refresh_content_expansion(
    log_file: Path,
) -> None:
    """Content Expansion関連データを再生成する。"""

    commands = [
        (
            "engines/content_expansion.py",
            [
                "-m",
                "engines.content_expansion",
            ],
        ),
        (
            "engines/content_expansion_queue.py",
            [
                "-m",
                "engines.content_expansion_queue",
            ],
        ),
        (
            "expansion.py",
            [
                "expansion.py",
            ],
        ),
        (
            "engines/expansion_candidates.py",
            [
                "-m",
                "engines.expansion_candidates",
            ],
        ),
    ]

    log(
        "Content Expansionを"
        "再計算します。",
        log_file,
    )

    for label, arguments in commands:
        log(
            "Content Expansion処理："
            f"{label}",
            log_file,
        )

        env = dict(
            os.environ
        )

        env[
            "PYTHONIOENCODING"
        ] = "utf-8"

        env[
            "PYTHONUTF8"
        ] = "1"

        result = subprocess.run(
            [
                sys.executable,
                *arguments,
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

        for line in result.stdout.splitlines():
            log(
                f"  {line}",
                log_file,
            )

        for line in result.stderr.splitlines():
            log(
                f"  [stderr] {line}",
                log_file,
            )

        if result.returncode != 0:
            raise RuntimeError(
                "Content Expansion更新に"
                "失敗しました："
                f"{label}"
            )

    log(
        "Content Expansion再計算完了。",
        log_file,
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
) -> Path:
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

    if target_keyword:
        input_text = (
            "1\n"
            f"{target_keyword}\n"
        )

        log(
            "AI編集長が選択したキーワードを"
            "main.pyへ渡します："
            f"{target_keyword}",
            log_file,
        )
    else:
        input_text = "2\n"

        log(
            "対象キーワードがないため、"
            "Keyword Queueを使用します。",
            log_file,
        )

    result = run_python_script(
        "main.py",
        log_file,
        input_text=input_text,
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

    if len(new_files) != 1:
        raise RuntimeError(
            "新規記事は1件だけ生成される想定です。"
            f"実際：{len(new_files)}件"
        )

    return next(
        iter(new_files)
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


def main(
    dry_run: bool = False,
) -> None:
    ensure_directories()

    remove_old_logs()

    log_file = create_log_file()

    action = ""

    rewritten_article_path: Path | None = None

    lock_acquired = False

    try:
        acquire_lock()

        lock_acquired = True
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

        update_seo_feedback(
            log_file
        )

        update_ga4_affiliate_clicks(
            log_file
        )

        update_revenue_summary(
            log_file
        )

        update_revenue_feedback(
            log_file
        )

        update_revenue_action_queue(
            log_file
        )

        update_domestic_asp_candidate_queue(
            log_file
        )

        update_portfolio_plan(
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
        # リライト実行可否確認
        # ----------------------------------------------------

        if action == "rewrite_article":
            portfolio_allowed = (
                decision.get(
                    "portfolio_allowed",
                    True,
                )
            )

            portfolio_reason = str(
                decision.get(
                    "portfolio_reason",
                    "",
                )
            ).strip()

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

            target_slug = str(
                decision.get(
                    "target_slug",
                    "",
                )
            ).strip()

            # ------------------------------------------------
            # Portfolio側で拒否された場合
            # ------------------------------------------------

            if portfolio_allowed is False:
                log(
                    "Portfolio Planで"
                    "実行が許可されていないため、"
                    "今回はリライトしません："
                    f"{target_slug}",
                    log_file,
                )

                if portfolio_reason:
                    log(
                        "Portfolio理由："
                        f"{portfolio_reason}",
                        log_file,
                    )

                # Portfolioによる拒否時は、
                # 新規記事へ切り替えず安全側で停止する
                action = "wait"

                decision[
                    "action"
                ] = "wait"

                reason = (
                    "Portfolio Planの"
                    "安全制御により記事変更を停止。 "
                    + portfolio_reason
                ).strip()

                decision[
                    "reason"
                ] = reason

            # ------------------------------------------------
            # Portfolioは許可しているが、
            # リライトCooldownで拒否された場合
            # ------------------------------------------------

            elif rewrite_allowed is False:
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

                expansion_candidate = (
                    load_top_expansion_candidate()
                )

                if expansion_candidate is not None:
                    action = "new_article"

                    decision[
                        "action"
                    ] = "new_article"

                    decision[
                        "target_keyword"
                    ] = str(
                        expansion_candidate.get(
                            "target_keyword",
                            "",
                        )
                    ).strip()

                    decision[
                        "target_title"
                    ] = str(
                        expansion_candidate.get(
                            "suggested_title",
                            "",
                        )
                    ).strip()

                    decision[
                        "target_slug"
                    ] = ""

                    decision[
                        "reason"
                    ] = (
                        "リライト対象が"
                        "クールダウン中のため、"
                        "記事拡張候補へ切り替え。 "
                        + str(
                            expansion_candidate.get(
                                "reason",
                                "",
                            )
                        ).strip()
                    )

                    decision[
                        "expansion_topic"
                    ] = str(
                        expansion_candidate.get(
                            "topic",
                            "",
                        )
                    ).strip()

                    decision[
                        "expansion_priority"
                    ] = int(
                        expansion_candidate.get(
                            "priority",
                            0,
                        )
                        or 0
                    )

                    decision[
                        "priority_score"
                    ] = int(
                        expansion_candidate.get(
                            "priority",
                            0,
                        )
                        or 0
                    )

                    log(
                        "新記事候補へ切り替えます："
                        f"{decision['target_keyword']}",
                        log_file,
                    )

                    priority_score = int(
                        decision.get(
                            "priority_score",
                            0,
                        )
                        or 0
                    )

                    reason = str(
                        decision.get(
                            "reason",
                            "",
                        )
                    )

                else:
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

        if dry_run:
            log(
                "DRY RUNのため、"
                "記事生成・リライト・"
                "GitHub Pushは実行しません。",
                log_file,
            )

            action = "wait"

            decision[
                "action"
            ] = "wait"

            decision[
                "reason"
            ] = (
                "Phase F DRY RUN。"
                "AI編集長判断までは実行し、"
                "コンテンツ変更は停止しました。"
            )

        if action == "new_article":
            new_article_path = (
                run_new_article(
                    decision,
                    log_file,
                )
            )

            expansion_topic = str(
                decision.get(
                    "expansion_topic",
                    "",
                )
            ).strip()

            if expansion_topic:
                target_keyword = str(
                    decision.get(
                        "target_keyword",
                        "",
                    )
                ).strip()

                mark_expansion_candidate_used(
                    target_keyword
                )

                record_expansion_used(
                    topic=expansion_topic,
                    target_keyword=target_keyword,
                    article_slug=(
                        new_article_path.stem
                    ),
                    article_title=str(
                        decision.get(
                            "target_title",
                            "",
                        )
                    ).strip(),
                )

                log(
                    "Expansion Historyへ"
                    "記録しました："
                    f"{expansion_topic}",
                    log_file,
                )

                refresh_content_expansion(
                    log_file
                )

                log(
                    "Expansion候補を"
                    "使用済みにしました："
                    f"{target_keyword}",
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

        # 最終状態を表示する前に
        # 実行中Lockを解除する
        if lock_acquired:
            release_lock()
            lock_acquired = False

        update_atlas_health(
            log_file
        )

        update_atlas_dashboard(
            log_file
        )

        update_daily_report(
            log_file
        )

        update_performance_history(
            log_file
        )

        update_performance_trend(
            log_file
        )

        optimization_decision_success = (
            update_optimization_decision(
                log_file
            )
        )

        if optimization_decision_success:
            safe_executor_success = (
                update_safe_executor(
                    log_file,
                    apply_mode=False,
                )
            )

            if safe_executor_success:
                optimization_history_success = (
                    update_optimization_history(
                        log_file
                    )
                )

                if optimization_history_success:
                    update_optimization_outcome(
                        log_file
                    )
                else:
                    log(
                        "Optimization History更新失敗のため、"
                        "Optimization Outcome更新を"
                        "スキップします。",
                        log_file,
                    )

            else:
                log(
                    "Safe Executor更新失敗のため、"
                    "Optimization History / Outcome更新を"
                    "スキップします。",
                    log_file,
                )

        else:
            log(
                "Optimization Decision更新失敗のため、"
                "Safe Executor / Optimization History / "
                "Outcome更新をスキップします。",
                log_file,
            )

        update_atlas_alert(
            log_file
        )

        log(
            "Atlas自動運転が完了しました。",
            log_file,
        )

    except Exception as error:
        # Lock取得前に失敗した場合は、
        # 別AtlasプロセスのLockや状態を変更しない
        if not lock_acquired:
            log(
                "Atlasを開始できませんでした："
                f"{error}",
                log_file,
            )

            raise

        save_latest_run(
            status="error",
            action=action,
            message=str(error),
        )

        release_lock()
        lock_acquired = False

        try:
            update_atlas_health(
                log_file
            )

            update_atlas_dashboard(
                log_file
            )

            update_daily_report(
                log_file
            )

            update_performance_history(
                log_file
            )

            update_performance_trend(
                log_file
            )

            optimization_decision_success = (
                update_optimization_decision(
                    log_file
                )
            )

            if optimization_decision_success:
                safe_executor_success = (
                    update_safe_executor(
                        log_file,
                        apply_mode=False,
                    )
                )

                if safe_executor_success:
                    optimization_history_success = (
                        update_optimization_history(
                            log_file
                        )
                    )

                    if optimization_history_success:
                        update_optimization_outcome(
                            log_file
                        )
                    else:
                        log(
                            "Optimization History更新失敗のため、"
                            "Optimization Outcome更新を"
                            "スキップします。",
                            log_file,
                        )

                else:
                    log(
                        "Safe Executor更新失敗のため、"
                        "Optimization History / Outcome更新を"
                        "スキップします。",
                        log_file,
                    )

            else:
                log(
                    "Optimization Decision更新失敗のため、"
                    "Safe Executor / Optimization History / "
                    "Outcome更新をスキップします。",
                    log_file,
                )

            update_atlas_alert(
                log_file
            )

        except Exception as status_error:
            log(
                "失敗後のHealth/Dashboard更新にも"
                "失敗しました："
                f"{status_error}",
                log_file,
            )

        log(
            "Atlas自動運転に失敗しました："
            f"{error}",
            log_file,
        )

        raise

    finally:
        if lock_acquired:
            release_lock()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Atlas自動運転を実行します。"
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "データ更新・AI編集長判断までは"
            "実行しますが、"
            "記事生成・リライト・"
            "GitHub Pushは行いません。"
        ),
    )

    args = parser.parse_args()

    main(
        dry_run=args.dry_run,
    )
