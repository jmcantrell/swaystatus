import logging
from threading import Thread
from unittest import TestCase, main

from swaystatus.logger import logger


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


if __name__ == "__main__":
    main()
