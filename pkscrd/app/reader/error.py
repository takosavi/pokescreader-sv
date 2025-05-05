from queue import Queue, Empty

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QMessageBox

from pkscrd.core.tolerance.service import QueuingToleranceCallback


def create_obs_tolerance_callback(errors: Queue[str]) -> QueuingToleranceCallback:
    return QueuingToleranceCallback(
        errors,
        "OBS Studio からの映像取得失敗が長時間続きました. アプリを終了します.",
        "OBS Studio へ接続できなくなりました. アプリを終了します.",
    )


def create_capture_tolerance_callback(errors: Queue[str]) -> QueuingToleranceCallback:
    return QueuingToleranceCallback(
        errors,
        "映像キャプチャデバイスからの映像取得失敗が長時間続きました. アプリを終了します.",
        "映像キャプチャデバイスへ接続できなくなりました. アプリを終了します.",
    )


def create_bouyomichan_tolerance_callback(
    errors: Queue[str],
) -> QueuingToleranceCallback:
    return QueuingToleranceCallback(
        errors,
        "棒読みちゃんの発話失敗が長時間続きました. アプリを終了します.",
        "棒読みちゃんへ接続できなくなりました. アプリを終了します.",
    )


def create_voicevox_tolerance_callback(errors: Queue[str]) -> QueuingToleranceCallback:
    return QueuingToleranceCallback(
        errors,
        "VOICEVOX への接続失敗が長時間続きました. アプリを終了します.",
        "VOICEVOX へ接続できなくなりました. アプリを終了します.",
    )


def watch_error(
    w: QWidget,
    messages: Queue[str],
    interval_in_millis: int = 100,
) -> None:
    timer = QTimer(w)
    timer.setInterval(interval_in_millis)

    def watch_() -> None:
        try:
            message = messages.get_nowait()
        except Empty:
            return

        QMessageBox.critical(
            w,
            "エラー",
            message,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.NoButton,
        )
        w.close()
        timer.stop()

    timer.timeout.connect(watch_)
    timer.start()
