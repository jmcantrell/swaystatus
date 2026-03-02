import time


class Elapsed:
    seconds: float | None

    def __enter__(self):
        self.start = time.perf_counter()
        self.seconds = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.seconds = time.perf_counter() - self.start
