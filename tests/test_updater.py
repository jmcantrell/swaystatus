import os
import json
import random
import pytest
from swaystatus.element import BaseElement
from swaystatus.updater import Updater

zero = 0.00001


@pytest.fixture
def updater_count(monkeypatch):
    def func(count):
        iterations = 0

        def count_iterations(self):
            nonlocal iterations
            if iterations < count:
                iterations += 1
                return True
            return False

        monkeypatch.setattr(Updater, "_running", count_iterations)

        return Updater

    return func


def test_updater_run(capfd, updater_count):
    class Foo(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("foo"))

    count = random.randint(5, 10)

    updater_count(count)([Foo()], interval=zero).run()

    captured = capfd.readouterr()
    lines = captured.out.strip().split(os.linesep)

    assert lines == [
        header,
        body_start,
        *[
            body_item.format(json.dumps([dict(full_text="foo")]))
            for _ in range(count)
        ],
    ]


def test_updater_no_blocks(capfd):
    class NoBlocks(BaseElement):
        def on_update(self, output):
            pass

    Updater([NoBlocks()], interval=zero).update()

    captured = capfd.readouterr()

    assert captured.out.strip() == body_item.format("[]")


def test_updater_multiple_blocks(capfd):
    texts = ["foo", "bar", "baz"]

    class MultipleBlocks(BaseElement):
        def on_update(self, output):
            output.extend([self.create_block(text) for text in texts])

    Updater([MultipleBlocks()], interval=zero).update()

    captured = capfd.readouterr()

    assert captured.out.strip() == body_item.format(
        json.dumps([dict(full_text=text) for text in texts])
    )


def test_updater_element_intervals(capfd, updater_count):
    class Intervals(BaseElement):
        def __init__(self):
            super().__init__()
            self.text = "initial"
            self.set_interval(0.1, options="foo")
            self.set_interval(0.2, options="bar")

        def on_interval(self, options):
            self.text = options

        def on_update(self, output):
            output.append(self.create_block(self.text))

    updater_count(3)([Intervals()], interval=0.1).run()

    captured = capfd.readouterr()
    lines = captured.out.strip().split(os.linesep)

    assert lines == [
        header,
        body_start,
        body_item.format(json.dumps([dict(full_text="initial")])),
        body_item.format(json.dumps([dict(full_text="foo")])),
        body_item.format(json.dumps([dict(full_text="bar")])),
    ]
