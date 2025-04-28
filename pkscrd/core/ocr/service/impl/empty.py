from typing import Optional

import cv2.typing
from cv2.typing import MatLike

from pkscrd.core.ocr.model import Fraction, LineContentType, LogFormat, TextColor
from pkscrd.core.ocr.service import OcrEngine


class EmptyEngine(OcrEngine):

    async def read_line(
        self,
        image: cv2.typing.MatLike,
        text_color: TextColor,
        *,
        content_type: Optional[LineContentType] = None,
    ) -> Optional[str]:
        return None

    async def read_fraction(
        self,
        image: MatLike,
        text_color: TextColor,
    ) -> Optional[Fraction]:
        return None

    async def read_log(self, image: MatLike, format: LogFormat) -> list[list[str]]:
        return []
