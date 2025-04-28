import asyncio
from typing import Optional

from cv2.typing import MatLike
from pnlib.move import (
    Effectiveness as PnEffectiveness,
    MoveScene as PnMoveScene,
    recognize_effectiveness,
)

from pkscrd.core.cursor.service import is_selected_background
from pkscrd.core.scene.model import ImageScene
from pkscrd.core.ocr.model import TextColor, LineContentType
from pkscrd.core.ocr.service import OcrEngine
from .model import Effectiveness, Move, Moves, MoveScene, Pp


class MoveReader:
    """技を読み取る."""

    def __init__(self, ocr_reader: "OcrMoveReader"):
        self._ocr_reader = ocr_reader

    async def read(
        self,
        scene: ImageScene,
        image: MatLike,
    ) -> Optional[Moves]:
        """
        技一覧を読み取り, タプルとして返す.
        対象のシーンではないとき, None を返す. また, 読み取りに失敗した要素は None となる.
        """
        scene_: MoveScene
        if scene is ImageScene.COMMAND_MOVE:
            scene_ = MoveScene.COMMAND
        elif scene is ImageScene.COMMAND_POKEMON:
            scene_ = MoveScene.POKEMON
        else:
            return None

        return tuple(  # type: ignore
            await asyncio.gather(
                *(self._read(image, scene_, index) for index in range(4))
            )
        )

    async def read_selected(
        self,
        scene: ImageScene,
        image: MatLike,
    ) -> Optional[tuple[int, Optional[Move]]]:
        """
        選択中の技を読み取り, そのインデックスと技の内容を返す.
        対象のシーンではないとき, None を返す. また, 技の内容が読み取れないときは None となる.

        技の読み取りができない場合でも, インデックスだけ返却できる.
        また, 選択中の技の位置だけを読み取るため, `read` よりも低負荷である.
        ただし, 技選択画面のみ実装しており, ポケモン選択画面では実装していない.
        """
        if scene is not ImageScene.COMMAND_MOVE:
            return None
        scene_ = MoveScene.COMMAND

        index = next((idx for idx in range(4) if _is_selected_move(image, idx)), None)
        if index is None:
            return None

        return index, await self._read(image, scene_, index)

    async def _read(
        self,
        image: MatLike,
        scene: MoveScene,
        index: int,
    ) -> Optional[Move]:
        selected = scene is MoveScene.COMMAND and _is_selected_move(image, index)
        name, pp = await asyncio.gather(
            self._ocr_reader.read_name(image, scene, index, selected),
            self._ocr_reader.read_pp(image, scene, index),
        )
        if not name:
            return None

        effectiveness = _recognize_effectiveness(image, scene, index)
        return Move(name, effectiveness, pp, selected=selected)

    @staticmethod
    def create(ocr: OcrEngine) -> "MoveReader":
        return MoveReader(OcrMoveReader(ocr))


class OcrMoveReader:
    """技読み取りの内部実装. OCR を用いて技情報を認識する."""

    _NAME_COORDINATES = {
        MoveScene.COMMAND: (610, 646, 1480, 1873),
        MoveScene.POKEMON: (381, 420, 880, 1340),
    }
    _PP_COORDINATES = {
        MoveScene.COMMAND: (662, 698, 1749, 1873),
        MoveScene.POKEMON: (381, 420, 1345, 1505),
    }

    def __init__(self, engine: OcrEngine):
        self._engine = engine

    async def read_name(
        self,
        image: MatLike,
        scene: MoveScene,
        index: int,
        selected: bool,
    ) -> Optional[str]:
        top, bottom, left, right = self._NAME_COORDINATES[scene]
        item_height = _HEIGHTS[scene]
        trimmed = image[
            top + item_height * index : bottom + item_height * index,
            left:right,
        ]
        return await self._engine.read_line(
            trimmed,
            text_color=TextColor.BLACK if selected else TextColor.GREY,
            content_type=LineContentType.MOVE_NAME,
        )

    async def read_pp(
        self,
        image: MatLike,
        scene: MoveScene,
        index: int,
    ) -> Optional[Pp]:
        top, bottom, left, right = self._PP_COORDINATES[scene]
        item_height = _HEIGHTS[scene]
        trimmed = image[
            top + item_height * index : bottom + item_height * index,
            left:right,
        ]
        fraction = await self._engine.read_fraction(
            trimmed,
            TextColor.WHITE_AND_YELLOW_AND_RED,
        )
        if not fraction:
            return None
        return Pp(current=fraction.numerator, max=fraction.denominator)


_PN_EFFECTIVENESS_MAP: dict[PnEffectiveness, Effectiveness] = {
    PnEffectiveness.SUPER_EFFECTIVE: Effectiveness.SUPER_EFFECTIVE,
    PnEffectiveness.EFFECTIVE: Effectiveness.EFFECTIVE,
    PnEffectiveness.NOT_VERY_EFFECTIVE: Effectiveness.NOT_VERY_EFFECTIVE,
    PnEffectiveness.NO_EFFECT: Effectiveness.NO_EFFECT,
}
_HEIGHTS = {MoveScene.COMMAND: 112, MoveScene.POKEMON: 86}


def _is_selected_move(image: MatLike, index: int) -> bool:
    """技が選択されているか判定する. 技選択画面のみ実装している."""
    offset = _HEIGHTS[MoveScene.COMMAND] * index
    return is_selected_background(image[610 + offset : 646 + offset, 1863:1873])


def _recognize_effectiveness(
    image: MatLike,
    scene: MoveScene,
    index: int,
) -> Optional[Effectiveness]:
    """
    技の相性を読み取る.
    """
    pn_scene = (
        PnMoveScene.COMMAND_MOVE
        if scene is MoveScene.COMMAND
        else PnMoveScene.COMMAND_POKEMON
    )
    result = recognize_effectiveness(image, pn_scene, index)
    if not result:
        return None
    return _PN_EFFECTIVENESS_MAP.get(result)
