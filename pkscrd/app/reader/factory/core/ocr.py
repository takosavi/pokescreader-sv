from pkscrd.app.settings.model import OcrSettings
from pkscrd.app.settings.error import SettingsError
from pkscrd.core.ocr.error import NotAvailableError
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.ocr.service.impl.empty import EmptyEngine
from pkscrd.core.ocr.service.impl.tesseract import (
    TesseractEngine,
    DllNotCompatibleError,
    DllNotFoundError,
    OcrTrialFailureError,
)
from pkscrd.core.ocr.service.impl.winocr import WinOcrEngine


async def create_ocr_engine(settings: OcrSettings, lang: str = "ja") -> OcrEngine:
    """
    設定に対応する OCR エンジンを作成する.

    Raises:
        ConfigurationError: 設定の問題が疑われるとき.
    """
    match settings.engine:
        case "winocr":
            try:
                return await WinOcrEngine.create(lang=lang)
            except NotAvailableError:
                raise SettingsError(
                    "日本語 Windows OCR が使用できない環境です."
                    " 他のエンジンの使用を検討してください."
                )

        case "tesseract":
            try:
                return await TesseractEngine.create()
            except (DllNotFoundError, DllNotCompatibleError):
                raise SettingsError(
                    "Tesseract OCR ライブラリの読み込みが失敗しました."
                    " Tesseract OCR が正しくインストールされているか確認してください."
                )
            except OcrTrialFailureError:
                raise SettingsError(
                    "Tesseract OCR の実行が失敗しました."
                    " Tesseract OCR が正しくインストールされているか確認してください."
                )

        case _:
            return EmptyEngine()
