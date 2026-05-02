"""Architectural guard for canonical reducer authority hardening."""

from __future__ import annotations

import ast
from pathlib import Path

_ALLOWED_CALLER = Path("trading_framework/core/domain/processing.py")
_TARGET_METHODS = frozenset(
    {
        "update_market",
        "apply_fill_event",
        "apply_order_submitted_event",
    }
)


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _find_target_calls(path: Path) -> list[tuple[int, int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[tuple[int, int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        method_name = node.func.attr
        if method_name not in _TARGET_METHODS:
            continue
        calls.append((node.lineno, node.col_offset, method_name))

    return calls


def test_direct_reducer_calls_are_limited_to_canonical_processing_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    production_root = repo_root / "trading_framework"

    violations: list[str] = []

    for file_path in _iter_python_files(production_root):
        relative_path = file_path.relative_to(repo_root)
        calls = _find_target_calls(file_path)
        if not calls:
            continue

        if relative_path == _ALLOWED_CALLER:
            continue

        for lineno, col, method_name in calls:
            violations.append(f"{relative_path}:{lineno}:{col} calls {method_name}(...)")

    assert not violations, "Unexpected direct reducer calls outside canonical boundary:\n" + "\n".join(
        violations
    )
