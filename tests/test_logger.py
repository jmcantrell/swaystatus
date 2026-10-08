import logging
from threading import Thread
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.logger import logger, logger_level_at


class TestThreadExcepthook(TestCase):
    def test_log_exception(self) -> None:
        exception = Exception("BOOM!")

        def run() -> None:
            raise exception

        thread = Thread(target=run, name="TestThread")

        with self.assertLogs(logger, logging.ERROR) as logged:
            thread.start()
            thread.join(timeout=1.0)

        record = logged.records[0]
        assert record.exc_info
        self.assertIs(record.exc_info[1], exception)
        self.assertEqual(record.message, "unhandled exception in thread: TestThread")


class TestLoggerLevelAt(TestCase):
    def setUp(self) -> None:
        logger_patcher = patch("swaystatus.logger.logger", logging.getLogger("test"))
        self.logger_mock = logger_patcher.start()
        self.addCleanup(logger_patcher.stop)

    def test_context(self) -> None:
        self.logger_mock.setLevel(30)
        with logger_level_at(42):
            self.assertEqual(self.logger_mock.level, 42)
        self.assertEqual(self.logger_mock.level, 30)

    def test_context_noop(self) -> None:
        self.logger_mock.setLevel(30)
        with logger_level_at(None):
            self.assertEqual(self.logger_mock.level, 30)
        self.assertEqual(self.logger_mock.level, 30)


if __name__ == "__main__":
    main()
