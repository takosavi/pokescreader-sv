from abc import ABC, abstractmethod
from typing import Optional

from cv2.typing import MatLike

from pkscrd.core.ocr.model import Fraction, LogFormat, TextColor, LineContentType


class OcrEngine(ABC):

    @abstractmethod
    async def read_line(
        self,
        image: MatLike,
        text_color: TextColor,
        *,
        content_type: Optional[LineContentType] = None,
    ) -> Optional[str]: ...

    @abstractmethod
    async def read_fraction(
        self,
        image: MatLike,
        text_color: TextColor,
    ) -> Optional[Fraction]: ...

    @abstractmethod
    async def read_log(self, image: MatLike, format: LogFormat) -> list[list[str]]: ...
