from subprocess import Popen
from typing import Callable

from .click_event import ClickEvent

type ShellCommand = str | list[str]
type ClickHandlerResult = Popen | Callable[[], bool] | bool | None
type ClickHandler[E] = ShellCommand | Callable[[E, ClickEvent], ShellCommand | ClickHandlerResult]
