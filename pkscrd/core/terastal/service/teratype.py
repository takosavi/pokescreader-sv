import os
from collections import defaultdict
from typing import Callable, Iterable, Optional, Iterator

import cv2
import numpy as np
from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.terastal.model import TeraType, TeraTypeDetection


class TeraTypeDetector:

    MapFunc = Callable[
        [
            Callable[[tuple[TeraType, MatLike]], tuple[TeraType, float]],
            Iterable[tuple[TeraType, MatLike]],
        ],
        Iterable[tuple[TeraType, float]],
    ]

    def __init__(self, models: Iterable[tuple[TeraType, MatLike]]):
        self._models = list(models)

    def detect(
        self,
        image: MatLike,
        *,
        map_func: Optional[MapFunc] = None,
    ) -> list[TeraTypeDetection]:
        hist = _calc_terastal_histogram(image)
        if hist is None:
            return []
        matcher = _HistMatcher(hist)

        scores: defaultdict[TeraType, float] = defaultdict(float)
        map_func = map_func or map
        for tera_type, score in map_func(matcher, self._models):
            scores[tera_type] = max(scores[tera_type], score)

        return [TeraTypeDetection(*s) for s in scores.items()]

    @staticmethod
    def build_model(root: Optional[str] = None) -> Iterator[tuple[TeraType, MatLike]]:
        """ローカルファイルからモデルをビルドする. 主に開発用."""
        root = root or os.path.join("terastal", "training")
        for t in TeraType:
            tera_type = TeraType(t)
            dir_path = os.path.join(root, tera_type)
            if not os.path.isdir(dir_path):
                logger.warning("Not a directory: {}", dir_path)
                continue

            for file in os.listdir(dir_path):
                path = os.path.join(dir_path, file)
                logger.debug("Load tera type model: {}", path)
                image = cv2.imread(path)
                hist = _calc_terastal_histogram(image)
                assert hist is not None
                yield tera_type, hist


class _HistMatcher:
    """マルチプロセス処理を可能にするためのアダプタ."""

    def __init__(self, hist: MatLike):
        self._hist = hist

    def __call__(self, model: tuple[TeraType, MatLike]) -> tuple[TeraType, float]:
        return model[0], cv2.compareHist(self._hist, model[1], cv2.HISTCMP_INTERSECT)


def _calc_terastal_histogram(
    image: MatLike,
    *,
    min_v: int = 32,
    min_element_count: int = 10000,
) -> Optional[MatLike]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV_FULL)
    mask = cv2.inRange(
        hsv,
        np.array((0, 0, min_v), dtype=np.uint8),
        np.array((255, 255, 255), dtype=np.uint8),
    )
    if np.count_nonzero(mask) < min_element_count:
        return None

    hist = cv2.calcHist(
        [hsv[:, :, 0], hsv[:, :, 1]],
        [0, 1],
        mask,
        [256, 256],
        [0, 256, 0, 256],
    )
    return hist
