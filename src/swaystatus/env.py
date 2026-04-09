import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from pathlib import Path

from .paths import path_normalized


def environ_path(name: str) -> Path:
    """Return a path from an environment variable."""
    return path_normalized(os.environ[name])


def environ_paths(name: str) -> list[Path]:
    """Return a list of paths from and environment variable."""
    return list(map(path_normalized, os.environ[name].split(":")))


def environ_alter(updates: Mapping[str, str | None]) -> None:
    """Alter the environment by unsetting the `None` values and setting others."""
    for name, value in updates.items():
        if value is None:
            with suppress(KeyError):
                del os.environ[name]
        else:
            os.environ[name] = str(value)


@contextmanager
def environ_update(**kwargs: str | None) -> Iterator:
    """Alter the environment during execution of a block."""
    environ_save = {k: os.environ.get(k) for k in kwargs}
    environ_alter(kwargs)
    try:
        yield
    finally:
        environ_alter(environ_save)
