import os
import sys
import tomllib
from typing import Optional, Iterator

from loguru import logger
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from .model import Settings
from .error import SettingsError, SettingsFileNotFoundError


def select_path() -> str:
    """
    設定ファイルのパスとして適するものを選択する.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]

    if os.path.exists(_FILE_NAME):
        return _FILE_NAME

    # App バンドルからのパス解決を試みる.
    if os.path.dirname(sys.argv[0]).endswith(os.path.join(".app", "Contents", "MacOS")):
        return os.path.join(os.path.dirname(sys.argv[0]), "..", "..", "..", _FILE_NAME)

    # 解決できなければデフォルトにフォールバック.
    return _FILE_NAME


def load_settings(path: Optional[str] = None) -> Settings:
    """
    設定ファイルを読み取る.

    Raises:
        SettingsFileNotFoundError: 設定ファイルが見つからないとき.
        SettingsError: 設定ファイルに問題があるとき.
    """
    path = path or _FILE_NAME

    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError as error:
        logger.opt(exception=error).debug("FileNotFoundError: {}", path)
        raise SettingsFileNotFoundError(
            f"{path} が見つかりませんでした."
            " マニュアルを参考にファイルを作成してください."
            " 作成済みの場合, ファイル名が正しいか, 拡張子が正しいか確認してください."
        )
    except tomllib.TOMLDecodeError as error:
        logger.opt(exception=error).debug("TOMLDecodeError: {}", path)
        raise SettingsError(
            f"{path} の読み込みに失敗しました. 正しく記述されているか確認してください.\n"
            f"メッセージ:\n{error}"
        )

    try:
        return Settings.model_validate(data)
    except ValidationError as error:
        logger.opt(exception=error).debug("ValidationError")
        message = "\n".join(create_validation_error_message(error))
        raise SettingsError(
            f"{path} の解釈に失敗しました. 正しく記述されているか確認してください."
            "\n"
            f"\n{message}"
        )


def create_validation_error_message(e: ValidationError) -> Iterator[str]:
    return (_fix_line(details) for details in e.errors())


def _fix_line(details: ErrorDetails) -> str:
    # HACK enum エラーを日本語で返す.
    logger.debug("{}", details)
    location = ".".join(map(str, details["loc"]))
    message = _VALIDATION_ERROR_TYPES.get(details["type"], details["msg"])
    return f"{location}: {message}"


_FILE_NAME = "settings.toml"
_VALIDATION_ERROR_TYPES = {
    "int_parsing": "整数を設定してください",
    "int_from_float": "整数を設定してください",
    "bool_parsing": "true または false を設定してください",
    "string_type": "文字列を設定してください",
    "missing": "必須項目です",
}
