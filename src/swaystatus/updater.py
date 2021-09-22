import json
import time
import signal


header = json.dumps(
    {
        "version": 1,
        "click_events": True,
        "stop_signal": signal.SIGTSTP,
    }
)
body_start = "[[]"
body_item = ",{}"


class Updater:
    def __init__(self, elements, interval=None):
        super().__init__()

        self.elements = elements
        self.element_timers = []

        for element in elements:
            element.updater = self
            self.element_timers.append([0] * len(element.intervals))

        self.interval = interval or 1

        self.time_before = time.perf_counter()

    def _running(self):
        return True

    def _send_line(self, line):
        print(line, flush=True)

    def _send_update(self):
        output = []
        for element in self.elements:
            element.on_update(output)
        self._send_line(body_item.format(json.dumps(output)))

    def update(self):
        time_now = time.perf_counter()
        self.seconds_elapsed = time_now - self.time_before
        self.time_before = time_now

        for element_index, element in enumerate(self.elements):
            timers = self.element_timers[element_index]
            for interval_index, timer in enumerate(timers):
                timer += self.seconds_elapsed
                interval, options = element.intervals[interval_index]
                if timer >= interval:
                    element.on_interval(options=options)
                    timers[interval_index] = 0
                else:
                    timers[interval_index] = timer

        self._send_update()

    def run(self):
        self._send_line(header)
        self._send_line(body_start)

        while self._running():
            self.update()
            time.sleep(self.interval)
