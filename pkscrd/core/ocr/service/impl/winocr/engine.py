import unicodedata
from typing import Optional

import numpy as np
from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.ocr.error import NotAvailableError
from pkscrd.core.ocr.model import Fraction, LineContentType, LogFormat, TextColor
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.ocr.service.util.image import optimize, optimize_log
from pkscrd.core.ocr.service.util.text import parse_fraction
from .core import WinOcr
from .text import (
    normalize_fraction,
    reorder_lines,
    fix_word,
    fix_line,
    fix_general,
    fix_move_name,
)


class WinOcrEngine(OcrEngine):

    _PADDING = 50
    _PADDING_FRACTION = 100

    def __init__(self, core: WinOcr, *, lang: str = "ja"):
        self._core = core
        self._lang = lang

    async def read_line(
        self,
        image: MatLike,
        text_color: TextColor,
        *,
        content_type: Optional[LineContentType] = None,
    ) -> Optional[str]:
        optimized = optimize(image, text_color=text_color, padding=self._PADDING)
        if optimized is None:
            return None
        result = await self._core.recognize(optimized, lang=self._lang)
        text = unicodedata.normalize("NFKC", result.text).replace(" ", "")
        text = fix_general(text)
        if content_type is LineContentType.MOVE_NAME:
            text = fix_move_name(text)
        return text or None

    async def read_fraction(
        self,
        image: MatLike,
        text_color: TextColor,
    ) -> Optional[Fraction]:
        optimized = optimize(
            image,
            text_color=text_color,
            padding=100,
            uses_blur=True,
        )
        if optimized is None:
            return None
        result = await self._core.recognize(optimized, lang=self._lang)
        return parse_fraction(normalize_fraction(result.text))

    async def read_log(self, image: MatLike, format: LogFormat) -> list[list[str]]:
        optimized = optimize_log(
            image,
            format.color,
            format,
            padding=self._PADDING,
        )
        if optimized is None:
            return []
        result = await self._core.recognize(optimized, lang=self._lang)
        return [
            fix_line(fix_word(word) for word in line)
            for line in reorder_lines(result, format, padding=self._PADDING)
        ]

    @staticmethod
    async def create(lang: str = "ja") -> "WinOcrEngine":
        """
        動作確認をしながら Windows OCR エンジンを生成する.

        Raises:
            NotAvailableError: Windows 日本語 OCR が利用できないとき.
        """
        core = WinOcr()
        try:
            await core.recognize(np.zeros((20, 20, 3), dtype=np.uint8), lang=lang)
        except Exception as error:
            logger.opt(exception=error).debug(f"An OCR trial failed: lang={lang}")
            raise NotAvailableError()
        return WinOcrEngine(core, lang=lang)
