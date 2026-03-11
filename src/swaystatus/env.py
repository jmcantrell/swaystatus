import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping


def environ_path(name: str) -> Path | None:
    """Return a path from an environment variable (if set)."""
    if value := os.environ.get(name):
        return Path(value)
    return None


def environ_paths(name: str) -> list[Path]:
    """Return a list of paths from and environment variable."""
    if value := os.environ.get(name):
        return list(map(Path, value.split(":")))
    return []


def environ_alter(updates: Mapping[str, str | None]) -> None:
    """Alter the environment by unsetting the `None` values and setting others."""
    for name, value in updates.items():
        if value is None:
            try:
                del os.environ[name]
            except KeyError:
                pass
        else:
            os.environ[name] = str(value)


@contextmanager
def environ_update(**kwargs: str | None) -> Iterator:
    """Alter the environment during execution of a block."""
    environ_save = {k: os.environ.get(k) for k in kwargs.keys()}
    environ_alter(kwargs)
    try:
        yield
    finally:
        environ_alter(environ_save)
