import importlib
import shutil
import sys
from pathlib import Path

import pytest

from swaystatus.modules import ModuleRegistry


@pytest.fixture
def temp_module(tmp_path):
    def copy(src_name: str | None = None, dst_name: str | None = None) -> Path:
        src = Path(__file__).parent / "modules" / (src_name or "no_output.py")
        dst = tmp_path / (dst_name or src.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        (dst.parent / "__init__.py").touch()
        shutil.copyfile(src, dst)
        return dst

    return copy


def test_modules_load_module_not_found() -> None:
    """Ensure that requesting a non-existent module will raise an error."""
    with pytest.raises(ModuleNotFoundError, match="foo"):
        registry = ModuleRegistry([])
        registry.packages = []
        registry.element_class("foo")


def test_modules_load(temp_module) -> None:
    """Ensure that an existing module will be found in a valid package."""
    path = temp_module(dst_name="foo.py")
    modules = ModuleRegistry([path.parent])
    Element = modules.element_class("foo")
    assert sys.modules[Element.__module__].__file__ == str(path)


def test_modules_load_first_found(temp_module) -> None:
    """Ensure packages included earlier have preference when looking for a module."""
    name = "foo"
    path1 = temp_module(dst_name=f"a/{name}.py")
    path2 = temp_module(dst_name=f"b/{name}.py")
    registry = ModuleRegistry([path1.parent, path2.parent])
    Element = registry.element_class(name)
    assert sys.modules[Element.__module__].__file__ == str(path1)


def test_modules_entry_points(temp_module, monkeypatch) -> None:
    """Ensure that module packages defined as an entry point are recognized."""

    class Package:
        __name__ = "entry"

    class EntryPoint:
        def load(self):
            return Package()

    def entry_points(**kwargs):
        assert kwargs["group"] == "swaystatus.modules"
        return [EntryPoint()]

    assert hasattr(importlib, "metadata")
    monkeypatch.setattr(importlib.metadata, "entry_points", entry_points)
    registry = ModuleRegistry([temp_module().parent])
    assert len(registry.packages) == 2  # tmp_path and the fake entry point
    assert registry.packages[-1] == "entry"  # the fake entry point is after tmp_path
