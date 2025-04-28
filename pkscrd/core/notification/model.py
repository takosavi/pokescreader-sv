import dataclasses
import enum
from typing import Optional, TypeAlias

from pkscrd.core.cursor.model import (
    CommandCursor,
    Cursor,
    PokemonCursor,
    PokemonCursorScene,
)
from pkscrd.core.hp.model import VisibleHp
from pkscrd.core.move.model import Move, Moves
from pkscrd.core.pokemon.model import PokemonId, Team
from pkscrd.core.scene.model import SceneChange
from pkscrd.core.terastal.model import TeraType


@dataclasses.dataclass(frozen=True)
class SceneChangeNotification:
    """シーン遷移通知"""

    change: SceneChange


class TeamDirection(enum.Enum):
    """チームの方向 (味方 or 相手)"""

    ALLY = enum.auto()
    OPPONENT = enum.auto()


@dataclasses.dataclass(frozen=True)
class TeamNotification:
    """チーム通知"""

    direction: TeamDirection
    team: Team
    with_types: bool = False


@dataclasses.dataclass(frozen=True)
class SelectionItem:
    index_in_team: int
    pokemon_id: Optional[PokemonId] = None


@dataclasses.dataclass(frozen=True)
class SelectionNotification:
    """選出通知"""

    items: list[Optional[SelectionItem]]


@dataclasses.dataclass(frozen=True)
class AllyHpNotification:
    """味方 HP 通知"""

    value: Optional[VisibleHp]


@dataclasses.dataclass(frozen=True)
class OpponentHpNotification:
    """相手 HP 通知"""

    ratio: Optional[float]


@dataclasses.dataclass(frozen=True)
class MovesNotification:
    """技通知"""

    items: Optional[Moves]


@dataclasses.dataclass(frozen=True)
class LogNotification:
    """ログメッセージ通知"""

    lines: list[str]


@dataclasses.dataclass(frozen=True)
class ScreenshotNotification:
    """スクリーンショット保存通知"""

    succeeded: bool


@dataclasses.dataclass(frozen=True)
class PokemonCursorNotification:
    """ポケモンカーソル通知"""

    scene: PokemonCursorScene
    cursor: Optional[PokemonCursor]


@dataclasses.dataclass(frozen=True)
class SelectionCompleteButtonNotification:
    """選出完了ボタン通知"""


@dataclasses.dataclass(frozen=True)
class CommandCursorNotification:
    """指示カーソル通知"""

    cursor: Optional[CommandCursor]


@dataclasses.dataclass(frozen=True)
class MoveCursorNotification:
    """技カーソル通知"""

    cursor: Optional[Cursor[Optional[Move]]]


@dataclasses.dataclass(frozen=True)
class UnknownCursorNotification:
    """不明なカーソル通知"""


@dataclasses.dataclass(frozen=True)
class TeraTypeNotification:
    """テラスタイプ通知"""

    primary: TeraType
    possible: list[TeraType] = dataclasses.field(default_factory=list)


CursorNotification: TypeAlias = (
    PokemonCursorNotification
    | SelectionCompleteButtonNotification
    | CommandCursorNotification
    | MoveCursorNotification
    | UnknownCursorNotification
)
Notification: TypeAlias = (
    SceneChangeNotification
    | TeamNotification
    | SelectionNotification
    | AllyHpNotification
    | OpponentHpNotification
    | MovesNotification
    | LogNotification
    | ScreenshotNotification
    | CursorNotification
    | TeraTypeNotification
)
