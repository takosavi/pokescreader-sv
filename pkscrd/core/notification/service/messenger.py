import enum
import math
from typing import Optional

from loguru import logger
from romajiphonem import phonemize

from pkscrd.core.cursor.model import PokemonCursorScene
from pkscrd.core.hp.model import VisibleHp
from pkscrd.core.move.model import Move, Effectiveness
from pkscrd.core.notification.model import (
    AllyHpNotification,
    CommandCursorNotification,
    LogNotification,
    MoveCursorNotification,
    MovesNotification,
    Notification,
    OpponentHpNotification,
    PokemonCursorNotification,
    ScreenshotNotification,
    SelectionCompleteButtonNotification,
    SelectionItem,
    SelectionNotification,
    TeamDirection,
    TeamNotification,
    TeraTypeNotification,
    UnknownCursorNotification,
    SceneChangeNotification,
)
from pkscrd.core.pokemon.model import Team, Type
from pkscrd.core.pokemon.service import PokemonMapper
from pkscrd.core.scene.model import SceneChange
from pkscrd.core.terastal.model import TeraType


class AllyHpFormat(enum.StrEnum):
    """相手 HP 読み上げフォーマット種別."""

    NUMERATOR = "numerator"
    RATIO = "ratio"
    BOTH = "both"


class AllyHpFormatter:
    """相手 HP 読み上げ形式へ変換する."""

    def __init__(self, fmt: AllyHpFormat = AllyHpFormat.BOTH):
        self._format = fmt

    def format(self, hp: Optional[VisibleHp]) -> Optional[str]:
        if not hp or not hp.max:
            return None

        if not hp.current:
            return "ゼロ"

        if self._format is AllyHpFormat.NUMERATOR:
            return str(hp.current)

        percentage = math.floor((hp.current / hp.max) * 100)
        if self._format is AllyHpFormat.RATIO:
            return f"{percentage}%"

        assert self._format is AllyHpFormat.BOTH
        return f"{hp.current}、{percentage}%"


class Messenger:
    """通知をテキストに変換する."""

    def __init__(
        self,
        ally_hp_formatter: AllyHpFormatter,
        pokemon_mapper: PokemonMapper,
    ) -> None:
        self._ally_hp_formatter = ally_hp_formatter
        self._pokemon_mapper = pokemon_mapper

    def convert_to_text(self, notification: Notification) -> str:
        match notification:
            case SceneChangeNotification(SceneChange.SELECTION_START):
                return "選出開始"

            case SceneChangeNotification(SceneChange.SELECTION_COMPLETE):
                return "選出終了"

            case SceneChangeNotification(SceneChange.COMMAND_START):
                return "指示開始"

            case TeamNotification(direction=dir_, team=team, with_types=with_types):
                label = _TEAM_DIRECTION_TO_TEXT[dir_]
                if not team:
                    return f"{label}が認識されていません"
                return f"{label}。{self._convert_team(team, with_types)}"

            case SelectionNotification(items=items):
                if not items:
                    return "選出されていません"
                return "選出。" + "。".join(map(self._convert_selection_item, items))

            case AllyHpNotification(value=value):
                converted = self._ally_hp_formatter.format(value)
                if not converted:
                    return "味方エイチピーが読み込めていません"
                return f"味方エイチピー{converted}"

            case OpponentHpNotification(ratio=ratio):
                if ratio is None:
                    return "相手エイチピーが読み込めていません"
                return f"相手エイチピー{math.floor(ratio * 100)}%"

            case MovesNotification(items=items):
                if not items:
                    return "技が読み込めませんでした"
                return "技。" + "。".join(map(_convert_move_item, items))

            case LogNotification(lines=lines):
                return "、".join(phonemize(line) for line in lines)

            case ScreenshotNotification(succeeded=succeeded):
                if succeeded:
                    return "スクリーンショットを保存しました"
                else:
                    return "スクリーンショットを保存できませんでした"

            case PokemonCursorNotification(scene=scene, cursor=cursor):
                if not cursor:
                    return "ポケモンカーソルを認識できませんでした"

                label = f"{cursor.index + 1}匹目"
                if cursor.content.pokemon_id and (
                    pokemon := self._pokemon_mapper.get(cursor.content.pokemon_id)
                ):
                    label = f"{label}、{pokemon.name}"
                if scene is PokemonCursorScene.COMMAND_POKEMON and (
                    hp := self._ally_hp_formatter.format(cursor.content.hp)
                ):
                    label = f"{label}、エイチピー{hp}"

                menu_label: Optional[str] = None
                if cursor.content.submenu_cursor:
                    menu_label = (
                        f"メニュー{cursor.content.submenu_cursor.index + 1}番目"
                    )
                    if cursor.content.submenu_cursor.content:
                        menu_label = (
                            f"{menu_label}、{cursor.content.submenu_cursor.content}"
                        )

                return "。".join(filter(None, (label, menu_label)))

            case SelectionCompleteButtonNotification():
                return "完了ボタン"

            case CommandCursorNotification(cursor=cursor):
                if not cursor:
                    return "指示カーソルを認識できませんでした"
                return f"指示{cursor.index + 1}番目"

            case MoveCursorNotification(cursor=cursor):
                if not cursor:
                    return "技カーソルを認識できませんでした"
                index = f"技{cursor.index + 1}番目"
                if not cursor.content:
                    return index
                return f"{index}、{_convert_move_item(cursor.content)}"

            case UnknownCursorNotification():
                return "カーソルを認識できない画面です"

            case TeraTypeNotification(primary=primary, possible=possible):
                message = f"テラスタイプ、{_TERA_TYPE_MAP[primary]}"
                if possible:
                    message += "。もしかすると、"
                    message += "、".join(_TERA_TYPE_MAP[item] for item in possible)
                return message

            case _:
                logger.warning("Unsupported notification: {}", notification)
                return "想定されていない発話です"

    def _convert_team(self, team: Team, with_types: bool = False) -> str:
        return "。".join(
            (
                (
                    (
                        pokemon.name
                        + "、"
                        + "または".join(
                            "".join(_TYPE_TO_TEXT[type_] for type_ in typeset)
                            for typeset in pokemon.typesets
                        )
                    )
                    if with_types
                    else pokemon.name
                )
                if (pokemon := (self._pokemon_mapper.get(id) if id else None))
                else "認識不可"
            )
            for id in team
        )

    def _convert_selection_item(self, item: Optional[SelectionItem]) -> str:
        if not item:
            return "認識不可"
        if item.pokemon_id and (pokemon := self._pokemon_mapper.get(item.pokemon_id)):
            return pokemon.name
        return f"{item.index_in_team + 1}匹目のポケモン"


_TEAM_DIRECTION_TO_TEXT = {
    TeamDirection.ALLY: "味方チーム",
    TeamDirection.OPPONENT: "相手チーム",
}
_TYPE_TO_TEXT = {
    Type.NORMAL: "ノーマル",
    Type.FIRE: "ほのお",
    Type.WATER: "みず",
    Type.ELECTRIC: "でんき",
    Type.GRASS: "くさ",
    Type.ICE: "こおり",
    Type.FIGHTING: "かくとう",
    Type.POISON: "どく",
    Type.GROUND: "じめん",
    Type.FLYING: "ひこう",
    Type.PSYCHIC: "エスパー",
    Type.BUG: "むし",
    Type.ROCK: "いわ",
    Type.GHOST: "ゴースト",
    Type.DRAGON: "ドラゴン",
    Type.DARK: "あく",
    Type.STEEL: "はがね",
    Type.FAIRY: "フェアリー",
    Type.UNKNOWN: "不明",
}
_EFFECTIVENESS_MAP = {
    Effectiveness.SUPER_EFFECTIVE: "抜群",
    Effectiveness.EFFECTIVE: "普通",
    Effectiveness.NOT_VERY_EFFECTIVE: "いまひとつ",
    Effectiveness.NO_EFFECT: "無効",
}
_TERA_TYPE_MAP = {
    TeraType.NORMAL: "ノーマル",
    TeraType.FIRE: "ほのお",
    TeraType.WATER: "みず",
    TeraType.ELECTRIC: "でんき",
    TeraType.GRASS: "くさ",
    TeraType.ICE: "こおり",
    TeraType.FIGHTING: "かくとう",
    TeraType.POISON: "どく",
    TeraType.GROUND: "じめん",
    TeraType.FLYING: "ひこう",
    TeraType.PSYCHIC: "エスパー",
    TeraType.BUG: "むし",
    TeraType.ROCK: "いわ",
    TeraType.GHOST: "ゴースト",
    TeraType.DRAGON: "ドラゴン",
    TeraType.DARK: "あく",
    TeraType.STEEL: "はがね",
    TeraType.FAIRY: "フェアリー",
    TeraType.STELLA: "ステラ",
}


def _convert_move_item(item: Optional[Move]) -> str:
    if not item:
        return "認識不可"

    items = filter(
        None,
        (
            item.name,
            _EFFECTIVENESS_MAP.get(item.effectiveness) if item.effectiveness else None,
            str(item.pp.current) if item.pp else None,
        ),
    )
    return "、".join(items)
