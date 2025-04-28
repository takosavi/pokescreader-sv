from typing import Optional

from PySide6.QtWidgets import QWidget, QMessageBox

from pkscrd.app.gui import set_window_icon


def check_using_initial_settings(parent: Optional[QWidget] = None) -> bool:
    message_box = QMessageBox(parent)
    set_window_icon(message_box)
    message_box.setIcon(QMessageBox.Icon.Warning)
    message_box.setWindowTitle("設定ファイル読み込み失敗")
    message_box.setText("設定ファイルが破損しているようです. 初期設定から開始しますか?")
    message_box.setStandardButtons(
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
    )
    message_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    return message_box.exec_() == QMessageBox.StandardButton.Ok
