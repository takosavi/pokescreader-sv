import asyncio
import os
import sys
import threading

import pnlib
from PySide6.QtWidgets import QApplication
from loguru import logger

from pkscrd.app.configuration import run_configuration
from pkscrd.app.reader import create_reader, run_settings_error, show_pnlib_error
from pkscrd.app.settings.error import SettingsError, SettingsFileNotFoundError


def main() -> None:
    debugging = bool(os.getenv("_PKSCRD_DEBUG"))
    logger.remove()
    logger.add(
        sys.stderr or "log.txt",  # For PyInstaller no console pattern
        level="DEBUG" if debugging else "WARNING",
        enqueue=True,
    )

    loop = asyncio.get_event_loop()
    app = QApplication()

    if not pnlib.is_successfully_loaded():
        show_pnlib_error()
        return

    needs_reader = True
    while needs_reader:
        needs_reader = False

        try:
            with create_reader(loop) as (window, polling):
                polling_thread = threading.Thread(
                    target=loop.run_until_complete,
                    args=(polling(),),
                    daemon=True,
                )
                logger.debug("Routine thread: {}", polling_thread.name)
                polling_thread.start()

                window.show()
                app.exec()

                polling.stop()
                polling_thread.join(timeout=60.0)
                logger.debug("Routine thread is stopped.")

                needs_reader = window.needs_restart
        except SettingsFileNotFoundError:
            # 設定ファイルが存在しないときは初期状態に該当するので,
            # メッセージを出さずに設定画面を表示する.
            needs_reader = run_configuration()
        except SettingsError as error:
            needs_configuration = run_settings_error(error)
            if not needs_configuration:
                continue
            needs_reader = run_configuration()
