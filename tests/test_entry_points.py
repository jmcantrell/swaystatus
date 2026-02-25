import json
import sys
from pathlib import Path
from signal import SIGCONT, SIGSTOP, SIGUSR1
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch


class TestModule(TestCase):
    def setUp(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        home_path_fake = Path(temp_dir.name)

        home_patcher = patch("pathlib.Path.home", return_value=home_path_fake)
        home_patcher.start()
        self.addCleanup(home_patcher.stop)

        modules_dir = home_path_fake / "data/swaystatus/modules"
        config_file = home_path_fake / "config/swaystatus/config.toml"

        self.env = {
            "XDG_DATA_HOME": str(modules_dir.parent.parent),
            "XDG_CONFIG_HOME": str(config_file.parent.parent),
        }

        config_file.parent.mkdir(parents=True)
        config_file.write_text('[[modules]]\nname = "test"\n')

        modules_dir.mkdir(parents=True)
        (modules_dir / "__init__.py").touch()
        (Path(__file__).parent / "data/modules/test.py").copy_into(modules_dir)

        self.process = Popen(self.command(), stdin=PIPE, stdout=PIPE, text=True, env=self.env)
        assert self.process.stdout

        self.stdout = self.process.stdout

        def shutdown():
            self.process.terminate()
            stdout, _ = self.process.communicate(timeout=1.0)
            self.assertFalse(stdout, "stdout had unexpected output")
            self.assertEqual(self.process.returncode, 0)

        self.addCleanup(shutdown)

    def command(self) -> list[str]:
        return [sys.executable, "-m", "swaystatus"]

    def test_stdout(self) -> None:
        self.assertEqual(
            json.loads(self.stdout.readline().strip()),
            {
                "version": 1,
                "stop_signal": SIGSTOP,
                "cont_signal": SIGCONT,
                "click_events": False,
            },
        )
        self.assertEqual(self.stdout.readline(), "[[]\n")
        self.assertEqual(self.stdout.readline(), ',[{"full_text": "test", "name": "test"}]\n')
        self.process.send_signal(SIGUSR1)
        self.assertEqual(self.stdout.readline(), ',[{"full_text": "test", "name": "test"}]\n')


class TestScript(TestModule):
    def command(self) -> list[str]:
        return [str(Path(sys.executable).parent / "swaystatus")]


if __name__ == "__main__":
    main()
