import os
import json
import random
import pytest
from swaystatus.element import BaseElement
from swaystatus.updater import Updater

brief_interval = 0.00001


@pytest.fixture
def updater_count(monkeypatch):
    """
    Create a patched updater class that will only send updates a requested
    number of times.
    """

    def func(count):
        iterations = 0

        def count_iterations(self):
            nonlocal iterations
            if iterations < count:
                iterations += 1
                return True
            return False

        monkeypatch.setattr(Updater, "running", count_iterations)

        return Updater

    return func


def test_updater_respects_option_click_events():
    """
    Ensure that the updater passes on our preference for click events.
    """

    assert Updater([], brief_interval, True)._header["click_events"]
    assert not Updater([], brief_interval, False)._header["click_events"]


def test_updater_start(capfd, updater_count):
    """
    Ensure that an updater will continuously emit blocks when started.
    """

    class Foo(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("foo"))

    count = random.randint(5, 10)

    updater = updater_count(count)([Foo()], brief_interval, False)
    updater.start()

    assert capfd.readouterr().out.strip().split(os.linesep) == [
        json.dumps(updater._header),
        updater._body_start,
    ] + ([updater._body_item.format(json.dumps([dict(full_text="foo")]))] * count)


def test_updater_no_blocks(capfd):
    """
    Ensure that if an element does not emit any blocks, none appear in the
    output.
    """

    class NoBlocks(BaseElement):
        def on_update(self, output):
            pass

    updater = Updater([NoBlocks()], brief_interval, False)
    updater.update()

    assert capfd.readouterr().out.strip() == updater._body_item.format("[]")


def test_updater_multiple_blocks(capfd):
    """
    Ensure that a single element is able to output multiple blocks.
    """

    texts = ["foo", "bar", "baz"]

    class MultipleBlocks(BaseElement):
        def on_update(self, output):
            output.extend([self.create_block(text) for text in texts])

    updater = Updater([MultipleBlocks()], brief_interval, False)
    updater.update()

    assert capfd.readouterr().out.strip() == updater._body_item.format(
        json.dumps([dict(full_text=text) for text in texts])
    )


def test_updater_multiple_elements(capfd):
    """
    Ensure that multiple elements output their blocks in the correct order.
    """

    class Foo(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("foo"))

    class Bar(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("bar"))

    updater = Updater([Foo(), Bar()], brief_interval, False)
    updater.update()

    assert capfd.readouterr().out.strip() == updater._body_item.format(
        json.dumps([dict(full_text="foo"), dict(full_text="bar")])
    )


def test_updater_element_intervals(capfd, updater_count):
    """
    Ensure that any intervals set are called when expected.
    """

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

    updater = updater_count(3)([Intervals()], 0.1, False)
    updater.start()

    assert capfd.readouterr().out.strip().split(os.linesep) == [
        json.dumps(updater._header),
        updater._body_start,
        updater._body_item.format(json.dumps([dict(full_text="initial")])),
        updater._body_item.format(json.dumps([dict(full_text="foo")])),
        updater._body_item.format(json.dumps([dict(full_text="bar")])),
    ]
