import importlib

import pytest

from swaystatus.modules import Modules


def test_modules_load_module_not_found():
    """Ensure that requesting a non-existent module will raise an error."""
    with pytest.raises(ModuleNotFoundError, match="foo"):
        Modules([]).load("foo")


def test_modules_load(tmp_module):
    """Ensure that an existing module will be found in a valid package."""
    path = tmp_module("no_output")
    assert Modules([path.parent]).load("no_output").__file__ == str(path)


def test_modules_entry_points(tmp_module, monkeypatch):
    """Ensure that module packages defined as an entry point are recognized."""

    class Package:
        __name__ = "test"

    class EntryPoint:
        def load(self):
            return Package()

    def entry_points(**kwargs):
        assert kwargs["group"] == "swaystatus.modules"
        return [EntryPoint()]

    monkeypatch.setattr(importlib.metadata, "entry_points", entry_points)
    path = tmp_module("no_output")

    packages = Modules([path.parent]).packages
    assert len(packages) == 2  # tmp_path and the fake entry point
    assert packages[-1] == "test"  # the fake entry point is after tmp_path
