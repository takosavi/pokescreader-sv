from importlib.resources import as_file, files
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QPixmap
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from pkscrd import __version__
from pkscrd.app.configuration import run_configuration
from pkscrd.app.gui import set_window_icon
from pkscrd.usecase.ally import AllyUseCase
from pkscrd.usecase.cursor import CursorUseCase
from pkscrd.usecase.hp import OpponentHpUseCase
from pkscrd.usecase.move import MoveUseCase
from pkscrd.usecase.screenshot import ScreenshotUseCase
from pkscrd.usecase.team import TeamUseCase


class GuiController(QWidget):

    def __init__(
        self,
        opponent_team: TeamUseCase,
        opponent_hp: OpponentHpUseCase,
        ally: AllyUseCase,
        move: MoveUseCase,
        cursor: CursorUseCase,
        screenshot: ScreenshotUseCase,
        uses_buttons: bool = True,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._needs_restart = False

        self.setWindowTitle(f"Pokéscreader for SV v{__version__}")
        set_window_icon(self)
        self.setMinimumWidth(320)

        def on_check_types() -> None:
            opponent_team.request(with_types=True)

        def on_configure() -> None:
            configured = run_configuration(self)
            if configured:
                self._needs_restart = True
                self.close()

        self._key_mapping: dict[
            tuple[Qt.KeyboardModifier, Qt.Key],
            Callable[[], None],
        ] = {
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_O): opponent_team.request,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_T): on_check_types,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_H): opponent_hp.request,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_A): ally.request,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_M): move.request,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_C): cursor.request,
            (Qt.KeyboardModifier.NoModifier, Qt.Key.Key_1): screenshot.request_saving,
            (Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Comma): on_configure,
        }

        if uses_buttons:
            layout = QVBoxLayout()
            self.setLayout(layout)

            read_opponent_team_button = QPushButton("相手チーム確認 (O)", parent=self)
            read_opponent_team_button.pressed.connect(opponent_team.request)
            layout.addWidget(read_opponent_team_button)

            check_types_button = QPushButton("相手チームのタイプ確認 (T)", parent=self)
            check_types_button.pressed.connect(on_check_types)
            layout.addWidget(check_types_button)

            read_opponent_hp = QPushButton("相手 HP 確認 (H)", parent=self)
            read_opponent_hp.pressed.connect(opponent_hp.request)
            layout.addWidget(read_opponent_hp)

            read_ally_hp = QPushButton("味方情報確認 (A)", parent=self)
            read_ally_hp.pressed.connect(ally.request)
            layout.addWidget(read_ally_hp)

            read_moves = QPushButton("技を読み取り (M)", parent=self)
            read_moves.pressed.connect(move.request)
            layout.addWidget(read_moves)

            read_cursor = QPushButton("カーソルを読み取り (C)", parent=self)
            read_cursor.pressed.connect(cursor.request)
            layout.addWidget(read_cursor)

            save_screenshots = QPushButton("スクリーンショット保存 (1)", parent=self)
            save_screenshots.pressed.connect(screenshot.request_saving)
            layout.addWidget(save_screenshots)

            configure = QPushButton("設定画面を表示 (Ctrl+,)", parent=self)
            configure.setAccessibleName("設定画面を表示 コントロールコンマ")
            configure.pressed.connect(on_configure)
            layout.addWidget(configure)
        else:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(layout)

            label = QLabel(self)
            with as_file(
                files("pkscrd.app.reader.controller.resources") / "banner.png"
            ) as banner_path:
                label.setPixmap(QPixmap(str(banner_path)))
            label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
            )
            layout.addWidget(
                label,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            )

    @property
    def needs_restart(self) -> bool:
        return self._needs_restart

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)

        combination = event.keyCombination()
        key = (combination.keyboardModifiers(), combination.key())
        if target := self._key_mapping.get(key):
            target()


class SettingsErrorDialog(QMessageBox):

    def __init__(self, message: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setIcon(QMessageBox.Icon.Critical)
        self.setWindowTitle("設定エラー")
        self.setText(message)
        self.setStandardButtons(QMessageBox.StandardButton.NoButton)
        set_window_icon(self)

        self._terminate = self.addButton("終了", QMessageBox.ButtonRole.RejectRole)
        self._configure = self.addButton("設定変更", QMessageBox.ButtonRole.ActionRole)

    @property
    def needs_configuration(self) -> bool:
        return self.clickedButton() == self._configure
