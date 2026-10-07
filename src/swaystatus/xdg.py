from pathlib import Path

from .env import environ_path


def xdg_config_home() -> Path:
    """Base directory for configuration files."""
    return environ_path("XDG_CONFIG_HOME") or Path.home() / ".config"


def xdg_data_home() -> Path:
    """Base directory for data files."""
    return environ_path("XDG_DATA_HOME") or Path.home() / ".local/share"
