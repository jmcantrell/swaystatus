import logging
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus import cli
from swaystatus.logger import logger


class TestMain(TestCase):
    def setUp(self) -> None:
        app_patcher = patch("swaystatus.cli.App")
        self.app_mock = app_patcher.start()
        self.addCleanup(app_patcher.stop)

        self.fake_exc = Exception("BOOM!")

    def test_exit(self) -> None:
        self.assertEqual(cli.main(), 0, "expected a zero status")
        self.app_mock.return_value.run.assert_called_once()

    def test_raises(self) -> None:
        for source, mock in [
            ("init", self.app_mock),
            ("start", self.app_mock.return_value.start),
        ]:
            with self.subTest(source=source):
                self.app_mock.reset_mock()
                mock.side_effect = self.fake_exc

                with self.assertLogs(logger, logging.ERROR) as logged:
                    self.assertEqual(cli.main(), 1, "expected a non-zero status")

                record = logged.records[0]
                assert record.exc_info
                self.assertIs(record.exc_info[1], self.fake_exc)
                self.assertEqual(record.message, "unhandled exception in app")


if __name__ == "__main__":
    main()
