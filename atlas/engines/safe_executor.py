import json
from datetime import datetime
from pathlib import Path
from typing import Any
import subprocess
import sys
from engines.title_optimizer import (
    optimize_article_title,
    save_result as save_title_result,
)
from engines.content_strengthener import (
    strengthen_existing_article,
    save_result as save_strengthen_result,
)

BASE_DIR = Path(__file__).resolve().parents[1]

REWRITE_SCRIPT = (
    BASE_DIR
    / "rewrite.py"
)

OPTIMIZATION_DECISION_FILE = (
    BASE_DIR
    / "data"
    / "optimization"
    / "optimization_decision.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "safe_execution"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "execution_plan.json"
)

EXECUTION_RESULT_FILE = (
    OUTPUT_DIR
    / "execution_result.json"
)

ALLOWED_AUTO_ACTIONS = {
    "TITLE_ONLY",
    "STRENGTHEN",
    "REWRITE",
}


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONを安全に読み込む。"""

    if not filepath.exists():
        return {}

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "JSON形式が不正です："
            f"{filepath}"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "JSONの最上位は"
            "オブジェクトにしてください。"
        )

    return data


def build_skip_plan(
    reason: str,
) -> dict[str, Any]:
    """自動実行しない場合のPlanを作る。"""

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status":
            "skip",
        "execution_allowed":
            False,
        "action":
            "WAIT",
        "target":
            "",
        "reason":
            reason,
        "next_executor":
            "",
    }


def build_execution_plan(
    decision: dict[str, Any],
) -> dict[str, Any]:
    """Optimization Decisionを再検証する。"""

    candidate = decision.get(
        "safe_execution_candidate"
    )

    if not isinstance(
        candidate,
        dict,
    ):
        return build_skip_plan(
            "safe_execution_candidateがありません。"
        )

    action = str(
        candidate.get(
            "action",
            "",
        )
    ).strip()

    target = str(
        candidate.get(
            "target",
            "",
        )
    ).strip()

    execution_mode = str(
        candidate.get(
            "execution_mode",
            "",
        )
    ).strip()

    execution_allowed = bool(
        candidate.get(
            "execution_allowed",
            False,
        )
    )

    if action not in ALLOWED_AUTO_ACTIONS:
        return build_skip_plan(
            "自動実行対象外のactionです："
            f"{action}"
        )

    if execution_mode != "auto_candidate":
        return build_skip_plan(
            "execution_modeが"
            "auto_candidateではありません。"
        )

    if not execution_allowed:
        return build_skip_plan(
            "Optimization Decision側で"
            "execution_allowed=Falseです。"
        )

    if not target:
        return build_skip_plan(
            "対象記事slugがありません。"
        )

    if action == "TITLE_ONLY":
        next_executor = (
            "title_optimizer"
        )

    elif action == "STRENGTHEN":
        next_executor = (
            "content_strengthener"
        )

    elif action == "REWRITE":
        next_executor = (
            "rewrite"
        )

    else:
        return build_skip_plan(
            "対応Executorがありません。"
        )

    return {
        "generated_at":
            datetime.now().isoformat(),
        "status":
            "ready",
        "execution_allowed":
            True,
        "action":
            action,
        "target":
            target,
        "priority":
            int(
                candidate.get(
                    "priority",
                    0,
                )
                or 0
            ),
        "reason":
            str(
                candidate.get(
                    "reason",
                    "",
                )
            ).strip(),
        "next_executor":
            next_executor,
        "source":
            str(
                candidate.get(
                    "source",
                    "",
                )
            ).strip(),
        "trend_state":
            str(
                candidate.get(
                    "trend_state",
                    decision.get(
                        "trend_state",
                        "",
                    ),
                )
            ).strip(),
    }


def save_execution_plan(
    plan: dict[str, Any],
) -> Path:
    """Execution Planを保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            plan,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return OUTPUT_FILE


def save_execution_result(
    result: dict[str, Any],
) -> Path:
    """Safe Executorの実行結果を保存する。"""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "saved_at":
            datetime.now().isoformat(),
        **result,
    }

    EXECUTION_RESULT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return EXECUTION_RESULT_FILE


def execute_plan(
    plan: dict[str, Any],
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execution Planに従って安全に処理を実行する。"""

    if (
        plan.get(
            "status"
        )
        != "ready"
    ):
        return {
            "status":
                "skip",
            "executed":
                False,
            "dry_run":
                dry_run,
            "action":
                str(
                    plan.get(
                        "action",
                        "WAIT",
                    )
                ),
            "target":
                str(
                    plan.get(
                        "target",
                        "",
                    )
                ),
            "reason":
                str(
                    plan.get(
                        "reason",
                        "",
                    )
                ),
        }

    if not bool(
        plan.get(
            "execution_allowed",
            False,
        )
    ):
        return {
            "status":
                "skip",
            "executed":
                False,
            "dry_run":
                dry_run,
            "action":
                str(
                    plan.get(
                        "action",
                        "",
                    )
                ),
            "target":
                str(
                    plan.get(
                        "target",
                        "",
                    )
                ),
            "reason":
                (
                    "Execution Planで"
                    "execution_allowed=Falseです。"
                ),
        }

    action = str(
        plan.get(
            "action",
            "",
        )
    ).strip()

    target = str(
        plan.get(
            "target",
            "",
        )
    ).strip()

    next_executor = str(
        plan.get(
            "next_executor",
            "",
        )
    ).strip()

    expected_executor_map = {
        "TITLE_ONLY":
            "title_optimizer",
        "STRENGTHEN":
            "content_strengthener",
        "REWRITE":
            "rewrite",
    }

    expected_executor = (
        expected_executor_map.get(
            action
        )
    )

    if expected_executor is None:
        return {
            "status":
                "skip",
            "executed":
                False,
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                target,
            "reason":
                (
                    "Safe Executorで許可されていない"
                    f"actionです：{action}"
                ),
        }

    if (
        next_executor
        != expected_executor
    ):
        return {
            "status":
                "skip",
            "executed":
                False,
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                target,
            "reason":
                (
                    "next_executorが"
                    "actionと一致しません。"
                    f" expected={expected_executor}"
                    f" actual={next_executor}"
                ),
        }

    if not target:
        return {
            "status":
                "skip",
            "executed":
                False,
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                "",
            "reason":
                "対象slugがありません。",
        }

    if action == "TITLE_ONLY":
        result = (
            optimize_article_title(
                slug=target,
                dry_run=dry_run,
            )
        )

        save_title_result(
            result
        )

        return {
            "status":
                result.get(
                    "status",
                    "",
                ),
            "executed":
                bool(
                    result.get(
                        "changed",
                        False,
                    )
                ),
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                target,
            "result":
                result,
        }

    if action == "STRENGTHEN":
        result = (
            strengthen_existing_article(
                slug=target,
                reason=str(
                    plan.get(
                        "reason",
                        "",
                    )
                ).strip(),
                dry_run=dry_run,
            )
        )

        save_strengthen_result(
            result
        )

        return {
            "status":
                result.get(
                    "status",
                    "",
                ),
            "executed":
                bool(
                    result.get(
                        "changed",
                        False,
                    )
                ),
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                target,
            "result":
                result,
        }

    if action == "REWRITE":
        command = [
            sys.executable,
            str(
                REWRITE_SCRIPT
            ),
            target,
        ]

        if dry_run:
            command.append(
                "--dry-run"
            )

        completed = (
            subprocess.run(
                command,
                cwd=BASE_DIR,
                check=False,
            )
        )

        if completed.returncode != 0:
            return {
                "status":
                    "failed",
                "executed":
                    False,
                "dry_run":
                    dry_run,
                "action":
                    action,
                "target":
                    target,
                "returncode":
                    completed.returncode,
                "reason":
                    (
                        "rewrite.pyが"
                        "異常終了しました。"
                    ),
            }
        return {
            "status":
                (
                    "dry_run"
                    if dry_run
                    else "updated"
                ),
            "executed":
                not dry_run,
            "dry_run":
                dry_run,
            "action":
                action,
            "target":
                target,
            "returncode":
                completed.returncode,
            "reason":
                (
                    "REWRITE Dry Run完了"
                    if dry_run
                    else "REWRITE実行完了"
                ),
        }

    return {
        "status":
            "skip",
        "executed":
            False,
        "dry_run":
            dry_run,
        "action":
            action,
        "target":
            target,
        "reason":
            (
                "対応していない"
                f"actionです：{action}"
            ),
    }


def print_execution_plan(
    plan: dict[str, Any],
) -> None:
    """Execution Planを表示する。"""

    print(
        "\n===== Atlas Safe Executor =====\n"
    )

    print(
        "Status："
        f"{plan.get('status', '')}"
    )

    print(
        "Execution Allowed："
        + (
            "YES"
            if plan.get(
                "execution_allowed"
            )
            else "NO"
        )
    )

    print(
        "Action："
        f"{plan.get('action', '')}"
    )

    print(
        "Target："
        f"{plan.get('target', '')}"
    )

    if plan.get(
        "next_executor"
    ):
        print(
            "Next Executor："
            f"{plan.get('next_executor', '')}"
        )

    print(
        "Reason："
        f"{plan.get('reason', '')}"
    )

    print()


def main() -> None:
    """Safe Execution Planを生成して実行する。"""

    decision = load_json(
        OPTIMIZATION_DECISION_FILE
    )

    plan = build_execution_plan(
        decision
    )

    filepath = save_execution_plan(
        plan
    )

    print_execution_plan(
        plan
    )

    print(
        f"保存先：{filepath}"
    )

    apply_mode = (
        "--apply"
        in sys.argv[1:]
    )

    execution_result = (
        execute_plan(
            plan,
            dry_run=not apply_mode,
        )
    )

    execution_result_path = (
        save_execution_result(
            execution_result
        )
    )

    print(
        "\nEXECUTION"
    )

    print(
        "Status："
        f"{execution_result.get('status', '')}"
    )

    print(
        "Executed："
        + (
            "YES"
            if execution_result.get(
                "executed"
            )
            else "NO"
        )
    )

    if not apply_mode:
        print(
            "Mode：DRY RUN"
        )
    else:
        print(
            "Mode：APPLY"
        )

    print(
        "実行結果保存先："
        f"{execution_result_path}"
    )


if __name__ == "__main__":
    main()