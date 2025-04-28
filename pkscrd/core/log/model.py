from __future__ import annotations

import dataclasses
import enum


class LogType(enum.Enum):
    GENERAL = enum.auto()
    BATTLE = enum.auto()


@dataclasses.dataclass(frozen=True)
class Log:
    type: LogType
    lines: list[str]
