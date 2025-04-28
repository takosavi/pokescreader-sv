from typing import Optional

import numpy as np
from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.ocr.error import NotAvailableError
from pkscrd.core.ocr.model import Fraction, LineContentType, LogFormat, TextColor
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.ocr.service.util.image import optimize, optimize_log
from pkscrd.core.ocr.service.util.text import parse_fraction
from .core import Tesseract


class OcrTrialFailureError(NotAvailableError):
    """試験実行が失敗した例外."""


class TesseractEngine(OcrEngine):

    def __init__(self, tess: Tesseract):
        self._tess = tess

    async def read_line(
        self,
        image: MatLike,
        text_color: TextColor,
        *,
        content_type: Optional[LineContentType] = None,
    ) -> Optional[str]:
        optimized = optimize(image, text_color=text_color)
        if optimized is None:
            return None

        char_whitelist: Optional[str] = None
        if content_type is LineContentType.MOVE_NAME:
            char_whitelist = _MOVE_NAME_CHARS
        return await self._tess.recognize_line(optimized, char_whitelist=char_whitelist)

    async def read_fraction(
        self,
        image: MatLike,
        text_color: TextColor,
    ) -> Optional[Fraction]:
        optimized = optimize(image, text_color=text_color)
        if optimized is None:
            return None
        result = await self._tess.recognize_line(
            optimized,
            lang="eng",
            char_whitelist=_FRACTION_CHARS,
        )
        return parse_fraction(result)

    async def read_log(self, image: MatLike, format: LogFormat) -> list[list[str]]:
        optimized = optimize_log(image, format.color, format)
        if optimized is None:
            return []
        result = await self._tess.recognize_block(optimized)
        return [[_fix_word(word) for word in line] for line in result]

    @staticmethod
    async def create() -> "TesseractEngine":
        """
        動作確認をしながら Tesseract OCR エンジンを生成する.

        Raises:
            DllNotFoundError: 動的ライブラリが見つからないとき.
            DllNotCompatibleError: 動的ライブラリのシンボルが不正なとき.
            OcrTrialFailureError: 試験実行が失敗したとき.
        """
        core = Tesseract()
        try:
            await core.recognize_line(np.zeros((20, 20), dtype=np.uint8), lang="eng")
        except Exception as error:
            logger.opt(exception=error).debug("An OCR trial failed.")
            raise OcrTrialFailureError()
        return TesseractEngine(core)


_FRACTION_CHARS = "0123456789/"
_MOVE_NAME_CHARS = (
    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
    "がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽゃゅょっ"
    "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    "ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペァィゥェォャュョッー"
    "013・"
)


def _fix_word(text: str) -> str:
    if text == "誤所に" or text == "怠所に":
        return "急所に"

    if text.endswith("/"):
        text = text[:-1] + "!"
    return text
