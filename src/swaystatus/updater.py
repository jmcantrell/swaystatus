import time
import json
from signal import SIGSTOP, SIGCONT


def send_line(line):
    print(line, flush=True)


class Updater:
    def __init__(self, elements, interval, click_events):
        super().__init__()

        self.elements = elements
        self.element_timers = []
        for element in self.elements:
            self.element_timers.append([0] * len(element.intervals))

        self.interval = interval
        self.time_before = time.perf_counter()

        self._header = {
            "version": 1,
            "stop_signal": SIGSTOP,
            "cont_signal": SIGCONT,
            "click_events": click_events,
        }
        self._body_start = "[[]"
        self._body_item = ",{}"

        self._running = False

    def update(self):
        """
        Prompt every element for any updates to the status bar.

        It does this by giving each element a turn at appending blocks to an
        `output` list that it passes as the first argument to the element's
        `on_update` method. This is done in the order that the elements were
        given to the updater at initialization.

        It also determines if any element has intervals that have come due and
        should be triggered by calling the element's `on_interval` method with
        the options given during `set_interval`.

        After all this has been done, a body item, as described in the "BODY"
        section of swaybar-protocol(7), is constructed and sent immediately to
        stdout.
        """

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
                    element.on_interval(options)
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
        send_line(json.dumps(self._header))
        send_line(self._body_start)

        self._running = True

        while self.running():
            self.update()
            time.sleep(self.interval)
