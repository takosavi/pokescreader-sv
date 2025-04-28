import dataclasses

from cv2.typing import MatLike

from pkscrd.core.ocr.error import NotAvailableError


@dataclasses.dataclass
class BoundingRect:
    x: float
    y: float
    width: float
    height: float


@dataclasses.dataclass
class OcrWord:
    text: str
    bounding_rect: BoundingRect


@dataclasses.dataclass
class OcrLine:
    words: list[OcrWord] = dataclasses.field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)


@dataclasses.dataclass
class OcrResult:
    lines: list[OcrLine] = dataclasses.field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)


class WinOcr:

    def __init__(self):
        """
        Raises:
            NotAvailableError: Windows OCR が使用できないとき.
        """
        try:
            import winocr  # type: ignore
        except ImportError:
            raise NotAvailableError("Failed to import `winocr`.")

        self._recognize = winocr.recognize_cv2

    async def recognize(self, image: MatLike, lang: str = "ja") -> OcrResult:
        result = await self._recognize(image, lang=lang)
        return OcrResult(
            lines=[
                OcrLine(
                    words=[
                        OcrWord(
                            text=word.text,
                            bounding_rect=BoundingRect(
                                x=word.bounding_rect.x,
                                y=word.bounding_rect.y,
                                width=word.bounding_rect.width,
                                height=word.bounding_rect.height,
                            ),
                        )
                        for word in line.words
                    ]
                )
                for line in result.lines
            ]
        )
