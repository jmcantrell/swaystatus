import os
import sys
from pathlib import Path

bin_name = os.path.basename(sys.argv[0])
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()


def environ_path(name, default=None):
    value = os.environ.get(name, default)
    return Path(value).expanduser() if value else default


def environ_paths(name, default=None):
    value = os.environ.get(name)
    parts = value.split(":") if value else (default or [])
    return [Path(p).expanduser() for p in parts]
