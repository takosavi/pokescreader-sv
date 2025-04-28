import operator
from collections import defaultdict
from typing import Optional

import cv2
from loguru import logger

from pkscrd.core.terastal.model import (
    TeraType,
    TeraTypeDetection,
    TeraTypeDetectionSummary,
)
from pkscrd.core.terastal.repos import load_terastal_omen_model, load_tera_type_models
from .omen import TerastalOmenDetector
from .teratype import TeraTypeDetector


class TerastalDetector:
    """テラスタルを判定する."""

    def __init__(
        self,
        omen_detector: "TerastalOmenDetector",
        type_detector: "TeraTypeDetector",
        *,
        buffer_size: int = 4,
        max_omen_wait_count: int = 20,
    ):
        self._omen_detector = omen_detector
        self._type_detector = type_detector
        self._buffer_size = buffer_size
        self._max_omen_wait_count = max_omen_wait_count

        self._omen_wait_count = 0
        self._is_detecting_tera_type = False
        self._buffer: list[list[TeraTypeDetection]] = []

    @property
    def is_detecting(self) -> bool:
        """
        テラスタイプ判定中かどうか.
        判定中は処理遅延を避けたいので, この判定を利用して遅延を軽減することが望ましい.
        """
        return bool(self._omen_wait_count)

    def detect(
        self,
        image: cv2.typing.MatLike,
        *,
        map_func: Optional["TeraTypeDetector.MapFunc"] = None,
    ) -> Optional[TeraTypeDetectionSummary]:
        """
        スクリーンショット画像を順に取り込み, テラスタイプが判定された時点で, スコアが高い順に返す.
        テラスタイプが判定できていないときは空リストを返す.
        """
        # 前兆に入る前の処理.
        if not self._omen_wait_count:
            if self._omen_detector.detect(image):
                logger.debug("Terastal omen detected.")
                self._omen_wait_count += 1
            return None

        # 前兆の最中の処理.
        if not self._is_detecting_tera_type and self._omen_detector.detect(image):
            self._omen_wait_count += 1
            if self._omen_wait_count > self._max_omen_wait_count:
                logger.warning("Terastal omen timed out.")
                self._omen_wait_count = 0
            return None

        # 前兆を抜けた後の処理.
        self._is_detecting_tera_type = True
        current_detections = self._type_detector.detect(image, map_func=map_func)
        logger.trace("Currently detected tera types: {}", current_detections)

        # 規定回数の検出結果が溜まるまで待機.
        self._buffer.append(current_detections)
        if len(self._buffer) < self._buffer_size:
            return None

        scores: defaultdict[TeraType, float] = defaultdict(float)
        for detections in self._buffer:
            for detection in detections:
                scores[detection.type] += detection.color_score
        detections = sorted(
            [TeraTypeDetection(*s) for s in scores.items()],
            key=operator.attrgetter("color_score"),
            reverse=True,
        )
        logger.debug("Tera type detected: {}", detections)

        self._buffer = []
        self._omen_wait_count = 0
        self._is_detecting_tera_type = False
        return summarize_tera_type_detections(detections)

    @staticmethod
    def create() -> "TerastalDetector":
        return TerastalDetector(
            TerastalOmenDetector(load_terastal_omen_model()),
            TeraTypeDetector(load_tera_type_models()),
        )


def summarize_tera_type_detections(
    detections: list[TeraTypeDetection],
) -> Optional[TeraTypeDetectionSummary]:
    """スコア順のテラスタイプ検出結果を入力に, テラスタイプ判定をまとめる."""
    if not detections:
        return None
    primary = detections[0]
    possible = [d for d in detections[1:] if d.color_score > primary.color_score * 0.75]
    return TeraTypeDetectionSummary(primary, possible)
