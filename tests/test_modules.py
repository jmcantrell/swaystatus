import shutil
import pytest
from pathlib import Path
from swaystatus import modules


def copy_module(name, directory: Path):
    """
    Copy a test module to a package directory.
    """

    fname = f"{name}.py"
    src = Path(__file__).parent / "modules" / fname
    dst = directory / fname

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch()
    shutil.copyfile(src, dst)

    return dst


def test_modules_find_module_not_found():
    """
    Ensure that requesting a non-existent module will raise an error.
    """

    with pytest.raises(ModuleNotFoundError, match="foo"):
        modules.Modules([]).find("foo")


def test_modules_find(tmp_path):
    """
    Ensure that an existing module will be found in a valid package.
    """

    path = copy_module("no_output", tmp_path)
    assert modules.Modules([tmp_path]).find("no_output").__file__ == str(path)


def test_modules_entry_points(tmp_path, monkeypatch):
    """
    Ensure that module packages defined as an entry point are recognized.
    """

    class Package:
        __name__ = "test"

    class EntryPoint:
        def load(self):
            return Package()

    def entry_points(**kwargs):
        assert kwargs["group"] == "swaystatus.modules"
        return [EntryPoint()]

    monkeypatch.setattr(modules.metadata, "entry_points", entry_points)

    copy_module("no_output", tmp_path)

    packages = modules.Modules([tmp_path])._packages

    assert len(packages) == 2
    assert packages[-1] == "test"
