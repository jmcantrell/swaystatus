from pathlib import Path

from pytest import raises

from swaystatus.config import Config


def test_module_keys() -> None:
    """Module keys can be iterated."""
    config = Config(
        modules=[
            {"name": "clock"},
            {"name": "clock", "instance": "home"},
        ]
    )
    assert list(config.module_keys()) == [
        ("clock", None),
        ("clock", "home"),
    ]


def test_module_missing() -> None:
    """A missing module will cause an exception."""
    with raises(KeyError):
        Config().module("clock")
    with raises(KeyError):
        Config().module("clock", "home")


def test_module_empty() -> None:
    """A module with no configuration will get an empty dictionary."""
    config = Config(
        modules=[
            {"name": "clock"},
            {"name": "clock", "instance": "home"},
        ]
    )
    assert config.module("clock") == {}
    assert config.module("clock", "home") == {}


def test_module_env() -> None:
    """A module can configure the environment."""
    config = Config(
        env={
            "LC_COLLATE": "C",
        },
        settings={
            "clock": {
                "env": {
                    "TZ": "UTC",
                    "LC_TIME": "en_US",
                },
            }
        },
        modules=[
            {
                "name": "clock",
                "env": {
                    "TZ": "America/Chicago",
                },
            },
        ],
    )
    assert config.module("clock") == {
        "env": {
            "LC_COLLATE": "C",
            "LC_TIME": "en_US",
            "TZ": "America/Chicago",
        }
    }


def test_module_on_click() -> None:
    """A module can configure click handlers."""
    config = Config(
        settings={
            "clock": {
                "on_click": {
                    1: "foot -H cal",
                    2: "date | wl-copy -n",
                },
            }
        },
        modules=[
            {
                "name": "clock",
                "on_click": {
                    2: "foot -H timedatectl",
                },
            },
        ],
    )
    assert config.module("clock") == {
        "on_click": {
            1: "foot -H cal",
            2: "foot -H timedatectl",
        },
    }


def test_module_params() -> None:
    """A module can configure extra parameters."""
    config = Config(
        settings={
            "clock": {
                "params": {
                    "full_text": "%c",
                    "short_text": "%r",
                },
            }
        },
        modules=[
            {
                "name": "clock",
                "params": {
                    "short_text": "%s",
                },
            },
        ],
    )
    assert config.module("clock") == {
        "full_text": "%c",
        "short_text": "%s",
    }


def test_from_file() -> None:
    """Configuration can be loaded from a file."""
    config_file = Path(__file__).parent / "data/config.toml"
    config = Config.from_file(config_file)
    assert config.interval == 5.0
    assert config.click_events
    assert config.module("clock") == {
        "full_text": "%r",
        "on_click": {1: "foot -H cal"},
        "env": {
            "LC_COLLATE": "C",
            "TZ": "America/Chicago",
        },
    }
