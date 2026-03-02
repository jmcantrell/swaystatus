import os
from pathlib import Path
from unittest import TestCase, main

from swaystatus.env import environ_alter, environ_path, environ_paths, environ_update


class TestEnviron(TestCase):
    def del_env(self, name: str) -> None:
        try:
            del os.environ[name]
        except KeyError:
            pass

    def cleanup_env(self, name: str) -> None:
        self.addCleanup(self.del_env, name)

    def get_env(self, name: str) -> str | None:
        self.cleanup_env(name)
        return os.environ.get(name)

    def set_env(self, name: str, value: str) -> None:
        self.cleanup_env(name)
        os.environ[name] = value


class TestEnvironPath(TestEnviron):
    def test_set(self) -> None:
        """Test that a path is returned if the environment variable is set."""
        name = "foo"
        path = Path("/path/to/file")
        self.set_env(name, str(path))
        self.assertEqual(environ_path(name), path)

    def test_unset(self) -> None:
        """Test that nothing is returned if the environment variable is not set."""
        name = "foo"
        self.del_env(name)
        self.assertIsNone(environ_path(name))


class TestEnvironPaths(TestEnviron):
    def test_set(self) -> None:
        """Test that a list of paths is returned if the environment variable is set."""
        name = "foo"
        paths = list(map(Path, ["file1", "file2", "file3"]))
        self.set_env(name, ":".join(map(str, paths)))
        self.assertListEqual(environ_paths(name), paths)

    def test_unset(self) -> None:
        """Test that an empty list is returned if an environment variable is not set."""
        name = "foo"
        self.del_env(name)
        self.assertListEqual(environ_paths(name), [])


class TestEnvironAlter(TestEnviron):
    def test_set(self) -> None:
        """Test that environment variables can be set."""
        name1 = "foo"
        name2 = "bar"
        value1 = "a"
        value2 = "b"
        self.del_env(name1)
        self.del_env(name2)
        environ_alter({name1: value1, name2: value2})
        self.assertEqual(self.get_env(name1), value1)
        self.assertEqual(self.get_env(name2), value2)

    def test_unset(self) -> None:
        """Test that environment variables can be unset."""
        name1 = "foo"
        name2 = "bar"
        value1 = "a"
        value2 = "b"
        self.set_env(name1, value1)
        self.set_env(name2, value2)
        environ_alter({name1: None, name2: None})
        self.assertIsNone(self.get_env(name1))
        self.assertIsNone(self.get_env(name2))


class TestEnvironUpdate(TestEnviron):
    def test_set(self) -> None:
        """Test that keyword arguments are set in the environment."""
        name = "foo"
        value = "test"
        self.del_env(name)
        with environ_update(**{name: value}):
            self.assertEqual(self.get_env(name), value)
        self.assertIsNone(self.get_env(name))

    def test_unset(self) -> None:
        """Test that keyword arguments with `None` values are unset in the environment."""
        name = "foo"
        value = "test"
        self.set_env(name, value)
        with environ_update(**{name: None}):
            self.assertIsNone(self.get_env(name))
        self.assertEqual(self.get_env(name), value)

    def test_only(self) -> None:
        """Test that only the given changes are reverted."""
        name = "foo"
        self.del_env(name)
        with environ_update(bar="a"):
            self.set_env(name, "b")
        self.assertEqual(self.get_env(name), "b")


if __name__ == "__main__":
    main()
