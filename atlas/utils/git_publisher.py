import subprocess
from datetime import datetime
from pathlib import Path

from config import (
    AUTO_GIT_PUSH,
    GIT_REMOTE,
)


WEBSITE_ROOT = Path(__file__).resolve().parents[2]


def run_git_command(
    arguments: list[str],
) -> str:
    """websiteリポジトリ内でGitコマンドを実行する。"""

    command = ["git", *arguments]

    result = subprocess.run(
        command,
        cwd=WEBSITE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "原因不明のGitエラー"
        )

        raise RuntimeError(
            f"Gitコマンドに失敗しました。\n"
            f"コマンド：{' '.join(command)}\n"
            f"内容：{error_message}"
        )

    return result.stdout.strip()


def get_repository_root() -> Path:
    """現在のGitリポジトリのルートを確認する。"""

    output = run_git_command(
        ["rev-parse", "--show-toplevel"]
    )

    repository_root = Path(output).resolve()

    if repository_root != WEBSITE_ROOT.resolve():
        raise RuntimeError(
            "想定外のGitリポジトリです。\n"
            f"想定：{WEBSITE_ROOT}\n"
            f"実際：{repository_root}"
        )

    return repository_root

def get_current_branch() -> str:
    """現在チェックアウト中のGitブランチ名を取得する。"""

    branch = run_git_command(
        ["branch", "--show-current"]
    ).strip()

    if not branch:
        raise RuntimeError(
            "現在のGitブランチを取得できませんでした。"
        )

    return branch

def get_relative_path(path: Path) -> str:
    """絶対パスをGitで使う相対パスへ変換する。"""

    resolved_path = path.resolve()

    try:
        relative_path = resolved_path.relative_to(
            WEBSITE_ROOT.resolve()
        )
    except ValueError as error:
        raise ValueError(
            "Gitへ追加できるのはwebsite内のファイルだけです。"
            f"\n対象：{resolved_path}"
        ) from error

    return relative_path.as_posix()


def has_staged_changes() -> bool:
    """ステージ済みの変更があるか確認する。"""

    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=WEBSITE_ROOT,
        check=False,
    )

    if result.returncode == 0:
        return False

    if result.returncode == 1:
        return True

    raise RuntimeError(
        "ステージ済み変更の確認に失敗しました。"
    )


def publish_generated_files(
    article_path: Path,
    image_path: Path,
    state_path: Path | None = None,
) -> bool:
    """
    Atlasが生成したファイルだけをCommit・Pushする。

    AUTO_GIT_PUSH=Falseの場合は何も変更しない。
    """

    if not AUTO_GIT_PUSH:
        print(
            "[Git Publisher] AUTO_GIT_PUSH=Falseのため、"
            "Commit・Pushをスキップしました。"
        )
        return False

    get_repository_root()

    target_paths = [
        article_path,
        image_path,
    ]

    if state_path is not None:
        target_paths.append(state_path)

    relative_paths = [
        get_relative_path(path)
        for path in target_paths
    ]

    print("[Git Publisher] 生成ファイルをステージします。")

    run_git_command(
        ["add", "--", *relative_paths]
    )

    if not has_staged_changes():
        print(
            "[Git Publisher] Commit対象の変更がありません。"
        )
        return False

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )

    commit_message = (
        f"Publish Atlas article: {timestamp}"
    )

    print(
        f"[Git Publisher] Commit：{commit_message}"
    )

    run_git_command(
        ["commit", "-m", commit_message]
    )

    current_branch = get_current_branch()

    print(
        f"[Git Publisher] "
        f"{GIT_REMOTE}/{current_branch}へPushします。"
    )

    run_git_command(
        [
            "push",
            GIT_REMOTE,
            current_branch,
        ]
    )

    print("[Git Publisher] Push完了！")

    return True