from swaystatus.config import Config


def test_config_default(tmp_path):
    config_dir = tmp_path / ".config" / "swaystatus"
    config_file = config_dir / "config.toml"

    config = Config(config_file)

    assert config.order == []
    assert config.interval == 1
    assert config.include == []
    assert config.settings == {}
    assert config.click_events
