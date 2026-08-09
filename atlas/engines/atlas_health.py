import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

AUTOMATION_DIR = (
    BASE_DIR
    / "data"
    / "automation"
)

LATEST_RUN_FILE = (
    AUTOMATION_DIR
    / "latest_run.json"
)

HEALTH_STATUS_FILE = (
    AUTOMATION_DIR
    / "health_status.json"
)

HEALTH_ALERT_DIR = (
    BASE_DIR
    / "logs"
    / "health"
)

# 36時間以上Atlasが正常実行されていなければ警告
MAX_RUN_AGE_HOURS = 36


def load_latest_run(
) -> dict[str, Any]:
    """Atlasの最新実行結果を読み込む。"""

    if not LATEST_RUN_FILE.exists():
        return {}

    try:
        data = json.loads(
            LATEST_RUN_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "latest_run.jsonの"
            "JSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "latest_run.jsonの最上位は"
            "オブジェクトにしてください。"
        )

    return data

def evaluate_health(
    latest_run: dict[str, Any],
) -> dict[str, Any]:
    """Atlasの健康状態を判定する。"""

    checked_at = datetime.now()

    if not latest_run:
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "error",
            "reason":
                "latest_run.jsonが存在しません。",
            "last_run":
                None,
            "last_status":
                None,
            "last_action":
                None,
            "age_hours":
                None,
        }

    finished_at_text = str(
        latest_run.get(
            "finished_at",
            "",
        )
    ).strip()

    status = str(
        latest_run.get(
            "status",
            "",
        )
    ).strip()

    action = str(
        latest_run.get(
            "action",
            "",
        )
    ).strip()

    message = str(
        latest_run.get(
            "message",
            "",
        )
    ).strip()

    if not finished_at_text:
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "error",
            "reason":
                "finished_atがありません。",
            "last_run":
                None,
            "last_status":
                status,
            "last_action":
                action,
            "age_hours":
                None,
        }

    try:
        finished_at = (
            datetime.fromisoformat(
                finished_at_text
            )
        )
    except ValueError:
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "error",
            "reason":
                "finished_atの日時形式が不正です。",
            "last_run":
                finished_at_text,
            "last_status":
                status,
            "last_action":
                action,
            "age_hours":
                None,
        }

    age = (
        checked_at
        - finished_at
    )

    age_hours = (
        age.total_seconds()
        / 3600
    )

    # 前回実行そのものが失敗
    if status == "error":
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "error",
            "reason":
                (
                    "Atlasの前回実行が"
                    "エラー終了しています。"
                ),
            "last_run":
                finished_at_text,
            "last_status":
                status,
            "last_action":
                action,
            "last_message":
                message,
            "age_hours":
                round(
                    age_hours,
                    2,
                ),
        }

    # 毎日実行のはずなのに長時間更新されていない
    if age > timedelta(
        hours=MAX_RUN_AGE_HOURS
    ):
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "warning",
            "reason":
                (
                    "Atlasの最新実行から"
                    f"{MAX_RUN_AGE_HOURS}時間以上"
                    "経過しています。"
                ),
            "last_run":
                finished_at_text,
            "last_status":
                status,
            "last_action":
                action,
            "last_message":
                message,
            "age_hours":
                round(
                    age_hours,
                    2,
                ),
        }

    if status != "success":
        return {
            "checked_at":
                checked_at.isoformat(),
            "health":
                "warning",
            "reason":
                (
                    "Atlasの実行状態が"
                    "successではありません。"
                ),
            "last_run":
                finished_at_text,
            "last_status":
                status,
            "last_action":
                action,
            "last_message":
                message,
            "age_hours":
                round(
                    age_hours,
                    2,
                ),
        }

    return {
        "checked_at":
            checked_at.isoformat(),
        "health":
            "healthy",
        "reason":
            "Atlasは正常に稼働しています。",
        "last_run":
            finished_at_text,
        "last_status":
            status,
        "last_action":
            action,
        "last_message":
            message,
        "age_hours":
            round(
                age_hours,
                2,
            ),
    }

def save_health_status(
    health: dict[str, Any],
) -> Path:
    """Atlasの健康状態を保存する。"""

    AUTOMATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    HEALTH_STATUS_FILE.write_text(
        json.dumps(
            health,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return HEALTH_STATUS_FILE

def save_health_alert(
    health: dict[str, Any],
) -> Path | None:
    """warning/error時だけ専用ログを保存する。"""

    if health.get(
        "health"
    ) == "healthy":
        return None

    HEALTH_ALERT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    alert_file = (
        HEALTH_ALERT_DIR
        / f"{timestamp}.json"
    )

    alert_file.write_text(
        json.dumps(
            health,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return alert_file

def print_health_status(
    health: dict[str, Any],
) -> None:
    """Atlasの健康状態を表示する。"""

    print(
        "\n===== Atlas Health Check =====\n"
    )

    print(
        "状態："
        f"{health['health']}"
    )

    print(
        "理由："
        f"{health['reason']}"
    )

    print(
        "前回実行："
        f"{health.get('last_run')}"
    )

    print(
        "前回Action："
        f"{health.get('last_action')}"
    )

    age_hours = health.get(
        "age_hours"
    )

    if age_hours is not None:
        print(
            "経過時間："
            f"{age_hours}時間"
        )

    print()

def main() -> None:
    latest_run = (
        load_latest_run()
    )

    health = (
        evaluate_health(
            latest_run
        )
    )

    filepath = (
        save_health_status(
            health
        )
    )

    alert_filepath = (
        save_health_alert(
            health
        )
    )

    print_health_status(
        health
    )

    print(
        f"保存先：{filepath}"
    )

    if alert_filepath is not None:
        print(
            "異常ログ："
            f"{alert_filepath}"
        )

    if health["health"] == "error":
        sys.exit(1)

    if health["health"] == "warning":
        sys.exit(2)

if __name__ == "__main__":
    main()