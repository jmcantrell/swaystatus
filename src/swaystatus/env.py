import os
import sys
from contextlib import contextmanager
from pathlib import Path

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
def environ_update(**kwargs):
    """Alter the environment during execution of a block."""
    environ_save = os.environ.copy()
    os.environ.update({k: str(v) for k, v in kwargs.items()})
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(environ_save)
