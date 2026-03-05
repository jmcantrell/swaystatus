import os
from pathlib import Path

from swaystatus.env import environ_alter, environ_path, environ_paths, environ_update


class TestEnviron:
    cleanup_env_names: set[str]

    def cleanup_env(self, name: str) -> None:
        self.cleanup_env_names.add(name)

    def del_env(self, name: str) -> None:
        try:
            del os.environ[name]
        except KeyError:
            pass

    def get_env(self, name: str) -> str | None:
        self.cleanup_env(name)
        return os.environ.get(name)

    def set_env(self, name: str, value: str) -> None:
        self.cleanup_env(name)
        os.environ[name] = value

    def setup_method(self) -> None:
        self.cleanup_env_names = set()

    def teardown_method(self) -> None:
        for name in self.cleanup_env_names:
            self.del_env(name)


class TestEnvironPath(TestEnviron):
    def test_set(self) -> None:
        """Test that a path is returned if the environment variable is set."""
        self.set_env("foo", "file")
        assert environ_path("foo") == Path("file")

    def test_unset(self) -> None:
        """Test that nothing is returned if the environment variable is not set."""
        self.del_env("foo")
        assert environ_path("foo") is None


class TestEnvironPaths(TestEnviron):
    def test_set(self) -> None:
        """Test that a list of paths is returned if the environment variable is set."""
        self.set_env("foo", "dir1:dir2:dir3")
        assert environ_paths("foo") == [Path("dir1"), Path("dir2"), Path("dir3")]

    def test_unset(self) -> None:
        """Test that an empty list is returned if an environment variable is not set."""
        self.del_env("foo")
        assert environ_paths("foo") == []


class TestEnvironAlter(TestEnviron):
    def test_set(self) -> None:
        """Test that environment variables can be set in bulk."""
        self.del_env("foo")
        self.del_env("bar")
        environ_alter(dict(foo="a", bar="b"))
        assert self.get_env("foo") == "a"
        assert self.get_env("bar") == "b"

    def test_unset(self) -> None:
        """Test that environment variables can be unset in bulk."""
        self.set_env("foo", "a")
        self.set_env("bar", "b")
        environ_alter(dict(foo=None, bar=None))
        assert self.get_env("foo") is None
        assert self.get_env("bar") is None


class TestEnvironUpdate(TestEnviron):
    def test_set(self) -> None:
        """Test that keyword arguments are set in the environment."""
        self.del_env("foo")
        with environ_update(foo="test"):
            assert self.get_env("foo") == "test"
        assert self.get_env("foo") is None

    def test_unset(self) -> None:
        """Test that keyword arguments with `None` values are unset in the environment."""
        self.set_env("foo", "test")
        with environ_update(foo=None):
            assert self.get_env("foo") is None
        assert self.get_env("foo") == "test"

    def test_only(self) -> None:
        """Test that only the given changes are reverted."""
        self.del_env("foo")
        with environ_update(bar="a"):
            self.set_env("foo", "b")
        assert self.get_env("foo") == "b"
