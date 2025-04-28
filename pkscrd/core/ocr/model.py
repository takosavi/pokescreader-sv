import dataclasses
import enum


class TextColor(enum.Enum):
    """認識するテキストの色"""

    WHITE = enum.auto()
    WHITE_AND_YELLOW = enum.auto()
    WHITE_AND_YELLOW_AND_RED = enum.auto()
    GREY = enum.auto()
    BLACK = enum.auto()


class LineContentType(enum.Enum):
    """行の内容種別"""

    MOVE_NAME = enum.auto()


@dataclasses.dataclass(frozen=True)
class LogFormat:
    """ログの形式"""

    color: TextColor
    line_height: int
    line_interval: int


@dataclasses.dataclass(frozen=True)
class Fraction:
    """分数表現."""

    numerator: int
    denominator: int
