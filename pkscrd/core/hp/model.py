import dataclasses
import enum


class HpScene(enum.Enum):
    """HP が表示されるシーン分類"""

    COMMAND = enum.auto()
    MOVE = enum.auto()


@dataclasses.dataclass(frozen=True)
class VisibleHp:
    """値を認識できる HP"""

    current: int
    max: int
