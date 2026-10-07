import os
from pathlib import Path
from random import randint
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.xdg import xdg_config_home, xdg_data_home


class TestXDG(TestCase):
    def setUp(self) -> None:
        env_patcher = patch.dict(os.environ, clear=True)
        self.env = env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def test_config_home_default(self) -> None:
        self.assertEqual(xdg_config_home(), Path.home() / ".config")

    def test_config_home_env_overrides_default(self) -> None:
        expected_config_home = Path(f"/path/to/config-{randint(1, 100)}")
        self.env["XDG_CONFIG_HOME"] = str(expected_config_home)
        self.assertEqual(xdg_config_home(), expected_config_home)

    def test_data_home_default(self) -> None:
        self.assertEqual(xdg_data_home(), Path.home() / ".local/share")

    def test_data_home_env_overrides_default(self) -> None:
        expected_data_home = Path(f"/path/to/data-{randint(1, 100)}")
        self.env["XDG_DATA_HOME"] = str(expected_data_home)
        self.assertEqual(xdg_data_home(), expected_data_home)


if __name__ == "__main__":
    main()
