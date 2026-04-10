import contextlib
import os
from pathlib import Path
from unittest import TestCase, main

from swaystatus.env import environ_alter, environ_path, environ_paths, environ_update


class TestEnviron(TestCase):
    def setUp(self) -> None:
        self.cleanup_env_names: set[str] = set()

    def tearDown(self) -> None:
        for name in self.cleanup_env_names:
            self.del_env(name)

    def cleanup_env(self, name: str) -> None:
        self.cleanup_env_names.add(name)

    def del_env(self, name: str) -> None:
        with contextlib.suppress(KeyError):
            del os.environ[name]

    def get_env(self, name: str) -> str | None:
        self.cleanup_env(name)
        return os.environ.get(name)

    def set_env(self, name: str, value: str) -> None:
        self.cleanup_env(name)
        os.environ[name] = value


class TestEnvironPath(TestEnviron):
    def test_set(self) -> None:
        self.set_env("foo", "/path")
        self.assertEqual(environ_path("foo"), Path("/path"))

    def test_unset(self) -> None:
        self.del_env("foo")
        self.assertIsNone(environ_path("foo"))


class TestEnvironPaths(TestEnviron):
    def test_set(self) -> None:
        self.set_env("foo", "/path1:/path2:/path3")
        self.assertEqual(environ_paths("foo"), [Path("/path1"), Path("/path2"), Path("/path3")])

    def test_unset(self) -> None:
        self.del_env("foo")
        self.assertEqual(environ_paths("foo"), [])


class TestEnvironAlter(TestEnviron):
    def test_set(self) -> None:
        self.del_env("foo")
        self.del_env("bar")
        environ_alter({"foo": "a", "bar": "b"})
        self.assertEqual(self.get_env("foo"), "a")
        self.assertEqual(self.get_env("bar"), "b")

    def test_unset(self) -> None:
        self.set_env("foo", "a")
        self.set_env("bar", "b")
        environ_alter({"foo": None, "bar": None})
        self.assertIsNone(self.get_env("foo"))
        self.assertIsNone(self.get_env("bar"))

    def test_unset_not_exist(self) -> None:
        self.del_env("foo")
        self.del_env("bar")
        environ_alter({"foo": None, "bar": None})


class TestEnvironUpdate(TestEnviron):
    def test_set(self) -> None:
        self.del_env("foo")
        with environ_update(foo="test"):
            self.assertEqual(self.get_env("foo"), "test")
        self.assertIsNone(self.get_env("foo"))

    def test_unset(self) -> None:
        self.set_env("foo", "test")
        with environ_update(foo=None):
            self.assertIsNone(self.get_env("foo"))
        self.assertEqual(self.get_env("foo"), "test")

    def test_only(self) -> None:
        self.del_env("foo")
        with environ_update(bar="a"):
            self.set_env("foo", "b")
        self.assertEqual(self.get_env("foo"), "b")


if __name__ == "__main__":
    main()
