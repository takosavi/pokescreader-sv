import asyncio
import os
import sys
import threading

import pnlib
from PySide6.QtWidgets import QApplication
from loguru import logger

from pkscrd.app.configuration import run_configuration
from pkscrd.app.reader import ReaderManager, run_settings_error, show_pnlib_error
from pkscrd.app.settings.error import SettingsError, SettingsFileNotFoundError


def main() -> None:
    debugging = bool(os.getenv("_PKSCRD_DEBUG"))
    logger.remove()
    logger.add(
        sys.stderr or "log.txt",
        level="DEBUG" if debugging else "WARNING",
        enqueue=True,
    )

    loop = asyncio.get_event_loop()
    app = QApplication()

    if not pnlib.is_successfully_loaded():
        show_pnlib_error()
        return

    def run() -> bool:
        """
        アプリケーションを実行する.

        Returns:
            読み上げアプリケーションの実行が引き続き必要であれば True, そうでなければ False.
        """
        context_manager = ReaderManager()

        hit_except = False
        try:
            window, polling = loop.run_until_complete(context_manager.__aenter__())

            polling_thread = threading.Thread(
                target=loop.run_until_complete,
                args=(polling(),),
                daemon=True,
            )
            logger.debug("Polling thread: {}", polling_thread.name)
            polling_thread.start()

            window.show()
            app.exec()

            polling.stop()
            polling_thread.join(timeout=60.0)
            logger.debug("Polling thread is stopped.")

            return window.needs_restart
        except:  # noqa: E722
            hit_except = True
            if not loop.run_until_complete(context_manager.__aexit__(*sys.exc_info())):
                raise
            return False  # 結合レベルでは重大な問題なので, 終了させることにする.
        finally:
            if not hit_except:
                loop.run_until_complete(context_manager.__aexit__(None, None, None))

    needs_reader = True
    while needs_reader:
        try:
            needs_reader = run()
        except SettingsFileNotFoundError:
            # 設定ファイルが存在しないときは初期状態に該当するので,
            # メッセージを出さずに設定画面を表示する.
            needs_reader = run_configuration()
        except SettingsError as error:
            needs_configuration = run_settings_error(error)
            if not needs_configuration:
                break
            needs_reader = run_configuration()
