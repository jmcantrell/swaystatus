import os
from pathlib import Path

from swaystatus.env import environ_path, environ_paths, environ_update

var_name = "SWAYSTATUS_TEST_VAR"


def test_environ_path_set() -> None:
    """Ensure that a path is returned if an environment variable is set."""
    path = Path("/path/to/file")
    os.environ[var_name] = str(path)
    assert environ_path(var_name) == path


def test_environ_path_unset() -> None:
    """Ensure that nothing is returned if an environment variable is not set."""
    try:
        del os.environ[var_name]
    except KeyError:
        pass
    assert environ_path(var_name) is None


def test_environ_paths_set() -> None:
    """Ensure that a list of paths is returned if an environment variable is set."""
    paths = list(map(Path, ["/path/to/file1", "/path/to/file2", "/path/to/file3"]))
    os.environ[var_name] = ":".join(map(str, paths))
    assert environ_paths(var_name) == paths


def test_environ_paths_unset() -> None:
    """Ensure that an empty list is returned if an environment variable is not set."""
    try:
        del os.environ[var_name]
    except KeyError:
        pass
    assert environ_paths(var_name) == []


def test_environ_update() -> None:
    """Ensure that environment changes are made and reverted."""
    os.environ[var_name] = "foo"
    with environ_update(**{var_name: "bar"}):
        assert os.environ[var_name] == "bar"
    assert os.environ[var_name] == "foo"
