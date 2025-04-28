import os
from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.terastal.repos import TerastalOmenModel


class TerastalOmenDetector:
    """テラスタル前兆を検知する."""

    def __init__(self, model: TerastalOmenModel):
        self._model = model
        self._in_omen = False

    def detect(self, image: MatLike) -> bool:
        if not _is_omen_inner(image, self._model.mask_inner):
            self._in_omen = False
            return False

        # 外側は徐々にテラスタル色に近づくため, 前兆に入るときだけ外側を判定する.
        if self._in_omen:
            return True

        if _is_omen_inner(image, self._model.mask_outer):
            return False
        self._in_omen = True
        return True

    @staticmethod
    def build_model(root: Optional[str] = None) -> TerastalOmenModel:
        """ローカルファイルからモデルをビルドする. 主に開発用."""
        root = root or os.path.join("terastal", "training")
        dir_path = os.path.join(root, "omen")
        logger.debug("Load Terastal omen model: {}", dir_path)

        def _create_mask(image: MatLike) -> MatLike:
            return np.uint8(255) - cv2.inRange(
                image,
                np.array((0, 0, 255), dtype=np.uint8),
                np.array((0, 0, 255), dtype=np.uint8),
            )

        return TerastalOmenModel(
            mask_inner=_create_mask(
                cv2.imread(os.path.join(dir_path, "terastal-omen-inner.png"))
            ),
            mask_outer=_create_mask(
                cv2.imread(os.path.join(dir_path, "terastal-omen-outer.png"))
            ),
        )


_WHITE_LOWER = np.array((248, 248, 248), dtype=np.uint8)
_WHITE_UPPER = np.array((255, 255, 255), dtype=np.uint8)


def _is_omen_inner(
    image: MatLike,
    region_mask: MatLike,
    *,
    max_non_white_ratio: float = 0.7,
    max_low_v_ratio: float = 0.01,
    min_higher_v_ratio: float = 0.5,
    max_high_s_ratio: float = 0.03,
    s_low_bound: int = 144,
    s_peak_lower: int = 8,
    s_peak_upper: int = 88,
    s_peak_band_width: int = 8,
    s_peak_tolerance: float = 0.4,
    min_h_in_band_ratio: float = 0.8,
    h_band_lower: int = 80,
    h_band_upper: int = 150,
    min_h_peak_ratio: float = 0.15,
    h_peak_lower: int = 100,
    h_peak_upper: int = 115,
) -> bool:
    original_total = np.count_nonzero(region_mask)

    # ポケモンによってはクリスタルからはみ出て白く表示される部分があり,
    # HSV 傾向が狂うのでマスクする.
    non_white_mask = cv2.bitwise_not(cv2.inRange(image, _WHITE_LOWER, _WHITE_UPPER))
    mask = cv2.bitwise_and(region_mask, non_white_mask)
    if np.count_nonzero(mask) < original_total * max_non_white_ratio:
        return False
    total = np.count_nonzero(mask)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 輝度は明るいほうに偏る
    # HACK もっと形を見るほうがよい
    v = cv2.calcHist([hsv[:, :, 2]], [0], mask, [256], [0, 256])
    if (
        np.sum(v[:128]) > total * max_low_v_ratio
        or np.sum(v[224:]) < total * min_higher_v_ratio
    ):
        return False

    # 色相は偏りがある
    h = cv2.calcHist([hsv[:, :, 0]], [0], mask, [180], [0, 180])
    if (
        np.sum(h[h_band_lower:h_band_upper]) < total * min_h_in_band_ratio
        or np.sum(h[h_peak_lower:h_peak_upper]) < total * min_h_peak_ratio
    ):
        return False

    # 彩度は低いほうに偏る
    s = cv2.calcHist([hsv[:, :, 1]], [0], mask, [256], [0, 256])
    if np.sum(s[s_low_bound:]) > total * max_high_s_ratio:
        return False
    # 残りですべての要素を分け合っていると仮定して,
    # 平均と比較して想定外の山・谷がないことを確認する.
    average = total / 255
    peak_threshold = average * s_peak_band_width * s_peak_tolerance
    out_peak_threshold = average * s_peak_band_width / s_peak_tolerance
    if any(
        np.sum(s[b : b + s_peak_band_width]) < peak_threshold
        for b in range(s_peak_lower, s_peak_upper, s_peak_band_width)
    ) or any(
        np.sum(s[b : b + s_peak_band_width]) > out_peak_threshold
        for b in range(s_peak_upper, s_low_bound, s_peak_band_width)
    ):
        return False

    return True
