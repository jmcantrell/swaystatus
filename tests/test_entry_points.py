import json
import random
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from signal import SIGCONT, SIGSTOP, SIGTERM, SIGUSR1
from subprocess import PIPE, Popen
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.cli import self_name


class TestModule(TestCase):
    def setUp(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.home_path_fake = Path(temp_dir.name)

        home_patcher = patch("pathlib.Path.home", return_value=self.home_path_fake)
        self.home_mock = home_patcher.start()
        self.addCleanup(home_patcher.stop)

        self.env = {
            "XDG_DATA_HOME": str(self.home_path_fake / "data"),
            "XDG_CONFIG_HOME": str(self.home_path_fake / "config"),
        }

    def command(self) -> list[str]:
        return [sys.executable, "-m", self_name]

    @contextmanager
    def command_running(self, *extra_args: str, click_events=False) -> Iterator[Popen[str]]:
        args = self.command()
        if click_events:
            args.append("--click-events")
        args.extend(extra_args)

        process = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, env=self.env)

        assert process.stdout
        self.assertEqual(
            json.loads(process.stdout.readline().strip()),
            dict(
                version=1,
                stop_signal=SIGSTOP,
                cont_signal=SIGCONT,
                click_events=click_events,
            ),
        )
        self.assertEqual(process.stdout.readline(), "[[]\n")

        yield process

        process.send_signal(SIGTERM)
        process.communicate(timeout=1.0)
        self.assertEqual(process.returncode, 0)

    def test_update(self) -> None:
        with self.command_running() as process:
            assert process.stdout
            self.assertEqual(process.stdout.readline(), ",[]\n")
            for _ in range(random.randint(5, 10)):
                process.send_signal(SIGUSR1)
                self.assertEqual(process.stdout.readline(), ",[]\n")

    def test_output(self) -> None:
        pass


class TestScript(TestModule):
    def command(self) -> list[str]:
        return [str(Path(sys.executable).parent / self_name)]


if __name__ == "__main__":
    main()
