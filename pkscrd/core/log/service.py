import difflib
from collections import deque
from typing import Optional

import cv2.typing
import jaconv
import numpy as np

from pkscrd.core.ocr.model import LogFormat, TextColor
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.scene.model import ImageScene
from .model import Log, LogType


class LogReader:
    """ログメッセージを読み取る."""

    def __init__(self, reader: "OcrLogReader"):
        self._reader = reader

    async def read(self, scene: ImageScene, image: cv2.typing.MatLike) -> Optional[Log]:
        """ログメッセージを読み取る."""
        if recognize_general_log_box(image):
            if general_log := await self._reader.read(image, LogType.GENERAL):
                return Log(LogType.GENERAL, ["".join(line) for line in general_log])
            return None

        if scene not in (ImageScene.UNKNOWN, ImageScene.COMMAND_CANCELING):
            return None  # 行動ログの表示場面は限られるため, 表示される可能性がある状況でのみ読み取る.
        if battle_log := await self._reader.read(image, LogType.BATTLE):
            return Log(LogType.BATTLE, ["".join(line) for line in battle_log])
        return None

    @staticmethod
    def create(ocr: OcrEngine) -> "LogReader":
        return LogReader(OcrLogReader(ocr))


class OcrLogReader:
    """ログメッセージ読み取りの内部実装. OCR を用いてログメッセージを読み取る."""

    _TEXT_COLOR_MAP = {
        LogType.GENERAL: TextColor.WHITE,
        LogType.BATTLE: TextColor.WHITE_AND_YELLOW,
    }
    _LINE_HEIGHT = 65
    _RUBY_HEIGHT = 16

    def __init__(self, engine: OcrEngine):
        self._engine = engine

    async def read(self, image: cv2.typing.MatLike, type_: LogType) -> list[list[str]]:
        top, left, right = _COORDINATES[type_]
        return await self._engine.read_log(
            image[top + self._RUBY_HEIGHT : top + self._LINE_HEIGHT * 2, left:right],
            LogFormat(
                color=self._TEXT_COLOR_MAP[type_],
                line_height=self._LINE_HEIGHT,
                line_interval=self._RUBY_HEIGHT,
            ),
        )


class LogStabilizer:
    """
    ログメッセージを安定化させる機能を提供する.

    ログメッセージは表示途中や表示されていない場面でも読み取られており,
    その内容を都度伝えることは適切ではない.
    通知内容を安定化させるため, 似たメッセージが連続で複数回読み取られたとき,
    そのメッセージが通知に適すると判定することにした.

    加えて, 同じメッセージが何度も伝えられることは望ましくないため.
    通知を一度だけに制限する機能も実装した.
    """

    def __init__(self, *, buffer_size: int = 1):
        self._already_read = False
        self._buffer: deque[Optional[Log]] = deque(maxlen=buffer_size)

    def handle(self, log: Optional[Log]) -> Optional[Log]:
        """
        ログメッセージを受け取り, 安定したと判断したらそのログメッセージを返す.
        安定していなければ None を返す.
        """
        if not log:
            self._buffer.append(None)
            return None

        normalized_log = Log(log.type, [_normalize(line) for line in log.lines])
        is_stable = len(self._buffer) and all(
            _match(log, normalized_log) for log in self._buffer
        )
        self._buffer.append(normalized_log)

        if not is_stable:
            self._already_read = False
            return None

        if self._already_read:
            return None

        self._already_read = True
        return log


def recognize_general_log_box(image: cv2.typing.MatLike, buffer: int = 1) -> bool:
    """汎用ログ表示欄の存在を認識する."""
    if not all(
        np.all(
            cv2.inRange(
                image[top + buffer : bottom - buffer, left + buffer : right - buffer],
                _GENERAL_LOG_BOX_CORNER_LOWER,
                _GENERAL_LOG_BOX_CORNER_UPPER,
            )
        )
        for top, bottom, left, right in _GENERAL_LOG_BOX_CORNER_COORDINATES
    ):
        return False

    background_sample = image[936 + buffer : 969 - buffer, 520 + buffer : 1388 - buffer]
    return np.all(
        cv2.inRange(
            background_sample,
            _GENERAL_LOG_BOX_BACKGROUND_LOWER,
            _GENERAL_LOG_BOX_BACKGROUND_UPPER,
        )
    ).item()


def _normalize(value: str) -> str:
    value = jaconv.z2h(value)
    value = jaconv.hira2hkata(value)
    return value.replace("ﾞ", "").replace("ﾟ", "").replace("八", "ﾊ").replace("ｱ", "ｵ")


def _match(lhs: Optional[Log], rhs: Optional[Log]) -> bool:
    if not lhs or not rhs:
        return False
    if lhs.type is not rhs.type:
        return False
    if not lhs.lines:
        return False
    if len(lhs.lines) != len(rhs.lines):
        return False
    return (
        difflib.SequenceMatcher(None, "".join(lhs.lines), "".join(rhs.lines)).ratio()
        > 0.5
    )


_COORDINATES = {
    LogType.GENERAL: (811, 535, 1388),
    LogType.BATTLE: (782, 285, 1650),
}


_GENERAL_LOG_BOX_CORNER_COORDINATES = (
    (780, 790, 495, 520),
    (970, 980, 1400, 1425),
    (795, 810, 480, 490),
    (940, 965, 1430, 1440),
)
_GENERAL_LOG_BOX_CORNER_LOWER = np.array((0, 160, 192), dtype=np.uint8)
_GENERAL_LOG_BOX_CORNER_UPPER = np.array((127, 255, 255), dtype=np.uint8)
_GENERAL_LOG_BOX_BACKGROUND_LOWER = np.array((0, 0, 0), dtype=np.uint8)
_GENERAL_LOG_BOX_BACKGROUND_UPPER = np.array((64, 64, 64), dtype=np.uint8)
