from typing import Optional
from unittest.mock import NonCallableMock

import pytest

from pkscrd.core.cursor.model import Cursor, PokemonCursorContent, PokemonCursorScene
from pkscrd.core.hp.model import VisibleHp
from pkscrd.core.move.model import Pp, Move, Effectiveness
from pkscrd.core.notification.model import (
    AllyHpNotification,
    CommandCursorNotification,
    LogNotification,
    MoveCursorNotification,
    MovesNotification,
    Notification,
    OpponentHpNotification,
    PokemonCursorNotification,
    SceneChangeNotification,
    ScreenshotNotification,
    SelectionCompleteButtonNotification,
    SelectionItem,
    SelectionNotification,
    TeamNotification,
    TeamDirection,
    TeraTypeNotification,
    UnknownCursorNotification,
)
from pkscrd.core.notification.service.messenger import (
    AllyHpFormat,
    AllyHpFormatter,
    Messenger,
)
from pkscrd.core.pokemon.model import PokemonId
from pkscrd.core.pokemon.repos import load_pokemons
from pkscrd.core.pokemon.service import PokemonMapper
from pkscrd.core.scene.model import SceneChange
from pkscrd.core.terastal.model import TeraType


class TestAllyHpFormatter:

    @pytest.mark.parametrize("hp", (None, VisibleHp(1, 0), VisibleHp(0, 0)))
    def test_値がないか分母が0のとき_Noneを返す(self, hp: Optional[VisibleHp]):
        formatter = AllyHpFormatter()
        assert formatter.format(hp) is None

    def test_値がゼロのときは簡潔なメッセージを返す(self):
        formatter = AllyHpFormatter()
        assert formatter.format(VisibleHp(0, 1)) == "ゼロ"

    _CASES = {
        "値だけ": (AllyHpFormat.NUMERATOR, VisibleHp(84, 167), "84"),
        "割合だけ": (AllyHpFormat.RATIO, VisibleHp(84, 167), "50%"),
        "値と割合": (AllyHpFormat.BOTH, VisibleHp(84, 167), "84、50%"),
    }

    @pytest.mark.parametrize(
        ("fmt", "hp", "expected"),
        _CASES.values(),
        ids=_CASES.keys(),
    )
    def test_format(self, fmt: AllyHpFormat, hp: Optional[VisibleHp], expected: str):
        formatter = AllyHpFormatter(fmt)
        assert formatter.format(hp) == expected


class TestMessenger:

    @pytest.fixture
    def sut(self) -> Messenger:
        ally_hp_formatter = NonCallableMock(AllyHpFormatter)
        ally_hp_formatter.format.side_effect = lambda v: (
            f"<{v.current}/{v.max}>" if v else None
        )
        return Messenger(ally_hp_formatter, PokemonMapper(load_pokemons()))

    _CASES = {
        "シーン遷移: 選出開始": (
            SceneChangeNotification(change=SceneChange.SELECTION_START),
            "選出開始",
        ),
        "シーン遷移: 選出終了": (
            SceneChangeNotification(change=SceneChange.SELECTION_COMPLETE),
            "選出終了",
        ),
        "シーン遷移: 指示開始": (
            SceneChangeNotification(change=SceneChange.COMMAND_START),
            "指示開始",
        ),
        "チーム: 味方, 未認識": (
            TeamNotification(direction=TeamDirection.ALLY, team=[]),
            "味方チームが認識されていません",
        ),
        "チーム: 味方, タイプなし": (
            TeamNotification(
                direction=TeamDirection.ALLY,
                team=[PokemonId(4, 0), PokemonId(892, 0)],
            ),
            "味方チーム。ヒトカゲ。ウーラオス",
        ),
        "チーム: 相手, タイプあり": (
            TeamNotification(
                direction=TeamDirection.OPPONENT,
                team=[PokemonId(4, 0), PokemonId(892, 0)],
                with_types=True,
            ),
            "相手チーム。ヒトカゲ、ほのお。ウーラオス、かくとうみずまたはかくとうあく",
        ),
        "選出: 選出なし": (SelectionNotification(items=[]), "選出されていません"),
        "選出: 選出あり": (
            SelectionNotification(
                items=[
                    None,
                    SelectionItem(index_in_team=0),
                    SelectionItem(index_in_team=1, pokemon_id=PokemonId(99999999, 99)),
                    SelectionItem(index_in_team=2, pokemon_id=PokemonId(1000, 0)),
                ]
            ),
            "選出。認識不可。1匹目のポケモン。2匹目のポケモン。サーフゴー",
        ),
        "味方 HP: 認識不可": (
            AllyHpNotification(value=None),
            "味方エイチピーが読み込めていません",
        ),
        "味方 HP: 認識可": (
            AllyHpNotification(value=VisibleHp(current=12, max=34)),
            "味方エイチピー<12/34>",
        ),
        "相手 HP: 認識不可": (
            OpponentHpNotification(ratio=None),
            "相手エイチピーが読み込めていません",
        ),
        "相手 HP: 認識可": (OpponentHpNotification(ratio=0.999), "相手エイチピー99%"),
        "技一覧: 認識不可": (MovesNotification(items=None), "技が読み込めませんでした"),
        "技一覧: 抜群, 普通, 相性なし, 認識不可": (
            MovesNotification(
                items=(
                    Move(
                        name="ムーンフォース",
                        effectiveness=Effectiveness.SUPER_EFFECTIVE,
                        pp=Pp(current=1, max=15),
                    ),
                    Move(
                        name="シャドーボール",
                        effectiveness=Effectiveness.EFFECTIVE,
                        pp=None,
                    ),
                    Move(name="みがわり", effectiveness=None, pp=Pp(current=2, max=10)),
                    None,
                ),
            ),
            "技。ムーンフォース、抜群、1。シャドーボール、普通。みがわり、2。認識不可",
        ),
        "技一覧: いまひとつ, 無効": (
            MovesNotification(
                items=(
                    Move(
                        name="どくづき",
                        effectiveness=Effectiveness.NOT_VERY_EFFECTIVE,
                        pp=None,
                    ),
                    Move(
                        name="からげんき",
                        effectiveness=Effectiveness.NO_EFFECT,
                        pp=None,
                    ),
                ),
            ),
            "技。どくづき、いまひとつ。からげんき、無効",
        ),
        "ログ": (
            LogNotification(lines=["Flutter Maneの", "ムーンフォース!"]),
            "フルッテア・マネの、ムーンフォース!",
        ),
        "スクリーンショット保存: 失敗": (
            ScreenshotNotification(succeeded=False),
            "スクリーンショットを保存できませんでした",
        ),
        "スクリーンショット保存: 成功": (
            ScreenshotNotification(succeeded=True),
            "スクリーンショットを保存しました",
        ),
        "ポケモンカーソル: 認識不可": (
            PokemonCursorNotification(scene=PokemonCursorScene.SELECTION, cursor=None),
            "ポケモンカーソルを認識できませんでした",
        ),
        "ポケモンカーソル: 選出画面, ID なし, HP なし, サブメニューなし": (
            PokemonCursorNotification(
                scene=PokemonCursorScene.SELECTION,
                cursor=Cursor(index=0, content=PokemonCursorContent()),
            ),
            "1匹目",
        ),
        "ポケモンカーソル: 選出画面, ID あり, HP あり, サブメニューテキストなし": (
            PokemonCursorNotification(
                scene=PokemonCursorScene.SELECTION,
                cursor=Cursor(
                    index=1,
                    content=PokemonCursorContent(
                        pokemon_id=PokemonId(1, 0),
                        hp=VisibleHp(current=123, max=456),
                        submenu_cursor=Cursor(index=0, content=None),
                    ),
                ),
            ),
            "2匹目、フシギダネ。メニュー1番目",
        ),
        "ポケモンカーソル: 選出画面, サブメニューテキストあり": (
            PokemonCursorNotification(
                scene=PokemonCursorScene.SELECTION,
                cursor=Cursor(
                    index=2,
                    content=PokemonCursorContent(
                        submenu_cursor=Cursor(index=1, content="テキスト"),
                    ),
                ),
            ),
            "3匹目。メニュー2番目、テキスト",
        ),
        "ポケモンカーソル: ポケモン選択画面, ID あり, HP あり, サブメニューテキストあり": (
            PokemonCursorNotification(
                scene=PokemonCursorScene.COMMAND_POKEMON,
                cursor=Cursor(
                    index=3,
                    content=PokemonCursorContent(
                        pokemon_id=PokemonId(4, 0),
                        hp=VisibleHp(current=123, max=456),
                        submenu_cursor=Cursor(index=0, content=None),
                    ),
                ),
            ),
            "4匹目、ヒトカゲ、エイチピー<123/456>。メニュー1番目",
        ),
        "選出完了ボタン": (SelectionCompleteButtonNotification(), "完了ボタン"),
        "指示カーソル: 認識不可": (
            CommandCursorNotification(cursor=None),
            "指示カーソルを認識できませんでした",
        ),
        "指示カーソル: 認識可": (
            CommandCursorNotification(cursor=Cursor(index=0, content=None)),
            "指示1番目",
        ),
        "技カーソル: 認識不可": (
            MoveCursorNotification(cursor=None),
            "技カーソルを認識できませんでした",
        ),
        "技カーソル: インデックスだけ": (
            MoveCursorNotification(cursor=Cursor(index=0, content=None)),
            "技1番目",
        ),
        "技カーソル: インデックスと内容": (
            MoveCursorNotification(
                cursor=Cursor(
                    index=0,
                    content=Move(
                        name="きょじゅうざん",
                        effectiveness=Effectiveness.NOT_VERY_EFFECTIVE,
                        pp=Pp(current=5, max=8),
                    ),
                ),
            ),
            "技1番目、きょじゅうざん、いまひとつ、5",
        ),
        "非対応カーソル": (
            UnknownCursorNotification(),
            "カーソルを認識できない画面です",
        ),
        "テラスタイプ: 副候補なし": (
            TeraTypeNotification(primary=TeraType.NORMAL),
            "テラスタイプ、ノーマル",
        ),
        "テラスタイプ: 副候補あり1": (
            TeraTypeNotification(
                primary=TeraType.FIRE,
                possible=[
                    TeraType.STELLA,
                    TeraType.WATER,
                    TeraType.ELECTRIC,
                    TeraType.GRASS,
                    TeraType.ICE,
                ],
            ),
            "テラスタイプ、ほのお。もしかすると、ステラ、みず、でんき、くさ、こおり",
        ),
        "テラスタイプ: 副候補あり2": (
            TeraTypeNotification(
                primary=TeraType.FIGHTING,
                possible=[
                    TeraType.POISON,
                    TeraType.GROUND,
                    TeraType.FLYING,
                    TeraType.PSYCHIC,
                    TeraType.BUG,
                ],
            ),
            "テラスタイプ、かくとう。もしかすると、どく、じめん、ひこう、エスパー、むし",
        ),
        "テラスタイプ: 副候補あり3": (
            TeraTypeNotification(
                primary=TeraType.ROCK,
                possible=[
                    TeraType.GHOST,
                    TeraType.DRAGON,
                    TeraType.DARK,
                    TeraType.STEEL,
                    TeraType.FAIRY,
                ],
            ),
            "テラスタイプ、いわ。もしかすると、ゴースト、ドラゴン、あく、はがね、フェアリー",
        ),
    }

    @pytest.mark.parametrize(
        ("notification", "expected"),
        _CASES.values(),
        ids=_CASES.keys(),
    )
    def test_convert_to_text(
        self,
        sut: Messenger,
        notification: Notification,
        expected: str,
    ):
        assert sut.convert_to_text(notification) == expected

    def test_convert_to_text_想定外の内容でもエラーにならない(self, sut: Messenger):
        assert sut.convert_to_text(None) == "想定されていない発話です"  # type: ignore
