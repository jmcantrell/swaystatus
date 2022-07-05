import shutil
from pathlib import Path
import pytest
from swaystatus import modules


def copy_module(name, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch()
    shutil.copy(Path(__file__).parent / "modules" / f"{name}.py", directory)


def test_modules_find(tmp_path):
    copy_module("no_output", tmp_path)
    assert modules.Modules([tmp_path]).find("no_output")


def test_modules_find_module_not_found(tmp_path):
    copy_module("no_output", tmp_path)
    with pytest.raises(ModuleNotFoundError, match="foo"):
        modules.Modules([tmp_path]).find("foo")


def test_modules_entry_points_after(tmp_path, monkeypatch):
    class Package:
        __name__ = "test"

    class EntryPoints:
        def select(self, **kwargs):
            assert kwargs["group"] == "swaystatus.modules"
            return [EntryPoint()]

    class EntryPoint:
        def load(self):
            return Package()

    def entry_points():
        return EntryPoints()

    monkeypatch.setattr(modules.metadata, "entry_points", entry_points)

    copy_module("no_output", tmp_path)

    packages = modules.Modules([tmp_path])._packages
    assert len(packages) == 2
    assert packages[-1] == "test"
