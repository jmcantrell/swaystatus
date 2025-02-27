import importlib
import sys

import pytest

from swaystatus.modules import ModuleRegistry


def test_modules_load_module_not_found() -> None:
    """Ensure that requesting a non-existent module will raise an error."""
    with pytest.raises(ModuleNotFoundError, match="foo"):
        registry = ModuleRegistry([])
        registry.packages = []
        registry.element_class("foo")


def test_modules_load(tmp_module) -> None:
    """Ensure that an existing module will be found in a valid package."""
    path = tmp_module(dst_name="foo.py")
    modules = ModuleRegistry([path.parent])
    Element = modules.element_class("foo")
    assert sys.modules[Element.__module__].__file__ == str(path)


def test_modules_load_first_found(tmp_module) -> None:
    """Ensure packages included earlier have preference when looking for a module."""
    name = "foo"
    path1 = tmp_module(dst_name=f"a/{name}.py")
    path2 = tmp_module(dst_name=f"b/{name}.py")
    registry = ModuleRegistry([path1.parent, path2.parent])
    Element = registry.element_class(name)
    assert sys.modules[Element.__module__].__file__ == str(path1)


def test_modules_entry_points(tmp_module, monkeypatch) -> None:
    """Ensure that module packages defined as an entry point are recognized."""

    class Package:
        __name__ = "entry"

    class EntryPoint:
        def load(self):
            return Package()

    def entry_points(**kwargs):
        assert kwargs["group"] == "swaystatus.modules"
        return [EntryPoint()]

    monkeypatch.setattr(importlib.metadata, "entry_points", entry_points)
    registry = ModuleRegistry([tmp_module().parent])
    assert len(registry.packages) == 2  # tmp_path and the fake entry point
    assert registry.packages[-1] == "entry"  # the fake entry point is after tmp_path
