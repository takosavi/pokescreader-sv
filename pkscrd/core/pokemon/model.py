import enum
import dataclasses
from typing import NamedTuple, Optional, TypeAlias


class Type(enum.StrEnum):
    """ポケモンのタイプ."""

    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"
    UNKNOWN = "unknown"


class PokemonId(NamedTuple):
    """ポケモン ID"""

    pokedex_number: int
    form_index: int


@dataclasses.dataclass(frozen=True)
class Pokemon:
    """ポケモン情報. 特に選出画面上での情報を扱う."""

    id: PokemonId
    name: str
    typesets: list[tuple[Type] | tuple[Type, Type]]


Team: TypeAlias = list[Optional[PokemonId]]
