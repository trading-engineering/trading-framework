"""Guards that core package stays runtime-independent."""

from __future__ import annotations

from pathlib import Path


def test_core_package_has_no_runtime_or_hftbacktest_imports() -> None:
    package_root = Path(__file__).resolve().parents[2] / "tradingchassis_core"
    for file_path in package_root.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        assert "hftbacktest" not in content
        assert "core_runtime" not in content
