import toml
import shutil
import pytest
from pathlib import Path
from swaystatus.config import Config


@pytest.fixture(autouse=True)
def reset(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setenv("HOME", str(tmp_path))


def copy_module(name, directory):
    shutil.copy(Path(__file__).parent / "modules" / f"{name}.py", directory)


def init_modules_dir(directory, *modules):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "__init__.py").touch()

    for module_name in modules:
        copy_module(module_name, directory)


def write_config(file, config):
    file.parent.mkdir(parents=True, exist_ok=True)
    open(file, "w").write(toml.dumps(config))


def test_config_default(tmp_path):
    directory = tmp_path / ".config" / "swaystatus"

    config = Config()
    config.load()

    assert config.directory == directory
    assert config.file == directory / "config.toml"
    assert config.elements == []


def test_config_xdg(monkeypatch, tmp_path):
    directory = tmp_path / "alt-config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(directory))
    directory /= "swaystatus"

    config = Config()
    config.load()

    assert config.directory == directory
    assert config.file == directory / "config.toml"
    assert config.elements == []


def test_config_module():
    config = Config()

    modules_dir = config.directory / "modules"
    init_modules_dir(modules_dir, "no_output")
    write_config(config.file, dict(modules_order=["no_output"]))

    config.load()

    assert len(config.elements) == 1
    assert config.elements[0].name == "no_output"


def test_config_modules_path(tmp_path):
    config = Config()

    modules_dir = tmp_path / "extra-modules"
    init_modules_dir(modules_dir, "no_output")
    write_config(
        config.file,
        dict(
            modules_order=["no_output"],
            modules_path=[str(modules_dir)],
        ),
    )

    config.load()

    assert len(config.elements) == 1
    assert config.elements[0].name == "no_output"


def test_config_no_module_empty_path():
    config = Config()

    write_config(config.file, dict(modules_order=["does_not_exist"]))

    with pytest.raises(ModuleNotFoundError, match="does_not_exist"):
        config.load()


def test_config_no_module_non_empty_path():
    config = Config()

    modules_dir = config.directory / "modules"
    init_modules_dir(modules_dir, "no_output")
    write_config(config.file, dict(modules_order=["does_not_exist"]))

    with pytest.raises(ModuleNotFoundError, match="does_not_exist"):
        config.load()
