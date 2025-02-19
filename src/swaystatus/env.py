import os
import sys
from pathlib import Path

self_name = os.path.basename(sys.argv[0])

cache_home = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
data_home = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()


def environ_path(name: str) -> Path | None:
    if value := os.environ.get(name):
        return Path(value).expanduser()
    return None


def environ_paths(name: str) -> list[Path] | None:
    if value := os.environ.get(name):
        return [Path(p).expanduser() for p in value.split(":")]
    return None
