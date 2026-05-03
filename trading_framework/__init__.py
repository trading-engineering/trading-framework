"""Compatibility import shim for the legacy trading_framework package.

This package is kept for one transition window and redirects imports to
tradingchassis_core.
"""

from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
import warnings

_OLD_ROOT = "trading_framework"
_NEW_ROOT = "tradingchassis_core"


def _to_new_name(fullname: str) -> str | None:
    if fullname == _OLD_ROOT:
        return _NEW_ROOT
    if fullname.startswith(f"{_OLD_ROOT}."):
        return f"{_NEW_ROOT}{fullname[len(_OLD_ROOT):]}"
    return None


class _LegacyAliasLoader(importlib.abc.Loader):
    def __init__(self, old_name: str, new_name: str) -> None:
        self._old_name = old_name
        self._new_name = new_name

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> object:
        module = importlib.import_module(self._new_name)
        sys.modules[self._old_name] = module
        return module

    def exec_module(self, module: object) -> None:
        return None


class _LegacyAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(
        self,
        fullname: str,
        path: object | None,
        target: object | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname == _OLD_ROOT:
            return None
        new_name = _to_new_name(fullname)
        if new_name is None:
            return None

        new_spec = importlib.util.find_spec(new_name)
        if new_spec is None:
            return None

        is_package = new_spec.submodule_search_locations is not None
        spec = importlib.machinery.ModuleSpec(
            name=fullname,
            loader=_LegacyAliasLoader(old_name=fullname, new_name=new_name),
            is_package=is_package,
        )
        if is_package:
            spec.submodule_search_locations = list(new_spec.submodule_search_locations or [])
        spec.origin = f"alias:{new_name}"
        return spec


def _install_alias_finder() -> None:
    for finder in sys.meta_path:
        if isinstance(finder, _LegacyAliasFinder):
            return
    sys.meta_path.insert(0, _LegacyAliasFinder())


_install_alias_finder()
warnings.warn(
    "trading_framework is deprecated; import from tradingchassis_core instead.",
    DeprecationWarning,
    stacklevel=2,
)

_new_pkg = importlib.import_module(_NEW_ROOT)
__all__ = list(getattr(_new_pkg, "__all__", []))

for _name in __all__:
    globals()[_name] = getattr(_new_pkg, _name)
