import dataclasses
import enum


class TeraType(enum.StrEnum):
    """テラスタイプ."""

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
    STELLA = "stella"


@dataclasses.dataclass
class TeraTypeDetection:
    type: TeraType
    color_score: float


@dataclasses.dataclass(frozen=True)
class TeraTypeDetectionSummary:
    primary: TeraTypeDetection
    possible: list[TeraTypeDetection] = dataclasses.field(default_factory=list)
