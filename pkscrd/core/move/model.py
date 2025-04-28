import dataclasses
import enum
from typing import Optional, TypeAlias


class Effectiveness(enum.Enum):
    SUPER_EFFECTIVE = enum.auto()
    EFFECTIVE = enum.auto()
    NOT_VERY_EFFECTIVE = enum.auto()
    NO_EFFECT = enum.auto()


@dataclasses.dataclass(frozen=True)
class Pp:
    """技 PP"""

    current: int
    max: int


@dataclasses.dataclass(frozen=True)
class Move:
    """技"""

    name: str
    effectiveness: Optional[Effectiveness] = None
    pp: Optional[Pp] = None
    selected: bool = False


Moves: TypeAlias = (
    tuple[Optional[Move]]
    | tuple[Optional[Move], Optional[Move]]
    | tuple[Optional[Move], Optional[Move], Optional[Move]]
    | tuple[Optional[Move], Optional[Move], Optional[Move], Optional[Move]]
)


class MoveScene(enum.Enum):
    COMMAND = enum.auto()
    POKEMON = enum.auto()
