import asyncio
import math
from typing import Optional

import cv2.typing
import numpy as np

from cv2.typing import MatLike
from pnlib.pkmn import recognize_ally_pokemon_for_command

from pkscrd.core.hp.model import VisibleHp
from pkscrd.core.ocr.model import TextColor
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.pokemon.model import PokemonId, Team
from .model import (
    Cursor,
    PokemonCursor,
    PokemonCursorContent,
    PokemonCursorScene,
    TextCursor,
)


class TextCursorReader:
    """
    テキストだけの汎用メニューのカーソルを読み取る.
    """

    _PADDING = 10
    _HEIGHT = 80
    _ITEM_HEIGHT = _HEIGHT

    def __init__(self, ocr: OcrEngine):
        self._ocr = ocr

    async def read(
        self,
        image: MatLike,
        top: int,
        left: int,
        width: int,
    ) -> Optional[TextCursor]:
        """
        テキストメニューのカーソルを読み取る.
        周囲の白枠の座標・寸法を指定すること.
        """
        content_top = top + self._PADDING
        content_left = left + self._PADDING
        content_width = width - self._PADDING * 2
        index = _find_vertical_cursor_index(
            image,
            count=4,
            top=content_top + 60,
            height=10,
            left=content_left + 2,
            width=28,
            item_height=self._ITEM_HEIGHT,
        )
        if index is None:
            return None

        cursor_top = content_top + self._ITEM_HEIGHT * index
        text = await self._ocr.read_line(
            image[
                cursor_top + 23 : cursor_top + self._HEIGHT - 23,
                content_left + 30 : content_left + content_width - 30,
            ],
            TextColor.BLACK,
        )
        return Cursor(index=index, content=text)


class CommandCursorReader:
    """
    指示カーソル (「たたかう」「にげる」など) を読み取る.
    """

    _TOP = 780
    _HEIGHT = 84
    # _LEFT = 1480
    # _WIDTH = 400
    _ITEM_HEIGHT = _HEIGHT + 4

    def read(self, image: MatLike) -> Optional[Cursor[None]]:
        """
        指示カーソルを読み取る.
        """
        index = _find_vertical_cursor_index(
            image,
            count=3,
            top=self._TOP,
            height=self._HEIGHT - 2,
            left=1840,
            width=30,
            item_height=self._ITEM_HEIGHT,
        )
        if index is None:
            return None
        return Cursor(index=index, content=None)


class PokemonCursorReader:
    """
    選出画面やポケモン選択画面の, ポケモンカーソルを読み取る.
    """

    _SCALES = {
        PokemonCursorScene.SELECTION: (147, 108, 155, 650, 116, 338),
        PokemonCursorScene.COMMAND_POKEMON: (160, 120, 80, 520, 126, 427),
    }
    _DETECTION_HEIGHTS = {
        PokemonCursorScene.SELECTION: 10,
        PokemonCursorScene.COMMAND_POKEMON: 20,
    }
    _SUBMENU_LEFT_OFFSET = 10
    _SUBMENU_WIDTHS = {
        PokemonCursorScene.SELECTION: 338,
        PokemonCursorScene.COMMAND_POKEMON: 427,
    }

    def __init__(self, text_reader: TextCursorReader, ocr: OcrEngine):
        self._text_reader = text_reader
        self._ocr = ocr

    async def read(
        self,
        image: MatLike,
        scene: PokemonCursorScene,
        team: Optional[Team] = None,
    ) -> Optional[PokemonCursor]:
        """
        ポケモンカーソルを読み取る.

        ## 選出画面を読み取るとき
        `scene` に `PokemonCursorScene.SELECTION` を指定する.

        次の項目が読み取られる.
        - ポケモンの ID (`team` 指定時のみ)
        - サブメニュー

        `team` に味方チームを設定すると, ポケモンの ID をマッピングして設定する.
        これは, カーソルのインデックスが味方チームと一致する性質を利用している.

        ## ポケモン選択画面を読み取るとき
        `scene` に `PokemonCursorScene.COMMAND_POKEMON` を指定する.

        次の項目が読み取られる.
        - ポケモンの ID
        - HP
        - サブメニュー

        `team` に味方チームを設定すると, 味方チームに含まれるポケモンを優先的に検索し,
        処理が軽量になることがある.
        """
        top, height, left, width, item_height, submenu_width = self._SCALES[scene]
        index = _find_vertical_cursor_index(
            image,
            count=6,
            top=top + 90,
            height=self._DETECTION_HEIGHTS[scene],
            left=left + 2,
            width=18,
            item_height=item_height,
        )
        if index is None:
            return None

        hp, submenu_cursor = await asyncio.gather(
            (
                self._read_hp(image, scene, index)
                if scene is PokemonCursorScene.COMMAND_POKEMON
                else _none()
            ),
            self._text_reader.read(
                image,
                top=top + item_height * index,
                left=left + width + self._SUBMENU_LEFT_OFFSET,
                width=submenu_width,
            ),
        )

        pokemon_id: Optional[PokemonId] = None
        if scene is PokemonCursorScene.SELECTION:
            if team and index < len(team):
                pokemon_id = team[index]
        elif scene is PokemonCursorScene.COMMAND_POKEMON:
            if pokemon := recognize_ally_pokemon_for_command(
                image,
                index,
                preferred_ids=(tuple(id[0] for id in team if id) if team else None),
            ):
                pokemon_id = PokemonId(*pokemon)

        return Cursor(
            index=index,
            content=PokemonCursorContent(
                hp=hp,
                pokemon_id=pokemon_id,
                submenu_cursor=submenu_cursor,
            ),
        )

    async def _read_hp(
        self,
        image: MatLike,
        scene: PokemonCursorScene,
        index: int,
    ) -> Optional[VisibleHp]:
        """
        HP を読み込む. `scene` が `PokemonCursorScene.COMMAND_POKEMON` の場合だけ実装している.
        """
        top, _0, _1, _2, item_height, _3 = self._SCALES[scene]
        hp_top_offset = 72
        hp_height = 36
        hp_left = 105
        hp_width = 200

        hp_top = top + hp_top_offset + item_height * index
        target = image[hp_top : hp_top + hp_height, hp_left : hp_left + hp_width]
        result = await self._ocr.read_fraction(target, TextColor.GREY)
        if not result:
            return None
        return VisibleHp(current=result.numerator, max=result.denominator)


def is_selected_background(image: cv2.typing.MatLike, min_ratio: float = 0.95) -> bool:
    """
    指定された画像が選択された項目の背景か確認する.
    選択中の項目背景は黄色になっているので, 画像全体がこの色かどうか判定する.
    """
    return np.count_nonzero(
        cv2.inRange(image, _SELECTED_LOWER, _SELECTED_UPPER)
    ) > math.floor(image.shape[0] * image.shape[1] * min_ratio)


_SELECTED_LOWER = np.array((0, 128, 192), dtype=np.uint8)
_SELECTED_UPPER = np.array((128, 255, 255), dtype=np.uint8)


def _find_vertical_cursor_index(
    image: MatLike,
    count: int,
    top: int,
    height: int,
    left: int,
    width: int,
    item_height: int,
) -> Optional[int]:
    """
    縦に等間隔で並んでいるメニューから, 選択されている項目を探し, インデックスを返却する.
    選択されている項目が見つからないときは None を返す.
    """
    count = min(count, (image.shape[0] - top + item_height - height) // item_height)
    targets = (
        image[t : t + height, left : left + width]
        for t in (top + item_height * i for i in range(count))
    )
    return next(
        (i for i, target in enumerate(targets) if is_selected_background(target)),
        None,
    )


async def _none() -> None:
    """None を返す非同期関数."""
    return None
