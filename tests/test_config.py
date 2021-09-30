import toml
import pytest
from schema import SchemaError, SchemaMissingKeyError
from swaystatus.config import Config

any_value = ["x", 0, 0.0, True, [], {}, None]


def min_config(**kwargs):
    data = {"order": []}
    data.update(kwargs)
    return data


@pytest.fixture
def write_config(tmp_path):
    def func(data):
        config_file = tmp_path / "config.toml"
        open(config_file, "w").write(toml.dumps(data))
        return config_file

    return func


def test_config_dict():
    assert isinstance(Config(), dict)


def test_config_order_required(write_config):
    with pytest.raises(SchemaMissingKeyError, match="order"):
        Config().read_file(write_config({}))


def test_config_order_is_list(write_config):
    with pytest.raises(SchemaError, match=r"foo.*list"):
        Config().read_file(write_config({"order": "foo"}))


def test_config_order_is_list_of_str(write_config):
    with pytest.raises(SchemaError, match=r"0.*str"):
        Config().read_file(write_config({"order": [0]}))


def test_config_order_valid(write_config):
    config = Config()
    config.read_file(write_config({"order": ["foo"]}))
    assert "order" in config


def test_config_click_events_is_bool(write_config):
    with pytest.raises(SchemaError, match=r"foo.*bool"):
        Config().read_file(write_config(min_config(click_events="foo")))


def test_config_click_events_valid(write_config):
    config = Config()
    config.read_file(write_config(min_config(click_events=True)))
    assert "click_events" in config


def test_config_include_is_list(write_config):
    with pytest.raises(SchemaError, match=r"foo.*list"):
        Config().read_file(write_config(min_config(include="foo")))


def test_config_include_is_list_of_str(write_config):
    with pytest.raises(SchemaError, match=r"0.*str"):
        Config().read_file(write_config(min_config(include=[0])))


def test_config_include_valid(write_config):
    config = Config()
    config.read_file(write_config(min_config(include=["foo"])))
    assert "include" in config


def test_config_interval_is_float(write_config):
    with pytest.raises(SchemaError, match=r"foo.*float"):
        Config().read_file(write_config(min_config(interval="foo")))


def test_config_interval_valid(write_config):
    config = Config()
    config.read_file(write_config(min_config(interval=0)))
    assert "interval" in config


def test_config_settings_is_dict(write_config):
    with pytest.raises(SchemaError, match=r"foo.*dict"):
        Config().read_file(write_config(min_config(settings="foo")))


def test_config_settings_valid_empty(write_config):
    config = Config()
    config.read_file(write_config(min_config(settings={})))
    assert "settings" in config


def test_config_settings_is_dict_of_dicts(write_config):
    with pytest.raises(SchemaError, match=r"bar.*dict"):
        Config().read_file(write_config(min_config(settings={"foo": "bar"})))


@pytest.mark.parametrize("value", any_value)
def test_config_settings_valid(write_config, value):
    config = Config()
    config.read_file(
        write_config(min_config(settings={"foo": {"bar": value}}))
    )
    assert "settings" in config


def test_config_on_click_is_dict(write_config):
    with pytest.raises(SchemaError, match=r"foo.*dict"):
        Config().read_file(write_config(min_config(on_click="foo")))


def test_config_on_click_empty(write_config):
    config = Config()
    config.read_file(write_config(min_config(on_click={})))
    assert "on_click" in config


def test_config_on_click_is_dict_of_dicts(write_config):
    with pytest.raises(SchemaError, match=r"bar.*dict"):
        Config().read_file(write_config(min_config(on_click={"foo": "bar"})))


def test_config_on_click_dict_empty(write_config):
    config = Config()
    config.read_file(write_config(min_config(on_click={"foo": {}})))
    assert "on_click" in config


def test_config_on_click_int_keys(write_config):
    with pytest.raises(SchemaError, match=r"bar"):
        Config().read_file(
            write_config(min_config(on_click={"foo": {"bar": "baz"}}))
        )


def test_config_on_click_positive_keys(write_config):
    with pytest.raises(SchemaError, match=r"Wrong key.*0"):
        Config().read_file(
            write_config(min_config(on_click={"foo": {"0": "bar"}}))
        )


def test_config_on_click_valid(write_config):
    config = Config()
    config.read_file(
        write_config(
            min_config(
                on_click={
                    "foo": {"1": "x", "2": ["y", "z"]},
                    "bar": {"3": "x", "4": ["y", "z"]},
                }
            )
        )
    )
    assert "on_click" in config
