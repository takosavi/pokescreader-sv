import dataclasses
import enum
from typing import Generic, Optional, TypeVar

from pkscrd.core.hp.model import VisibleHp
from pkscrd.core.pokemon.model import PokemonId

_T = TypeVar("_T")


@dataclasses.dataclass(frozen=True)
class Cursor(Generic[_T]):
    index: int
    content: _T


type TextCursor = Cursor[Optional[str]]


class Command(enum.Enum):
    BATTLE = enum.auto()
    POKEMON = enum.auto()
    BAG = enum.auto()
    RUN = enum.auto()


type CommandCursor = Cursor[None]


class PokemonCursorScene(enum.Enum):
    SELECTION = enum.auto()
    COMMAND_POKEMON = enum.auto()


@dataclasses.dataclass(frozen=True)
class PokemonCursorContent:
    pokemon_id: Optional[PokemonId] = None
    hp: Optional[VisibleHp] = None
    submenu_cursor: Optional[TextCursor] = None


type PokemonCursor = Cursor[PokemonCursorContent]
