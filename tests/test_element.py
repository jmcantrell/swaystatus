from pathlib import Path
from random import choice, randint
from string import ascii_letters
from subprocess import Popen
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import Mock, patch

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, ElementRegistry, UpdateHandler
from swaystatus.logging import logger
from tests.fake import fake_click_event


class TestElement(TestCase):
    def test_blocks_must_be_implemented(self) -> None:
        """Test that the blocks method must be implemented."""
        with self.assertRaises(NotImplementedError):
            BaseElement().blocks()

    def test_click_unhandled(self) -> None:
        """Test that a click event with no handler does nothing."""

        class Element(BaseElement):
            pass

        self.assertFalse(Element().on_click(fake_click_event(button=1)))

    def test_click_handler_method(self) -> None:
        """Test that a click handler can be defined as a method."""

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent): ...
            def on_click_2(self, click_event: ClickEvent): ...
            def on_click_3(self, click_event: ClickEvent): ...

        for button in range(1, 4):
            with self.subTest(button=button), patch.object(Element, f"on_click_{button}") as handler:
                click_event = fake_click_event(button=button)
                Element().on_click(click_event)
                handler.assert_called_once_with(click_event)

    def test_click_handler_init_function(self) -> None:
        """Test that click handler functions can be set at initialization."""

        class Element(BaseElement):
            name = "test"

        for button in range(1, 4):
            with self.subTest(button=button):
                handler = Mock()
                click_event = fake_click_event(button=button)
                element = Element(on_click={button: handler})
                element.on_click(click_event)
                handler.assert_called_once_with(element, click_event)

    def test_click_handler_init_shell_command(self) -> None:
        """Test that click handler shell commands can be set at initialization."""

        class Element(BaseElement):
            pass

        for button in range(1, 4):
            string = "".join(choice(ascii_letters) for i in range(randint(10, 30)))
            cases = {
                "echo ~": str(Path.home()),  # shell tilde expansion
                "echo $foo": string,  # environment variables passed
                "echo ${button}": str(button),  # environment variables from click event
            }
            env = {"foo": string}
            click_event = fake_click_event(button=button)
            for command, output in cases.items():
                with self.subTest(button=button, command=command), TemporaryDirectory() as temp_dir:
                    stdout_file = Path(temp_dir) / "stdout"
                    handler = f"{command} >{stdout_file}"  # shell redirection
                    element = Element(on_click={button: handler}, env=env)
                    updater = element.on_click(click_event)
                    assert callable(updater)
                    self.assertTrue(updater())
                    self.assertEqual(stdout_file.read_text().strip(), output)

    def test_click_handler_result_none(self) -> None:
        """Test that a click handler returning nothing does not trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> None:
                pass

        self.assertFalse(Element().on_click(fake_click_event(button=1)))

    def test_click_handler_result_update(self) -> None:
        """Test that a click handler can request a status update."""
        update = bool(randint(0, 1))

        class Element(BaseElement):
            def on_click_1(self, *args) -> bool:
                return update

        self.assertIs(Element().on_click(fake_click_event(button=1)), update)

    def test_click_handler_result_update_handler(self) -> None:
        """Test that a click handler can request a deferred status update."""
        update = bool(randint(0, 1))

        def update_handler_inner() -> bool:
            return update

        class Element(BaseElement):
            def on_click_1(self, *args) -> UpdateHandler:
                return update_handler_inner

        update_handler = Element().on_click(fake_click_event(button=1))
        assert callable(update_handler)
        self.assertEqual(update_handler(), update)

    def test_click_handler_result_update_handler_raises(self) -> None:
        """Test that an exception raised during an update handler is caught and logged."""

        def update_handler_inner() -> bool:
            raise Exception

        class Element(BaseElement):
            def on_click_1(self, *args) -> UpdateHandler:
                return update_handler_inner

        update_handler = Element().on_click(fake_click_event(button=1))
        assert callable(update_handler)
        with self.assertLogs(logger, level="ERROR") as log:
            self.assertEqual(update_handler(), False)
        self.assertIn("unhandled exception in update handler", log.output[0])

    def test_click_handler_result_process_success(self) -> None:
        """Test that a successful process will trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen("true")

        update_handler = Element().on_click(fake_click_event(button=1))
        assert callable(update_handler)
        self.assertTrue(update_handler())

    def test_click_handler_result_process_failure(self) -> None:
        """Test that a failed process will not trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen("false")

        update_handler = Element().on_click(fake_click_event(button=1))
        assert callable(update_handler)
        self.assertFalse(update_handler())

    def test_click_handler_result_shell_command_success(self) -> None:
        """Test that a successful shell command will trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> str:
                return "true"

            def on_click_2(self, *args) -> list[str]:
                return ["true"]

        element = Element()
        for button in [1, 2]:
            with self.subTest(button=button):
                update_handler = element.on_click(fake_click_event(button=button))
                assert callable(update_handler)
                self.assertTrue(update_handler())

    def test_click_handler_result_shell_command_failure(self) -> None:
        """Test that a failed shell command will not trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> str:
                return "false"

            def on_click_2(self, *args) -> list[str]:
                return ["false"]

        element = Element()
        for button in [1, 2]:
            with self.subTest(button=button):
                update_handler = element.on_click(fake_click_event(button=button))
                assert callable(update_handler)
                self.assertFalse(update_handler())


class TestElementRegistry(TestCase):
    def setUp(self) -> None:
        class Element1(BaseElement):
            name = "test1"

        class Element2(BaseElement):
            name = "test2"

        self.element1 = Element1()
        self.element1a = Element1(instance="a")
        self.element1b = Element1(instance="b")
        self.element2a = Element2(instance="a")
        self.element2b = Element2(instance="b")
        self.element_registry = ElementRegistry(
            [
                self.element1,
                self.element1a,
                self.element1b,
                self.element2a,
                self.element2b,
            ]
        )

    def test_get(self) -> None:
        """Test that an element can be retrieved."""
        self.assertIs(self.element_registry.get("test1"), self.element1)
        with self.assertRaises(KeyError):
            self.element_registry.get("bogus", None)

    def test_get_instance(self) -> None:
        """Test that an element instance can be retrieved."""
        self.assertIs(self.element_registry.get("test1", "a"), self.element1a)
        self.assertIs(self.element_registry.get("test1", "b"), self.element1b)
        with self.assertRaises(KeyError):
            self.element_registry.get("test2", "c")
        with self.assertRaises(KeyError):
            self.element_registry.get("bogus", "a")

    def test_get_instance_fallback(self) -> None:
        """Test that a non-existent instance falls back to an existing element with the same name."""
        self.assertIs(self.element_registry.get("test1", "c"), self.element1)
        with self.assertRaises(KeyError):
            self.element_registry.get("test2", None)


if __name__ == "__main__":
    main()
