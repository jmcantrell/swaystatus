import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

self_name = os.path.basename(sys.argv[0])


def environ_path(name: str) -> Path | None:
    """Return a path from an environment variable (if set)."""
    if value := os.environ.get(name):
        return Path(value).expanduser()
    return None


def environ_paths(name: str) -> list[Path]:
    """Return a list of paths from and environment variable."""
    return [Path(p).expanduser() for p in os.environ[name].split(":")] if name in os.environ else []


@contextmanager
def environ_update(**kwargs) -> Iterator:
    """Alter the environment during execution of a block."""
    environ_save = {k: os.environ.get(k) for k in kwargs.keys()}
    os.environ.update({k: str(v) for k, v in kwargs.items()})
    try:
        yield
    finally:
        for key, value in environ_save.items():
            if value is None:
                try:
                    del os.environ[key]
                except KeyError:
                    pass
            else:
                os.environ[key] = value
