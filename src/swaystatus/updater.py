import json, time
from signal import SIGTSTP


def send_line(line):
    print(line, flush=True)


class Updater:
    def __init__(self, elements, **options):
        super().__init__()

        self.elements = elements
        self.element_timers = []

        for element in elements:
            element.updater = self
            self.element_timers.append([0] * len(element.intervals))

        self.interval = options.get("interval", 1)

        self.time_before = time.perf_counter()

        self._running = False

        self._header = {
            "version": 1,
            "stop_signal": SIGTSTP,
            "click_events": options.get("click_events", True),
        }
        self._body_start = "[[]"
        self._body_item = ",{}"

    def update(self):
        time_now = time.perf_counter()
        self.seconds_elapsed = time_now - self.time_before
        self.time_before = time_now

        output = []

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
            element.on_update(output)

        send_line(self._body_item.format(json.dumps(output)))

    def running(self):
        return self._running

    def stop(self):
        self._running = False

    def start(self):
        self._running = True

        send_line(json.dumps(self._header))
        send_line(self._body_start)

        while self.running():
            self.update()
            time.sleep(self.interval)
