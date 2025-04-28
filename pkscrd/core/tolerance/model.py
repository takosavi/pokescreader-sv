import enum
from typing import TypeAlias, Callable, Any


class FatalError(Exception):
    """致命的な問題が発生したときに処理を止めるための例外."""


class ToleranceEvent(enum.Enum):
    """Tolerance が発行するイベント."""

    ERROR_COUNT_WARNING = enum.auto()
    ERROR_COUNT_FATAL = enum.auto()
    RECOVERY_FAILED = enum.auto()


ToleranceCallback: TypeAlias = Callable[[ToleranceEvent], Any]
