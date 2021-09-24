import shutil
from pathlib import Path
import pytest
from swaystatus.modules import Modules


def copy_module(name, directory):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch()
    shutil.copy(Path(__file__).parent / "modules" / f"{name}.py", directory)


def test_modules_find(tmp_path):
    copy_module("no_output", tmp_path)
    assert Modules([tmp_path]).find("no_output")


def test_modules_find_module_not_found():
    with pytest.raises(ModuleNotFoundError, match="foo"):
        Modules([]).find("foo")
