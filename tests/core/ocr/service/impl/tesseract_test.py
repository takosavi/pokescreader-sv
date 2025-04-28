import os
import sys

import numpy as np
import pytest

from pkscrd.core.ocr.service.impl.tesseract import (
    DllNotCompatibleError,
    DllNotFoundError,
    Tesseract,
    TesseractRuntimeError,
)


@pytest.mark.skipif(
    bool(os.getenv("NO_TESSERACT")),
    reason="Tesseract が使えるときだけ実行する.",
)
class TestTesseract:

    _IMAGE_EXAMPLE = np.zeros((20, 20), dtype=np.uint8)

    def test_動的ライブラリが読み込めなかったとき(self):
        with pytest.raises(DllNotFoundError) as error_info:
            Tesseract("/dev/null")
        assert str(error_info.value) == "/dev/null"

    @pytest.mark.skipif(
        not sys.platform.startswith("win"),
        reason="Windows でのみ実行する.",
    )
    def test_動的ライブラリに想定するシンボルがないとき(self):
        with pytest.raises(DllNotCompatibleError):
            Tesseract("python3")

    @pytest.mark.asyncio
    async def test_存在しない言語を指定(self):
        core = Tesseract()
        with pytest.raises(TesseractRuntimeError):
            await core.recognize_line(self._IMAGE_EXAMPLE, lang="xxx")
