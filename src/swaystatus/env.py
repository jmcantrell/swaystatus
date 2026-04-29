import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from pathlib import Path


def environ_path(name: str) -> Path | None:
    """Return a path from an environment variable (if set)."""
    return Path(value) if (value := os.environ.get(name)) else None


def environ_paths(name: str) -> list[Path]:
    """Return a list of paths from and environment variable."""
    return list(map(Path, value.split(":"))) if (value := os.environ.get(name)) else []


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
