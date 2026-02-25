from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

context_var: ContextVar[str | None] = ContextVar("context", default=None)


@contextmanager
def context(label: str) -> Iterator:
    with context_var.set(label):
        yield


@contextmanager
def context_group(label: str) -> Iterator[str]:
    group_id = str(uuid4())
    with context(f"{label} {group_id}"):
        yield group_id
