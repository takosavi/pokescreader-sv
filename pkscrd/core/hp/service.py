import enum
import functools
from typing import Callable, Mapping, Optional, TypeAlias

import cv2
import numpy as np
from cv2.typing import MatLike

from pkscrd.core.ocr.model import TextColor
from pkscrd.core.ocr.service import OcrEngine
from .model import HpScene, VisibleHp

AllyHpMap: TypeAlias = Mapping[HpScene, VisibleHp]
OpponentHpMap: TypeAlias = Mapping[HpScene, float]


class AllyHpReader:
    """味方 HP を読み取る."""

    def __init__(self, ocr_reader: "OcrAllyHpReader"):
        self._ocr_reader = ocr_reader

    async def read(self, image: MatLike) -> AllyHpMap:
        """味方 HP を読み取り, 表示シーンと値の対を返す."""
        return {s: hp for s in HpScene if (hp := await self._read(image, s))}

    async def _read(self, image: MatLike, scene: HpScene) -> Optional[VisibleHp]:
        if not recognize_gauge(image, scene, is_opponent=False):
            return None
        return await self._ocr_reader.read(image, scene)

    @staticmethod
    def create(ocr: OcrEngine) -> "AllyHpReader":
        return AllyHpReader(OcrAllyHpReader(ocr))


class OcrAllyHpReader:
    """味方 HP 読み取りの内部実装. OCR で HP を読み取る."""

    _POSITIONS: dict[HpScene, tuple[int, int, int, int]] = {
        HpScene.COMMAND: (946, 982, 200, 380),
        HpScene.MOVE: (1002, 1038, 180, 360),
    }

    def __init__(self, engine: OcrEngine):
        self._engine = engine

    async def read(self, image: MatLike, scene: HpScene) -> Optional[VisibleHp]:
        top, bottom, left, right = self._POSITIONS[scene]
        image = image[top:bottom, left:right]
        fraction = await self._engine.read_fraction(image, TextColor.GREY)
        if not fraction:
            return None
        return VisibleHp(current=fraction.numerator, max=fraction.denominator)


def recognize_opponent_hps(image: MatLike) -> OpponentHpMap:
    """相手 HP を認識し, 表示シーンと値の対を返す."""
    scenes_having_gauge = (
        scene for scene in HpScene if recognize_gauge(image, scene, is_opponent=True)
    )
    return {
        scene: ratio
        for scene in scenes_having_gauge
        if (ratio := _recognize_opponent_hp_ratio(image, scene)) is not None
    }


def recognize_gauge(
    image: MatLike,
    scene: HpScene,
    is_opponent: bool,
) -> bool:
    """
    ゲージの存在を認識する.
    表示位置にゲージの外枠と,その内側のギャップを判定する.
    """
    top, bottom, left, right = _GAUGE_POSITIONS[is_opponent][scene]
    borders = (
        image[top - 4 : top - 2, left:right],
        image[bottom + 2 : bottom + 4, left:right],
        image[
            top + 1 : bottom - 1,
            left - 4 - _GAUGE_OFFSET : left - 2 - _GAUGE_OFFSET,
        ],
        image[
            top + 1 : bottom - 1,
            right + 2 + _GAUGE_OFFSET : right + 4 + _GAUGE_OFFSET,
        ],
    )
    if not all(np.all(border >= _BORDER_MIN_EACH) for border in borders):
        return False

    gaps = (
        image[top - 2 : top - 1, left:right],
        image[bottom + 1 : bottom + 2, left:right],
        image[
            top + 1 : bottom - 1,
            left - 2 - _GAUGE_OFFSET : left - 1 - _GAUGE_OFFSET,
        ],
        image[
            top + 1 : bottom - 1,
            right + 1 + _GAUGE_OFFSET : right + 2 + _GAUGE_OFFSET,
        ],
    )
    if not all(np.all(gap <= _GAP_MAX_EACH) for gap in gaps):
        return False

    return all(
        np.average(cv2.cvtColor(border, cv2.COLOR_BGR2GRAY))  # type: ignore
        - np.average(cv2.cvtColor(gap, cv2.COLOR_BGR2GRAY))  # type: ignore
        >= _BORDER_GAP_MIN_DIFF
        for border, gap in zip(borders, gaps)
    )


_GAUGE_OFFSET = 1
_GAUGE_POSITIONS = {
    False: {
        HpScene.COMMAND: (
            946,
            982,
            100 + _GAUGE_OFFSET,
            380 - _GAUGE_OFFSET,
        ),
        HpScene.MOVE: (
            1002,
            1038,
            80 + _GAUGE_OFFSET,
            360 - _GAUGE_OFFSET,
        ),
    },
    True: {
        HpScene.COMMAND: (
            156,
            192,
            1540 + _GAUGE_OFFSET,
            1820 - _GAUGE_OFFSET,
        ),
        HpScene.MOVE: (
            92,
            128,
            1560 + _GAUGE_OFFSET,
            1840 - _GAUGE_OFFSET,
        ),
    },
}
_BORDER_MIN_EACH = np.array([80, 80, 80], dtype=np.uint8)
_GAP_MAX_EACH = np.array([184, 184, 184], dtype=np.uint8)
_BORDER_GAP_MIN_DIFF = 50


def _recognize_opponent_hp_ratio(
    image: MatLike,
    scene: HpScene,
    *,
    color_threshold: float = 0.8,
) -> Optional[float]:
    top, bottom, left, right = _GAUGE_POSITIONS[True][scene]
    image = image[top:bottom, left:right]
    row = image[image.shape[0] // 2]

    colorful_area = image[:6, :]
    color = next(
        (
            color
            for color in _GaugeColor
            if np.max(np.apply_along_axis(lambda c: color.ratio(*c), 2, colorful_area))
            > color_threshold
        ),
        _GaugeColor.RED,
    )

    if (border := _find_border(image, color, color_threshold=color_threshold)) is None:
        return None
    return border / row.shape[0]


class _GaugeColor(enum.Enum):
    GREEN = enum.auto()
    YELLOW = enum.auto()
    RED = enum.auto()

    @functools.cached_property
    def ratio(self) -> Callable[[np.uint8, np.uint8, np.uint8], float]:
        return _COLOR_RATIOS[self]


def _find_border(
    image: MatLike,
    color: _GaugeColor,
    *,
    color_threshold: float,
    trimmed: int = 2,
    border_color_threshold: float = 0.5,
    border_left_trimmed: int = 1,
    border_right_trimmed: int = 2,
) -> Optional[int]:
    image = image[trimmed:-trimmed, trimmed:-trimmed]
    row = image[len(image) // 2]

    border = 0
    for index in range(len(row)):  # HACK NumPy らしい方法で実装する.
        if color.ratio(*row[index]) < border_color_threshold:
            break
        border = index

    colored = image[:, 0 : max(border - border_left_trimmed, 0)]
    if all(colored.shape) and np.any(
        np.apply_along_axis(lambda c: color.ratio(*c) < color_threshold, 2, colored)
    ):
        return None

    background = image[:, min(border + border_right_trimmed, len(row)) :]
    if all(background.shape) and not np.all(
        np.apply_along_axis(lambda c: _is_background(*c), 2, background)
    ):
        return None

    if not border:
        return 0
    if border == len(row) - 1:
        return border + trimmed * 2 + 1
    return border + trimmed


_AVG_BACKGROUND = 64
_MAX_BACKGROUND = 144


def _is_background(b: np.uint8, g: np.uint8, r: np.uint8) -> np.bool:
    return b < _MAX_BACKGROUND and g < _MAX_BACKGROUND and r < _MAX_BACKGROUND


def _green_ratio(b: np.uint8, g: np.uint8, r: np.uint8) -> float:
    if r > _MAX_BACKGROUND or b > _MAX_BACKGROUND:
        return 0.0
    return _limit_ratio((int(g) - _AVG_BACKGROUND) / (200 - _AVG_BACKGROUND))


def _yellow_ratio(b: np.uint8, g: np.uint8, r: np.uint8) -> float:
    if b > _MAX_BACKGROUND:
        return 0.0
    return (
        _limit_ratio((int(r) - _AVG_BACKGROUND) / (240 - _AVG_BACKGROUND))
        + _limit_ratio((int(g) - _AVG_BACKGROUND) / (145 - _AVG_BACKGROUND))
    ) / 2


def _red_ratio(b: np.uint8, g: np.uint8, r: np.uint8) -> float:
    if g > _MAX_BACKGROUND or b > _MAX_BACKGROUND:
        return 0.0
    return _limit_ratio((int(r) - _AVG_BACKGROUND) / (220 - _AVG_BACKGROUND))


_COLOR_RATIOS = {
    _GaugeColor.GREEN: _green_ratio,
    _GaugeColor.YELLOW: _yellow_ratio,
    _GaugeColor.RED: _red_ratio,
}


def _limit_ratio(value: float) -> float:
    return max(0.0, min(1.0, value))
