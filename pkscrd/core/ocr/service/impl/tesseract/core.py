import asyncio
import ctypes.util
import dataclasses
import enum
import os
import sys
from importlib.resources import files
from typing import Optional, Callable, Iterable, Iterator, TypeVar

import cv2
from loguru import logger

from pkscrd.core.ocr.error import NotAvailableError

_T = TypeVar("_T")


class PageSegMode(enum.IntEnum):
    OSD_ONLY = 0
    AUTO_OSD = 1
    AUTO_ONLY = 2
    AUTO = 3
    SINGLE_COLUMN = 4
    SINGLE_BLOCK_VERT_TEXT = 5
    SINGLE_BLOCK = 6
    SINGLE_LINE = 7
    SINGLE_WORD = 8
    CIRCLE_WORD = 9
    SINGLE_CHAR = 10
    SPARSE_TEXT = 11
    SPARSE_TEXT_OSD = 12
    RAW_LINE = 13


class DllNotFoundError(NotAvailableError):
    """動的ライブラリが存在しない例外."""


class DllNotCompatibleError(NotAvailableError):
    """動的ライブラリの形式不正例外."""


class TesseractRuntimeError(RuntimeError):
    """Tesseract OCR 実行中のエラー"""


class Tesseract:
    class PageIteratorLevel(enum.IntEnum):
        BLOCK = 0
        PARA = 1
        TEXTLINE = 2
        WORD = 3
        SYMBOL = 4

    def __init__(self, lib_path: Optional[str] = None):
        """
        Raises:
            LibraryNotFoundError: ライブラリが存在しないとき.
        :param lib_path:
        """
        lib_path = lib_path or _search_lib_name() or _DEFAULT_LIB_PATH
        try:
            tess = ctypes.cdll.LoadLibrary(lib_path)
        except FileNotFoundError:
            raise DllNotFoundError(lib_path)

        try:
            _add_dll_def(tess)
        except AttributeError as error:
            raise DllNotCompatibleError(str(error))

        self._tess = tess

    async def recognize_line(
        self,
        greyscale,
        data_path: Optional[str] = None,
        lang: Optional[str] = None,
        char_whitelist: Optional[str] = None,
    ) -> str:
        """
        Raises:
            TesseractRuntimeError: 実行失敗したとき.
        """
        return await self._recognize(
            greyscale,
            self._parse_line,
            data_path=data_path,
            lang=lang,
            page_seg_mode=PageSegMode.SINGLE_LINE,
            char_whitelist=char_whitelist,
        )

    async def recognize_block(
        self,
        greyscale: cv2.typing.MatLike,
        data_path: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> list[list[str]]:
        """
        Raises:
            TesseractRuntimeError: 実行失敗したとき.
        """
        return await self._recognize(
            greyscale,
            self._parse_block,
            data_path=data_path,
            lang=lang,
            page_seg_mode=PageSegMode.SINGLE_BLOCK,
        )

    async def _recognize(
        self,
        greyscale: cv2.typing.MatLike,
        callback: Callable[[int], _T],
        data_path: Optional[str] = None,
        lang: Optional[str] = None,
        page_seg_mode: PageSegMode = PageSegMode.SINGLE_BLOCK,
        char_whitelist: Optional[str] = None,
    ) -> _T:
        """
        Raises:
            TesseractRuntimeError: 実行失敗したとき.
        """
        data_path = data_path or str(
            files("pkscrd.core.ocr.service.impl.tesseract.resources") / "tessdata"
        )
        lang = lang or "jpn"

        imagedata = (ctypes.c_ubyte * (greyscale.shape[0] * greyscale.shape[1]))(
            # HACK typing 解決.
            *[value.item() for row in greyscale for value in row]  # type: ignore
        )

        api: int = self._tess.TessBaseAPICreate()
        try:
            rc: int = self._tess.TessBaseAPIInit3(
                api,
                str(data_path).encode("utf-8"),
                lang.encode("utf-8"),
            )
            if rc:
                raise TesseractRuntimeError(f"初期化が失敗しました: rc={rc}")

            self._tess.TessBaseAPISetVariable(api, _DEBUG_FILE_KEY, _DEBUG_FILE_VALUE)
            if char_whitelist and not self._tess.TessBaseAPISetVariable(
                api,
                _TESSEDIT_CHAR_WHITELIST,
                char_whitelist.encode("utf-8"),
            ):
                logger.warning("Failed to set the whitelist: {}", char_whitelist)

            self._tess.TessBaseAPISetPageSegMode(api, page_seg_mode.value)
            self._tess.TessBaseAPISetImage(
                api,
                imagedata,
                greyscale.shape[1],
                greyscale.shape[0],
                1,
                greyscale.shape[1],
            )
            self._tess.TessBaseAPISetSourceResolution(api, 300)

            rc = await asyncio.get_running_loop().run_in_executor(
                None,
                self._tess.TessBaseAPIRecognize,
                api,
                ctypes.c_void_p(None),
            )
            if rc:
                raise TesseractRuntimeError(f"OCR 実行が失敗しました: rc={rc}")

            return callback(api)
        finally:
            self._tess.TessBaseAPIDelete(api)

    def _parse_line(self, api: int) -> str:
        block = self._parse_block(api)
        return "".join("".join(line) for line in block)

    def _parse_block(self, api: int) -> list[list[str]]:
        result_iterator = self._tess.TessBaseAPIGetIterator(api)
        page_iterator = self._tess.TessResultIteratorGetPageIteratorConst(
            result_iterator
        )

        left = ctypes.c_int(0)
        top = ctypes.c_int(0)
        right = ctypes.c_int(0)
        bottom = ctypes.c_int(0)
        words: list[_Word] = []
        lines: list[list[_Word]] = []
        while True:
            if text_bytes := self._tess.TessResultIteratorGetUTF8Text(
                result_iterator,
                Tesseract.PageIteratorLevel.WORD,
            ):
                text: str = text_bytes.decode("utf-8")
                succeeds = self._tess.TessPageIteratorBoundingBox(
                    page_iterator,
                    Tesseract.PageIteratorLevel.WORD,
                    ctypes.pointer(left),
                    ctypes.pointer(top),
                    ctypes.pointer(right),
                    ctypes.pointer(bottom),
                )
                if succeeds:
                    confidence: float = self._tess.TessResultIteratorConfidence(
                        result_iterator,
                        Tesseract.PageIteratorLevel.WORD,
                    )
                    words.append(
                        _Word(
                            text,
                            left.value,
                            top.value,
                            right.value,
                            bottom.value,
                            confidence,
                        )
                    )

            if self._tess.TessPageIteratorIsAtFinalElement(
                page_iterator,
                Tesseract.PageIteratorLevel.TEXTLINE,
                Tesseract.PageIteratorLevel.WORD,
            ):
                if words:
                    lines.append(words)
                words = []

            if not self._tess.TessPageIteratorNext(
                page_iterator,
                Tesseract.PageIteratorLevel.WORD,
            ):
                break

        if words:
            lines.append(words)

        if _calc_block_confidence(lines) < _MIN_AVERAGE_CONFIDENCE:
            return []
        return [list(_to_line(words)) for words in lines]


if sys.platform == "win32":
    _LIB_SEARCH_NAMES: tuple[str, ...] = ("libtesseract-5", "libtesseract")
    _DEFAULT_LIB_PATH = os.path.join(
        "C:\\Program Files",
        "Tesseract-OCR",
        "libtesseract-5.dll",
    )
    _DEBUG_FILE_VALUE = b"NUL"
else:
    _LIB_SEARCH_NAMES = ("tesseract", "tesseract.5")
    _DEFAULT_LIB_PATH = "/opt/homebrew/lib/libtesseract.5.dylib"
    _DEBUG_FILE_VALUE = b"/dev/null"

_DEBUG_FILE_KEY = b"debug_file"
_TESSEDIT_CHAR_WHITELIST = b"tessedit_char_whitelist"
_SKIPPING_CHARACTERS = {"_", "。"}
_MIN_AVERAGE_CONFIDENCE = 50.0


@dataclasses.dataclass(frozen=True)
class _Word:
    text: str
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0
    confidence: float = 0.0


def _search_lib_name() -> Optional[str]:
    return next(filter(None, map(ctypes.util.find_library, _LIB_SEARCH_NAMES)), None)


def _add_dll_def(tess) -> None:
    tess.TessBaseAPICreate.restype = ctypes.c_void_p  # TessBaseAPI*
    tess.TessBaseAPIDelete.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
    ]
    tess.TessBaseAPIInit3.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.c_char_p,  # datapath: const char*
        ctypes.c_char_p,  # language: const char*
    ]
    tess.TessBaseAPIInit3.restype = ctypes.c_int
    tess.TessBaseAPISetVariable.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.c_char_p,  # name: const char*
        ctypes.c_char_p,  # value: const char*
    ]
    tess.TessBaseAPISetVariable.restype = ctypes.c_bool
    tess.TessBaseAPISetPageSegMode.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.c_int,  # mode: TessPageSegMode
    ]
    tess.TessBaseAPISetImage.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.POINTER(ctypes.c_ubyte),  # imagedata: const unsigned char*
        ctypes.c_int,  # width: int
        ctypes.c_int,  # height: int
        ctypes.c_int,  # bytes_per_pixel: int
        ctypes.c_int,  # bytes_per_line: int
    ]
    tess.TessBaseAPISetSourceResolution.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.c_int,  # ppi: int
    ]
    tess.TessBaseAPIRecognize.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
        ctypes.c_void_p,  # monitor: ETEXT_DESC*
    ]
    tess.TessBaseAPIRecognize.restype = ctypes.c_int
    tess.TessBaseAPIGetUTF8Text.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
    ]
    tess.TessBaseAPIGetUTF8Text.restype = ctypes.c_char_p
    tess.TessBaseAPIGetIterator.argtypes = [
        ctypes.c_void_p,  # handle: TessBaseAPI*
    ]
    tess.TessBaseAPIGetIterator.restype = ctypes.c_void_p  # TessResultIterator*

    tess.TessResultIteratorGetPageIteratorConst.argtypes = [
        ctypes.c_void_p,  # handle: TessResultIterator*
    ]
    tess.TessResultIteratorGetPageIteratorConst.restype = (
        ctypes.c_void_p  # const TessPageIterator*
    )
    tess.TessResultIteratorGetUTF8Text.argtypes = [
        ctypes.c_void_p,  # handle: TessResultIterator*
        ctypes.c_int,  # level: TessPageIteratorLevel
    ]
    tess.TessResultIteratorGetUTF8Text.restype = ctypes.c_char_p
    tess.TessResultIteratorConfidence.argtypes = [
        ctypes.c_void_p,  # handle: TessResultIterator*
        ctypes.c_int,  # level: TessPageIteratorLevel
    ]
    tess.TessResultIteratorConfidence.restype = ctypes.c_float

    tess.TessPageIteratorNext.argtypes = [
        ctypes.c_void_p,  # handle: const TessPageIterator*
        ctypes.c_int,  # level: TessPageIteratorLevel
    ]
    tess.TessPageIteratorNext.restype = ctypes.c_bool
    tess.TessPageIteratorIsAtFinalElement.argtypes = [
        ctypes.c_void_p,  # handle: const TessPageIterator*
        ctypes.c_int,  # level: TessPageIteratorLevel
        ctypes.c_int,  # element: TessPageIteratorLevel
    ]
    tess.TessPageIteratorIsAtFinalElement.restype = ctypes.c_bool
    tess.TessPageIteratorBoundingBox.argtypes = [
        ctypes.c_void_p,  # handle: const TessPageIterator*
        ctypes.c_int,  # level: TessPageIteratorLevel
        ctypes.POINTER(ctypes.c_int),  # left
        ctypes.POINTER(ctypes.c_int),  # top
        ctypes.POINTER(ctypes.c_int),  # right
        ctypes.POINTER(ctypes.c_int),  # bottom
    ]
    tess.TessPageIteratorBoundingBox.restype = ctypes.c_bool


def _calc_block_confidence(block: list[list[_Word]]) -> float:
    count = sum(sum(1 for _ in line) for line in block)
    if not count:
        return 0.0
    confidence = sum(sum(w.confidence for w in line) for line in block)
    return confidence / count


def _to_line(words: Iterable[_Word]) -> Iterator[str]:
    iterator = iter(words)
    buffer = [next(iterator)]
    for word in iterator:
        if word.text in _SKIPPING_CHARACTERS:
            continue

        last = buffer[-1]
        last_right = last.right
        if word.left < last_right + 20:  # HACK ちゃんと測る
            buffer.append(word)
            continue

        yield "".join(w.text for w in buffer)
        buffer = [word]

    yield "".join(w.text for w in buffer)
