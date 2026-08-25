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

SOCIAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_queue.json"
)

SOCIAL_APPROVAL_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "social"
    / "social_approval_queue.json"
)

POPULAR_ARTICLES_FILE = (
    BASE_DIR.parent
    / "src"
    / "data"
    / "popular_articles.json"
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


def update_human_approval_queue(
    log_file: Path,
) -> bool:
    """Human Approval Queueを更新する。"""

    log(
        "Human Approval Queueを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.human_approval_queue",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Human Approval Queue更新成功。",
            log_file,
        )
        return True

    log(
        "Human Approval Queueの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_approved_action_router(
    log_file: Path,
) -> bool:
    """Approved Action Routerを更新する。"""

    log(
        "Approved Action Routerを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.approved_action_router",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Approved Action Router更新成功。",
            log_file,
        )
        return True

    log(
        "Approved Action Routerの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_approval_safety_guard(
    log_file: Path,
) -> bool:
    """Approval Safety Guardを更新する。"""

    log(
        "Approval Safety Guardを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.approval_safety_guard",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Approval Safety Guard更新成功。",
            log_file,
        )
        return True

    log(
        "Approval Safety Guardの"
        "更新に失敗しました。",
        log_file,
    )

    return False


def update_notification_engine(
    log_file: Path,
) -> bool:
    """Notification Engineを更新する。"""

    log(
        "Notification Engineを更新します。",
        log_file,
    )

    result = run_python_module(
        "engines.notification_engine",
        log_file,
    )

    if result.returncode == 0:
        log(
            "Notification Engine更新成功。",
            log_file,
        )
        return True

    log(
        "Notification Engineの"
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

    EDITORIAL_DECISION_FILE.parent.mkdir(parents=True, exist_ok=True)
    EDITORIAL_DECISION_FILE.write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

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

    artifact_dirs = (
        blog_dir,
        BASE_DIR.parent / "public" / "images" / "blog",
        BASE_DIR.parent / "public" / "images" / "social",
    )

    before_artifacts = {
        path.resolve()
        for directory in artifact_dirs
        for path in directory.glob("*")
        if path.is_file()
    }

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

    try:
        affiliate_service = str(decision.get("affiliate_service", "")).strip()
        if affiliate_service:
            from engines.a8_submission_export import validate_a8_service
            validate_a8_service(affiliate_service)
            log("公開前のアフィリエイト案件検査：OK", log_file)

        result = run_python_script(
            "main.py",
            log_file,
            input_text=input_text,
        )

        if result.returncode != 0:
            error_lines = [
                line.strip()
                for line in (result.stderr or "").splitlines()
                if line.strip()
            ]
            detail = error_lines[-1] if error_lines else "原因を取得できませんでした。"
            if "APITimeoutError" in detail or "timed out" in detail.lower():
                detail = "OpenAIのWeb調査が通信タイムアウトしました。少し時間を置いて再実行してください。"
            raise RuntimeError(f"main.pyが異常終了しました：{detail}")
    except Exception:
        after_artifacts = {
            path.resolve()
            for directory in artifact_dirs
            for path in directory.glob("*")
            if path.is_file()
        }
        from engines.social_record_cleanup import remove_article_records
        failed_slugs = {
            path.stem
            for path in after_artifacts - before_artifacts
            if path.parent == blog_dir.resolve() and path.suffix.lower() == ".mdx"
        }
        for failed_slug in failed_slugs:
            remove_article_records(failed_slug)
        removed = 0
        for path in sorted(after_artifacts - before_artifacts):
            path.unlink(missing_ok=True)
            removed += 1
        log(f"失敗時クリーンアップ：生成途中のファイルを{removed}件削除しました。", log_file)
        raise

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


def update_ga4_popular_articles(
    log_file: Path,
    publish: bool = True,
) -> None:
    """GA4の記事閲覧数ランキングを更新する。"""

    if not ATLAS_RUN_GA4_AFFILIATE:
        log("GA4人気記事ランキング更新：SKIP", log_file)
        return

    log("GA4人気記事ランキングを更新します。", log_file)
    result = run_python_script("ga4_popular_articles.py", log_file)
    if result.returncode != 0:
        if ATLAS_USE_CACHED_GA4_ON_ERROR and POPULAR_ARTICLES_FILE.exists():
            log("GA4人気記事ランキング取得に失敗しました。前回順位を維持します。", log_file)
            return
        raise RuntimeError("GA4人気記事ランキングの更新に失敗しました。")

    log("GA4人気記事ランキング更新成功。", log_file)
    if publish:
        publish_additional_files(
            paths=[POPULAR_ARTICLES_FILE],
            commit_prefix="Update GA4 popular articles",
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


def run_phase_c(
    article_path: Path,
    log_file: Path,
) -> None:
    """
    Phase Cを実行する。

    ・AIによる自然なタイトル改行
    ・Blog 16:9画像生成
    ・Instagram 4:5画像生成
    ・MDXのimage更新
    ・titleLines / cardTitleLines更新

    を対象記事へ反映する。
    """

    slug = article_path.stem

    log(
        "Phase Cを実行します："
        f"{slug}",
        log_file,
    )

    result = run_python_script(
        "generate_images.py",
        log_file,
        arguments=[
            slug,
        ],
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Phase Cの画像・タイトル生成に"
            "失敗しました："
            f"{slug}"
        )

    log(
        "Phase C完了："
        f"{slug}",
        log_file,
    )


def run_social_distribution(
    article_path: Path,
    log_file: Path,
    refresh: bool = False,
    auto_publish: bool = True,
) -> None:
    """
    記事のSNS配信候補を生成する。

    ・Social Distribution
    ・Social Copy Generator
    ・Social Approval Queue

    までを実行する。

    refresh=Trueの場合は、
    同一記事の未投稿SNS候補を
    最新記事内容で更新する。

    通常運転ではX・Instagramを自動承認し、
    Instagramの7秒リールも生成する。
    全記事更新などではauto_publish=Falseを指定する。
    """

    slug = article_path.stem

    log(
        "Social Distributionを開始します："
        f"{slug}",
        log_file,
    )

    # -----------------------------------------------------
    # 1. SNS配信候補生成
    # -----------------------------------------------------

    distribution_arguments = [
        slug,
    ]

    if refresh:
        distribution_arguments.append(
            "--refresh"
        )

    result = run_python_module(
        "engines.social_distribution",
        log_file,
        arguments=distribution_arguments,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Social Distributionに"
            "失敗しました："
            f"{slug}"
        )

    # -----------------------------------------------------
    # 2. SNS投稿文生成
    # -----------------------------------------------------

    result = run_python_module(
        "engines.social_copy_generator",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Social Copy Generatorに"
            "失敗しました："
            f"{slug}"
        )

    # -----------------------------------------------------
    # 3. Human Approval Queueへ追加
    # -----------------------------------------------------

    result = run_python_module(
        "engines.social_approval_queue",
        log_file,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Social Approval Queueに"
            "失敗しました："
            f"{slug}"
        )

    log(
        "SNS投稿候補を承認待ちへ"
        "追加しました："
        f"{slug}",
        log_file,
    )

    if not auto_publish:
        return

    result = run_python_module(
        "engines.social_auto_approver",
        log_file,
        arguments=[slug],
    )

    if result.returncode != 0:
        raise RuntimeError(
            "SNS投稿の自動承認に失敗しました："
            f"{slug}"
        )

    result = run_python_module(
        "engines.instagram_reel_generator",
        log_file,
        arguments=[slug],
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Instagramリール生成に"
            "失敗しました："
            f"{slug}"
        )

    log(
        "X・Instagram投稿を自動承認し、リールを生成しました："
        f"{slug}",
        log_file,
    )


def run_social_publishers(
    log_file: Path,
    article_slug: str = "",
) -> bool:
    """
    承認済みSNS投稿を配信する。

    ・Social Publish Routerでapprovedをready化
    ・X PublisherでXへ投稿
    ・Instagram PublisherでInstagramへ投稿
    ・Instagram Reel Publisherで7秒リールを投稿

    各Publisherは1回の実行につき
    最大1件だけ実投稿する。
    """

    log(
        "承認済みSNS投稿の配信処理を"
        "開始します。",
        log_file,
    )

    # 公開対象の記事について、配信直前にも承認Queueを同期して
    # 自動承認する。記事生成後に処理が中断しても、次の実行で
    # pendingのまま取り残さない。
    if article_slug:
        result = run_python_module(
            "engines.social_approval_queue",
            log_file,
        )
        if result.returncode != 0:
            log("SNS承認Queueの同期に失敗しました。", log_file)
            return False

        result = run_python_module(
            "engines.social_auto_approver",
            log_file,
            arguments=[article_slug],
        )
        if result.returncode != 0:
            log(f"SNS投稿の自動承認に失敗しました：{article_slug}", log_file)
            return False

    # -----------------------------------------------------
    # 1. approved → ready Route生成
    # -----------------------------------------------------

    result = run_python_module(
        "engines.social_publish_router",
        log_file,
        arguments=["--article-slug", article_slug],
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Social Publish Routerに"
            "失敗しました。"
        )

    publishers = (
        ("X", "engines.x_publisher", "Xへの投稿が完了しました。"),
        ("Instagram", "engines.instagram_publisher", "Instagramへの投稿が完了しました。"),
        (
            "Instagramリール",
            "engines.instagram_reel_publisher",
            "Instagramリールへの投稿が完了しました。",
        ),
    )
    delivery_results: dict[str, bool] = {}

    # 1媒体の失敗で残りの媒体を止めず、3種類をそれぞれ実行する。
    for label, module, success_message in publishers:
        result = run_python_module(
            module,
            log_file,
            arguments=["--apply", "--article-slug", article_slug],
        )
        succeeded = (
            result.returncode == 0
            and success_message in (result.stdout or "")
        )
        delivery_results[label] = succeeded
        if not succeeded:
            log(f"{label}への自動配信に失敗しました。次の媒体を続行します。", log_file)

    log(
        "承認済みSNS投稿の"
        "配信処理が完了しました。",
        log_file,
    )

    return all(delivery_results.values())


def run_refresh_all_articles() -> None:
    """
    既存の全MDX記事を現在のAlsivo仕様へ一括更新する。

    各記事について、

    1. rewrite
    2. Phase C
    3. SNS候補refresh
    4. SNS投稿文生成
    5. Social Approval Queue更新

    を実行する。

    全記事終了後に、

    ・internal_links更新
    ・GitHub Push

    を1回だけ実行する。

    通常のAtlas自動運転、
    AI編集長、
    Search Console更新、
    SNS実投稿処理は実行しない。
    """

    ensure_directories()

    remove_old_logs()

    log_file = create_log_file()

    lock_acquired = False

    successful: list[str] = []

    failed: list[
        tuple[
            str,
            str,
        ]
    ] = []

    blog_dir = (
        BASE_DIR.parent
        / "content"
        / "blog"
    )

    article_paths = sorted(
        path
        for path in blog_dir.glob(
            "*.mdx"
        )
        if path.is_file()
    )

    if not article_paths:
        raise RuntimeError(
            "一括更新対象のMDX記事がありません。"
        )

    total = len(
        article_paths
    )

    try:
        acquire_lock()

        lock_acquired = True

        log(
            "================================",
            log_file,
        )

        log(
            "Atlas全記事一括更新を開始します。",
            log_file,
        )

        log(
            f"対象記事数：{total}",
            log_file,
        )

        log(
            "SNS実投稿・AI編集長・"
            "Search Console更新は実行しません。",
            log_file,
        )

        log(
            "================================",
            log_file,
        )

        # =====================================================
        # 各記事を更新
        # =====================================================

        for index, article_path in enumerate(
            article_paths,
            start=1,
        ):
            slug = article_path.stem

            log(
                "--------------------------------",
                log_file,
            )

            log(
                f"[{index}/{total}] "
                f"更新開始：{slug}",
                log_file,
            )

            try:
                decision = {
                    "action":
                        "rewrite_article",
                    "priority_score":
                        100,
                    "reason":
                        (
                            "既存記事を現在の"
                            "Alsivo仕様へ一括更新"
                        ),
                    "target_keyword":
                        "",
                    "target_slug":
                        slug,
                    "target_title":
                        "",
                    "search_intent":
                        "",
                    "recommended_focus":
                        [],
                    "target_queries":
                        [],
                    "monetization_opportunity":
                        "",
                    "expected_effect":
                        "",
                }

                # ---------------------------------------------
                # 1. Rewrite
                # ---------------------------------------------

                rewritten_article_path = (
                    run_rewrite(
                        decision,
                        log_file,
                    )
                )

                # ---------------------------------------------
                # 2. Phase C
                #
                # Blog / Instagram画像
                # タイトル改行などを更新
                # ---------------------------------------------

                run_phase_c(
                    rewritten_article_path,
                    log_file,
                )

                # ---------------------------------------------
                # 3. SNS候補refresh
                # 4. SNS投稿文生成
                # 5. Approval Queue更新
                # ---------------------------------------------

                run_social_distribution(
                    rewritten_article_path,
                    log_file,
                    refresh=True,
                    auto_publish=False,
                )

                successful.append(
                    slug
                )

                log(
                    f"[OK] 更新完了：{slug}",
                    log_file,
                )

            except Exception as article_error:
                message = (
                    f"{type(article_error).__name__}: "
                    f"{article_error}"
                )

                failed.append(
                    (
                        slug,
                        message,
                    )
                )

                log(
                    f"[FAILED] {slug}",
                    log_file,
                )

                log(
                    message,
                    log_file,
                )

                log(
                    "次の記事へ進みます。",
                    log_file,
                )

        # =====================================================
        # Internal Links
        #
        # 全記事終了後に1回だけ再計算する
        # =====================================================

        log(
            "全記事処理後の"
            "AI関連記事更新を開始します。",
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
                "全記事更新後の"
                "AI関連記事更新に失敗しました。"
            )

        log(
            "AI関連記事更新完了。",
            log_file,
        )

        # =====================================================
        # GitHub Push
        #
        # 全変更を最後に1回だけPushする
        # =====================================================

        publish_paths: list[Path] = [
            INTERNAL_LINKS_FILE,
            SOCIAL_QUEUE_FILE,
            SOCIAL_APPROVAL_QUEUE_FILE,
        ]

        for article_path in article_paths:

            slug = article_path.stem

            # ---------------------------------------------
            # MDX
            # ---------------------------------------------

            if article_path.exists():
                publish_paths.append(
                    article_path
                )

            # ---------------------------------------------
            # Blog image
            # ---------------------------------------------

            blog_image_path = (
                BASE_DIR.parent
                / "public"
                / "images"
                / "blog"
                / f"{slug}.png"
            )

            if blog_image_path.exists():
                publish_paths.append(
                    blog_image_path
                )

            # ---------------------------------------------
            # Instagram image
            # ---------------------------------------------

            instagram_image_path = (
                BASE_DIR.parent
                / "public"
                / "images"
                / "social"
                / (
                    f"{slug}"
                    "-instagram.png"
                )
            )

            if instagram_image_path.exists():
                publish_paths.append(
                    instagram_image_path
                )

            instagram_reel_path = (
                BASE_DIR.parent
                / "public"
                / "images"
                / "social"
                / f"{slug}-instagram-reel.mp4"
            )

            if instagram_reel_path.exists():
                publish_paths.append(instagram_reel_path)

            for suffix in (".webp", ".png", ".jpg", ".jpeg"):
                background_path = (
                    BASE_DIR.parent / "public" / "images" / "article-backgrounds"
                    / f"{slug}{suffix}"
                )
                if background_path.exists():
                    publish_paths.append(background_path)
                    break

        # 同一Pathが複数入った場合に備えて重複除去
        publish_paths = list(
            dict.fromkeys(
                publish_paths
            )
        )

        log(
            "全記事更新結果を"
            "GitHubへ反映します。",
            log_file,
        )

        pushed = (
            publish_additional_files(
                paths=publish_paths,
                commit_prefix=(
                    "Refresh all Atlas articles"
                ),
            )
        )

        if pushed:
            log(
                "全記事更新の"
                "GitHub Push完了。",
                log_file,
            )
        else:
            log(
                "Git差分がないため、"
                "Pushをスキップしました。",
                log_file,
            )

        # =====================================================
        # Result
        # =====================================================

        log(
            "================================",
            log_file,
        )

        log(
            "Atlas全記事一括更新結果",
            log_file,
        )

        log(
            f"対象記事：{total}",
            log_file,
        )

        log(
            f"成功：{len(successful)}",
            log_file,
        )

        log(
            f"失敗：{len(failed)}",
            log_file,
        )

        if successful:
            log(
                "----- 成功 -----",
                log_file,
            )

            for slug in successful:
                log(
                    f"[OK] {slug}",
                    log_file,
                )

        if failed:
            log(
                "----- 失敗 -----",
                log_file,
            )

            for slug, message in failed:
                log(
                    f"[FAILED] {slug}",
                    log_file,
                )

                log(
                    f"         {message}",
                    log_file,
                )

        log(
            "================================",
            log_file,
        )

        if failed:
            log(
                "一部記事で失敗しましたが、"
                "一括更新処理は完了しました。",
                log_file,
            )
        else:
            log(
                "全記事の更新が"
                "正常に完了しました。",
                log_file,
            )

    finally:
        if lock_acquired:
            release_lock()


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
    force_new_article: bool = False,
    force_rewrite: str | None = None,
) -> None:
    ensure_directories()

    remove_old_logs()

    log_file = create_log_file()

    action = ""

    rewritten_article_path: Path | None = None
    new_article_path: Path | None = None
    new_article_published = False
    social_delivery_success = True

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

        # ----------------------------------------------------
        # 前回までに人間が承認したSNS投稿を配信
        #
        # 通常運転時のみ実投稿する。
        #
        # DRY RUN：
        #   実投稿しない。
        #
        # FORCE REWRITE：
        #   記事メンテナンスが目的なので、
        #   起動時のSNS実投稿は行わない。
        # ----------------------------------------------------

        if dry_run:
            log(
                "DRY RUNのため、"
                "SNS実投稿をスキップします。",
                log_file,
            )

        elif force_rewrite is not None:
            log(
                "FORCE REWRITEモードのため、"
                "起動時のSNS実投稿をスキップします。",
                log_file,
            )

        else:
            run_social_publishers(
                log_file
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

        update_ga4_popular_articles(
            log_file,
            publish=not dry_run,
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

        # ----------------------------------------------------
        # リライト強制テスト
        #
        # --force-rewrite <slug> 指定時のみ、
        # AI編集長の判断に関係なく
        # 指定記事をリライトする。
        #
        # 通常のTask Scheduler実行には影響しない。
        # ----------------------------------------------------

        if (
            force_rewrite
            and not dry_run
        ):
            target_path = (
                BASE_DIR.parent
                / "content"
                / "blog"
                / f"{force_rewrite}.mdx"
            )

            if not target_path.exists():
                raise FileNotFoundError(
                    "FORCE REWRITE対象の記事が"
                    "見つかりません："
                    f"{target_path}"
                )

            log(
                "FORCE REWRITEモード："
                "AI編集長判断を上書きして"
                "指定記事をリライトします："
                f"{force_rewrite}",
                log_file,
            )

            action = "rewrite_article"

            decision[
                "action"
            ] = "rewrite_article"

            decision[
                "target_slug"
            ] = force_rewrite

            decision[
                "priority_score"
            ] = 100

            decision[
                "reason"
            ] = (
                "Phase C本番テストのため"
                "指定記事を強制リライト。"
            )

            priority_score = 100

            reason = str(
                decision["reason"]
            )

        # ----------------------------------------------------
        # 新規記事強制テスト
        #
        # --force-new-article 指定時のみ、
        # AI編集長の判断に関係なく
        # 新規記事を1件生成する。
        #
        # 通常のTask Scheduler実行には影響しない。
        # ----------------------------------------------------

        if (
            force_new_article
            and not dry_run
        ):
            log(
                "FORCE NEW ARTICLEモード："
                "AI編集長判断を上書きして"
                "新規記事を1件生成します。",
                log_file,
            )

            affiliate_service = str(
                decision.get("affiliate_service", "")
            ).strip()
            expansion_candidate = (
                None
                if affiliate_service
                else load_top_expansion_candidate()
            )

            action = "new_article"

            decision[
                "action"
            ] = "new_article"

            # ---------------------------------------------
            # Expansion候補がある場合は最優先候補を使う
            # ---------------------------------------------

            if expansion_candidate is not None:

                target_keyword = str(
                    expansion_candidate.get(
                        "target_keyword",
                        "",
                    )
                ).strip()

                target_title = str(
                    expansion_candidate.get(
                        "suggested_title",
                        "",
                    )
                ).strip()

                expansion_topic = str(
                    expansion_candidate.get(
                        "topic",
                        "",
                    )
                ).strip()

                expansion_priority = int(
                    expansion_candidate.get(
                        "priority",
                        0,
                    )
                    or 0
                )

                decision[
                    "target_keyword"
                ] = target_keyword

                decision[
                    "target_title"
                ] = target_title

                decision[
                    "target_slug"
                ] = ""

                decision[
                    "expansion_topic"
                ] = expansion_topic

                decision[
                    "expansion_priority"
                ] = expansion_priority

                decision[
                    "priority_score"
                ] = expansion_priority

                decision[
                    "reason"
                ] = (
                    "Phase C本番テストのため"
                    "新規記事を強制生成。 "
                    + str(
                        expansion_candidate.get(
                            "reason",
                            "",
                        )
                    ).strip()
                )

                log(
                    "FORCE NEW ARTICLE候補："
                    f"{target_keyword}",
                    log_file,
                )

            # ---------------------------------------------
            # Expansion候補がなければ
            # main.pyのKeyword Queueに任せる
            # ---------------------------------------------

            elif not affiliate_service:

                decision[
                    "target_keyword"
                ] = ""

                decision[
                    "target_title"
                ] = ""

                decision[
                    "target_slug"
                ] = ""

                decision[
                    "expansion_topic"
                ] = ""

                decision[
                    "priority_score"
                ] = 100

                decision[
                    "reason"
                ] = (
                    "Phase C本番テストのため"
                    "Keyword Queueから"
                    "新規記事を強制生成。"
                )

                log(
                    "Expansion候補がないため、"
                    "Keyword Queueを使用します。",
                    log_file,
                )

            else:
                log(
                    "登録済みアフィリエイト案件を優先します："
                    f"{affiliate_service}",
                    log_file,
                )

            priority_score = int(
                decision.get(
                    "priority_score",
                    100,
                )
                or 100
            )

            reason = str(
                decision.get(
                    "reason",
                    "",
                )
            )

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

            run_phase_c(
                new_article_path,
                log_file,
            )

            run_social_distribution(
                new_article_path,
                log_file,
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

            run_phase_c(
                rewritten_article_path,
                log_file,
            )

            run_social_distribution(
                rewritten_article_path,
                log_file,
                refresh=True,
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
                action == "new_article"
                and new_article_path
                is not None
            ):
                publish_paths.append(
                    new_article_path
                )

                blog_image_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "blog"
                    / f"{new_article_path.stem}.png"
                )

                if blog_image_path.exists():
                    publish_paths.append(
                        blog_image_path
                    )

                instagram_image_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "social"
                    / (
                        f"{new_article_path.stem}"
                        "-instagram.png"
                    )
                )

                if instagram_image_path.exists():
                    publish_paths.append(
                        instagram_image_path
                    )

                instagram_reel_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "social"
                    / f"{new_article_path.stem}-instagram-reel.mp4"
                )

                if instagram_reel_path.exists():
                    publish_paths.append(instagram_reel_path)

                for suffix in (".webp", ".png", ".jpg", ".jpeg"):
                    background_path = (
                        BASE_DIR.parent / "public" / "images" / "article-backgrounds"
                        / f"{new_article_path.stem}{suffix}"
                    )
                    if background_path.exists():
                        publish_paths.append(background_path)
                        break

            elif (
                action == "rewrite_article"
                and rewritten_article_path
                is not None
            ):
                publish_paths.append(
                    rewritten_article_path
                )

                blog_image_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "blog"
                    / f"{rewritten_article_path.stem}.png"
                )

                if blog_image_path.exists():
                    publish_paths.append(
                        blog_image_path
                    )

                instagram_image_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "social"
                    / f"{rewritten_article_path.stem}-instagram.png"
                )
                instagram_reel_path = (
                    BASE_DIR.parent
                    / "public"
                    / "images"
                    / "social"
                    / f"{rewritten_article_path.stem}-instagram-reel.mp4"
                )
                for social_path in (instagram_image_path, instagram_reel_path):
                    if social_path.exists():
                        publish_paths.append(social_path)

                for suffix in (".webp", ".png", ".jpg", ".jpeg"):
                    background_path = (
                        BASE_DIR.parent / "public" / "images" / "article-backgrounds"
                        / f"{rewritten_article_path.stem}{suffix}"
                    )
                    if background_path.exists():
                        publish_paths.append(background_path)
                        break

            pushed = (
                publish_additional_files(
                    paths=publish_paths,
                    commit_prefix=(
                        "Update Atlas content"
                    ),
                )
            )

            if action == "new_article":
                # ここ以降はGitHubへ反映済みなので、後工程の失敗では削除しない。
                new_article_published = True

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

            published_article_path = (
                new_article_path
                if action == "new_article"
                else rewritten_article_path
            )

            if published_article_path is not None:
                deploy_result = run_python_module(
                    "engines.publication_waiter",
                    log_file,
                    arguments=[published_article_path.stem],
                )

                if deploy_result.returncode == 0:
                    social_delivery_success = run_social_publishers(
                        log_file,
                        published_article_path.stem,
                    )
                    if not social_delivery_success:
                        log(
                            "記事公開は成功しましたが、SNS配信に失敗しました。",
                            log_file,
                        )
                else:
                    log(
                        "本番反映待ちのため、SNS配信を"
                        "次回自動運転へ繰り越しました。",
                        log_file,
                    )

        save_latest_run(
            status="success" if social_delivery_success else "warning",
            action=action,
            message=(
                "Atlas自動運転完了"
                if social_delivery_success
                else "記事公開は完了しましたが、SNS配信に失敗しました。"
            ),
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
            approval_queue_success = (
                update_human_approval_queue(
                    log_file
                )
            )

            if not approval_queue_success:
                log(
                    "Human Approval Queue更新失敗。"
                    "承認系処理は安全側で継続します。",
                    log_file,
                )

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

            router_success = (
                update_approved_action_router(
                    log_file
                )
            )

            if router_success:
                update_approval_safety_guard(
                    log_file
                )
            else:
                log(
                    "Approved Action Router更新失敗のため、"
                    "Approval Safety Guard更新を"
                    "スキップします。",
                    log_file,
                )

        else:
            log(
                "Optimization Decision更新失敗のため、"
                "Safe Executor / Human Approval / "
                "Optimization History / Outcome / "
                "Approved Action Router / "
                "Approval Safety Guard更新を"
                "スキップします。",
                log_file,
            )

        update_atlas_alert(
            log_file
        )

        update_notification_engine(
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

        if (
            action == "new_article"
            and new_article_path is not None
            and not new_article_published
        ):
            cleanup_targets = (
                new_article_path,
                BASE_DIR.parent / "public" / "images" / "blog" / f"{new_article_path.stem}.png",
                BASE_DIR.parent / "public" / "images" / "blog" / f"{new_article_path.stem}.webp",
                BASE_DIR.parent / "public" / "images" / "social" / f"{new_article_path.stem}-instagram.png",
                BASE_DIR.parent / "public" / "images" / "social" / f"{new_article_path.stem}-instagram-reel.mp4",
                BASE_DIR.parent / "public" / "images" / "article-backgrounds" / f"{new_article_path.stem}.png",
                BASE_DIR.parent / "public" / "images" / "article-backgrounds" / f"{new_article_path.stem}.webp",
                BASE_DIR.parent / "public" / "images" / "article-backgrounds" / f"{new_article_path.stem}.jpg",
                BASE_DIR.parent / "public" / "images" / "article-backgrounds" / f"{new_article_path.stem}.jpeg",
            )
            removed = 0
            for path in cleanup_targets:
                if path.exists():
                    path.unlink()
                    removed += 1
            from engines.social_record_cleanup import remove_article_records
            social_removed = remove_article_records(new_article_path.stem)
            log(f"失敗時クリーンアップ：生成途中のファイルを{removed}件削除しました。", log_file)
            log(f"失敗時クリーンアップ：SNS記録を{social_removed}件削除しました。", log_file)
            try:
                from engines.a8_submission_export import export_a8_submission_csv
                export_a8_submission_csv()
            except Exception as cleanup_error:
                log(f"A8.net提出用CSVの復元に失敗しました：{cleanup_error}", log_file)

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
                approval_queue_success = (
                    update_human_approval_queue(
                        log_file
                    )
                )

                if not approval_queue_success:
                    log(
                        "Human Approval Queue更新失敗。"
                        "承認系処理は安全側で継続します。",
                        log_file,
                    )

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

                router_success = (
                    update_approved_action_router(
                        log_file
                    )
                )

                if router_success:
                    update_approval_safety_guard(
                        log_file
                    )
                else:
                    log(
                        "Approved Action Router更新失敗のため、"
                        "Approval Safety Guard更新を"
                        "スキップします。",
                        log_file,
                    )

            else:
                log(
                    "Optimization Decision更新失敗のため、"
                    "Safe Executor / Human Approval / "
                    "Optimization History / Outcome / "
                    "Approved Action Router / "
                    "Approval Safety Guard更新を"
                    "スキップします。",
                    log_file,
                )

            update_atlas_alert(
                log_file
            )

            update_notification_engine(
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

    parser.add_argument(
        "--force-new-article",
        action="store_true",
        help=(
            "テスト用。"
            "AI編集長の判断に関係なく"
            "新規記事を1件生成し、"
            "Phase Cを含む公開フローを"
            "本番経路で実行します。"
        ),
    )

    parser.add_argument(
        "--force-rewrite",
        type=str,
        default=None,
        metavar="SLUG",
        help=(
            "テスト用。"
            "指定した既存記事を強制リライトし、"
            "Phase Cを含む公開フローを"
            "本番経路で実行します。"
        ),
    )

    parser.add_argument(
        "--refresh-all-articles",
        action="store_true",
        help=(
            "既存の全MDX記事を"
            "現在のAlsivo仕様へ一括更新します。"
            "Rewrite、Phase C、"
            "SNS候補更新まで実行し、"
            "最後にまとめてGitHubへPushします。"
            "SNS実投稿は行いません。"
        ),
    )

    args = parser.parse_args()

    if args.refresh_all_articles:
        run_refresh_all_articles()
        sys.exit(0)

    main(
        dry_run=args.dry_run,
        force_new_article=(
            args.force_new_article
        ),
        force_rewrite=(
            args.force_rewrite
        ),
    )
