import os
import sys
from contextlib import contextmanager
from pathlib import Path

self_name = os.path.basename(sys.argv[0])

cache_home = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
data_home = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()


def environ_path(name: str) -> Path | None:
    """Return a path from an environment variable (if set)."""
    if value := os.environ.get(name):
        return Path(value).expanduser()
    return None


def environ_paths(name: str) -> list[Path] | None:
    """Return paths from a colon-separated environment variable (if set)."""
    if value := os.environ.get(name):
        return [Path(p).expanduser() for p in value.split(":")]
    return None


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
