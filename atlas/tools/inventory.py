import argparse
import ast
import json
from datetime import datetime
from pathlib import Path
from typing import Any


EXCLUDED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".next",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}


def should_exclude(path: Path) -> bool:
    """
    仮想環境やGit、ビルド成果物など、
    棚卸しに不要なフォルダを除外する。
    """

    return any(part in EXCLUDED_DIRECTORIES for part in path.parts)


def read_python_metadata(file_path: Path) -> dict[str, Any]:
    """
    Pythonファイルを解析し、import、関数、クラスを取得する。

    ファイルは実行せず、ASTによる静的解析のみを行う。
    """

    metadata: dict[str, Any] = {
        "imports": [],
        "functions": [],
        "classes": [],
        "parse_error": None,
    }

    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            source = file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as error:
            metadata["parse_error"] = f"文字コードを読み取れませんでした: {error}"
            return metadata
    except OSError as error:
        metadata["parse_error"] = f"ファイルを読み取れませんでした: {error}"
        return metadata

    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        metadata["parse_error"] = (
            f"構文解析に失敗しました: "
            f"line={error.lineno}, message={error.msg}"
        )
        return metadata

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                metadata["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            for alias in node.names:
                imported_name = (
                    f"{module}.{alias.name}"
                    if module
                    else alias.name
                )
                metadata["imports"].append(imported_name)

        elif isinstance(node, ast.FunctionDef):
            metadata["functions"].append(node.name)

        elif isinstance(node, ast.AsyncFunctionDef):
            metadata["functions"].append(node.name)

        elif isinstance(node, ast.ClassDef):
            metadata["classes"].append(node.name)
