from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

context_var: ContextVar[str | None] = ContextVar("context", default=None)


@contextmanager
def context(label: str) -> Generator:
    with context_var.set(label):
        yield


@contextmanager
def context_group(label: str) -> Generator[str]:
    group_id = str(uuid4())
    with context(f"{label} {group_id}"):
        yield group_id
