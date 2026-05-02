"""Architectural guard for ProcessingPosition cursor ownership."""

from __future__ import annotations

import ast
from pathlib import Path

_ALLOWED_CALLER = Path("trading_framework/core/domain/processing.py")
_ALLOWED_MUTATION_FILE = Path("trading_framework/core/domain/state.py")
_TARGET_METHOD = "_advance_processing_position"
_TARGET_ATTR = "_last_processing_position_index"
_POSITIONED_MARKET_TARGET_METHOD = "_update_market_from_positioned_canonical_event"


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _find_target_method_calls(path: Path) -> list[tuple[int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != _TARGET_METHOD:
            continue
        calls.append((node.lineno, node.col_offset))

    return calls


def _find_positioned_market_target_method_calls(path: Path) -> list[tuple[int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != _POSITIONED_MARKET_TARGET_METHOD:
            continue
        calls.append((node.lineno, node.col_offset))

    return calls


def _find_target_attr_mutations(path: Path) -> list[tuple[int, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    writes: list[tuple[int, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, ast.AugAssign):
            targets = [node.target]
        else:
            continue

        for target in targets:
            if isinstance(target, ast.Attribute) and target.attr == _TARGET_ATTR:
                writes.append((target.lineno, target.col_offset))

    return writes


def test_processing_position_cursor_is_mutated_only_via_canonical_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    production_root = repo_root / "trading_framework"

    call_violations: list[str] = []
    mutation_violations: list[str] = []

    for file_path in _iter_python_files(production_root):
        relative_path = file_path.relative_to(repo_root)

        method_calls = _find_target_method_calls(file_path)
        if method_calls and relative_path != _ALLOWED_CALLER:
            for lineno, col in method_calls:
                call_violations.append(
                    f"{relative_path}:{lineno}:{col} calls {_TARGET_METHOD}(...)"
                )

        attr_writes = _find_target_attr_mutations(file_path)
        if attr_writes and relative_path != _ALLOWED_MUTATION_FILE:
            for lineno, col in attr_writes:
                mutation_violations.append(
                    f"{relative_path}:{lineno}:{col} writes {_TARGET_ATTR}"
                )

    assert not call_violations, (
        "Unexpected ProcessingPosition cursor helper calls outside canonical boundary:\n"
        + "\n".join(call_violations)
    )
    assert not mutation_violations, (
        "Unexpected ProcessingPosition cursor mutations outside StrategyState:\n"
        + "\n".join(mutation_violations)
    )


def test_positioned_market_helper_is_called_only_via_canonical_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    production_root = repo_root / "trading_framework"

    call_violations: list[str] = []

    for file_path in _iter_python_files(production_root):
        relative_path = file_path.relative_to(repo_root)
        method_calls = _find_positioned_market_target_method_calls(file_path)
        if method_calls and relative_path != _ALLOWED_CALLER:
            for lineno, col in method_calls:
                call_violations.append(
                    f"{relative_path}:{lineno}:{col} calls "
                    f"{_POSITIONED_MARKET_TARGET_METHOD}(...)"
                )

    assert not call_violations, (
        "Unexpected positioned market helper calls outside canonical boundary:\n"
        + "\n".join(call_violations)
    )
