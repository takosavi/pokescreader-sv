from typing import Literal, Optional, Callable, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QTabWidget,
)

from pkscrd.app.configuration.model import (
    AllyHpFormat,
    BouyomichanConfiguration,
    CaptureDeviceConfiguration,
    Configuration,
    GuiConfiguration,
    NotificationConfiguration,
    NotificationEngine,
    OcrConfiguration,
    VoicevoxConfiguration,
    WebSocketServerConfiguration,
)
from pkscrd.app.gui import set_window_icon
from .inputs import VoicevoxSpeakerInput, AudioDeviceInput

_FORM_ALIGNMENT_FLAG = Qt.AlignmentFlag.AlignVCenter


class WebSocketServerGroup(QGroupBox):

    def __init__(
        self,
        value: WebSocketServerConfiguration,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent, title="WebSocket サーバー")

        self._port = QSpinBox(self)
        self._port.setMinimum(0)
        self._port.setMaximum(65535)
        self._port.setValue(value.port)

        password_widget = QWidget(self)
        self._password = QLineEdit(password_widget)
        self._password.setAccessibleName("パスワード")
        self._password.setText(value.password)
        self._password.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self._show_password = QCheckBox("パスワードを表示", parent=password_widget)
        self._show_password.checkStateChanged.connect(
            lambda state: self._password.setEchoMode(
                QLineEdit.EchoMode.Normal
                if state is Qt.CheckState.Checked
                else QLineEdit.EchoMode.Password
            )
        )
        password_layout = QVBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.addWidget(self._password)
        password_layout.addWidget(self._show_password)
        password_widget.setLayout(password_layout)

        layout = QFormLayout(self)
        layout.addRow("ポート番号", self._port)
        layout.addRow("パスワード", password_widget)
        self.setLayout(layout)

    def output(self) -> WebSocketServerConfiguration:
        return WebSocketServerConfiguration(
            port=self._port.value(),
            password=self._password.text(),
        )


class CaptureDeviceGroup(QGroupBox):

    def __init__(
        self,
        value: CaptureDeviceConfiguration,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent, title="映像キャプチャデバイス")

        self._source = QLineEdit(self)
        self._source.setText(value.source)

        layout = QFormLayout(self)
        layout.setLabelAlignment(_FORM_ALIGNMENT_FLAG)
        layout.addRow("ソース", self._source)
        self.setLayout(layout)

    def output(self) -> CaptureDeviceConfiguration:
        return CaptureDeviceConfiguration(source=self._source.text())


class NotificationGroup(QGroupBox):
    _LABEL_TO_ENGINE: dict[str, NotificationEngine] = {
        "棒読みちゃん": "bouyomichan",
        "VOICEVOX": "voicevox",
    }
    _ENGINE_TO_LABEL: dict[NotificationEngine, str] = {
        value: key for key, value in _LABEL_TO_ENGINE.items()
    }

    _LABEL_TO_ALLY_HP_FORMAT: dict[str, AllyHpFormat] = {
        "数値と割合": "both",
        "数値のみ": "numerator",
        "割合のみ": "ratio",
    }
    _ALLY_HP_FORMAT_TO_LABEL: dict[AllyHpFormat, str] = {
        value: key for key, value in _LABEL_TO_ALLY_HP_FORMAT.items()
    }

    engine_clicked = Signal(str)

    def __init__(
        self,
        value: NotificationConfiguration,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent, title="発話")

        self._engine = QComboBox(self)
        self._engine.addItems(list(self._LABEL_TO_ENGINE))
        self._engine.setCurrentText(self._ENGINE_TO_LABEL[value.engine])
        self._engine.currentTextChanged.connect(
            lambda text: self.engine_clicked.emit(self._LABEL_TO_ENGINE[text])
        )

        self._ally_hp_format = QComboBox(self)
        self._ally_hp_format.addItems(list(self._LABEL_TO_ALLY_HP_FORMAT))
        self._ally_hp_format.setCurrentText(
            self._ALLY_HP_FORMAT_TO_LABEL[value.ally_hp_format]
        )

        self._notifies_ally_team = QCheckBox("味方チームを読み上げる", parent=self)
        self._notifies_ally_team.setChecked(value.notifies_ally_team)
        self._notifies_log = QCheckBox("ログメッセージを読み上げる", parent=self)
        self._notifies_log.setChecked(value.notifies_log)
        self._notifies_tera_type = QCheckBox("テラスタイプを読み上げる", parent=self)
        self._notifies_tera_type.setChecked(value.notifies_tera_type)

        layout = QFormLayout(self)
        layout.setLabelAlignment(_FORM_ALIGNMENT_FLAG)
        layout.addRow("エンジン", self._engine)
        layout.addRow("味方 HP 形式", self._ally_hp_format)
        layout.addRow(self._notifies_ally_team)
        layout.addRow(self._notifies_log)
        layout.addRow(self._notifies_tera_type)
        self.setLayout(layout)

    @property
    def engine(self) -> NotificationEngine:
        return self._LABEL_TO_ENGINE[self._engine.currentText()]

    @property
    def ally_hp_format(self) -> AllyHpFormat:
        return self._LABEL_TO_ALLY_HP_FORMAT[self._ally_hp_format.currentText()]

    def output(self) -> NotificationConfiguration:
        return NotificationConfiguration(
            engine=self.engine,
            ally_hp_format=self.ally_hp_format,
            notifies_ally_team=self._notifies_ally_team.isChecked(),
            notifies_log=self._notifies_log.isChecked(),
            notifies_tera_type=self._notifies_tera_type.isChecked(),
        )


class BouyomichanGroup(QGroupBox):

    def __init__(
        self,
        value: BouyomichanConfiguration,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent, title="棒読みちゃん連携")
        self._speed = QSpinBox()
        self._speed.setAccessibleName("速度")
        self._speed.setToolTip("100 が標準で, 大きいほど速くなります")
        self._speed.setMinimum(1)
        self._speed.setMaximum(999)
        self._speed.setValue(value.speed)

        layout = QFormLayout(self)
        layout.addRow("速度", self._speed)
        self.setLayout(layout)

    def output(self) -> BouyomichanConfiguration:
        return BouyomichanConfiguration(speed=self._speed.value())


class VoicevoxGroup(QGroupBox):

    def __init__(
        self,
        value: VoicevoxConfiguration,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent=parent, title="VOICEVOX 連携")

        self._speaker = VoicevoxSpeakerInput(parent=self, value=value.speaker)
        self._audio_device = AudioDeviceInput(parent=self, value=value.audio)

        self._volume_scale = QDoubleSpinBox(parent=parent)
        self._volume_scale.setAccessibleName("音量倍率")
        self._volume_scale.setDecimals(1)
        self._volume_scale.setSingleStep(0.1)
        self._volume_scale.setMinimum(0.1)
        self._volume_scale.setMaximum(2.0)
        self._volume_scale.setValue(value.volume_scale)

        self._speed_scale = QDoubleSpinBox(parent=parent)
        self._speed_scale.setAccessibleName("速度倍率")
        self._speed_scale.setDecimals(1)
        self._speed_scale.setSingleStep(0.1)
        self._speed_scale.setMinimum(0.1)
        self._speed_scale.setMaximum(10.0)
        self._speed_scale.setValue(value.speed_scale)

        self._uses_stereo = QCheckBox("ステレオ音声にする")
        self._uses_stereo.setChecked(value.uses_stereo)

        form = QFormLayout(self)
        form.setLabelAlignment(_FORM_ALIGNMENT_FLAG)
        form.addRow("キャラクター", self._speaker)
        form.addRow("オーディオデバイス", self._audio_device)
        form.addRow("音量倍率", self._volume_scale)
        form.addRow("速度倍率", self._speed_scale)
        form.addRow(self._uses_stereo)

    def output(self) -> VoicevoxConfiguration:
        return VoicevoxConfiguration(
            speaker=self._speaker.output(),
            volume_scale=round(self._volume_scale.value(), 1),
            speed_scale=round(self._speed_scale.value(), 1),
            uses_stereo=self._uses_stereo.isChecked(),
            audio=self._audio_device.output(),
        )


class OcrGroup(QGroupBox):
    _ID_TO_ENGINE: dict[int, Literal["winocr", "tesseract", "none"]] = {
        0: "winocr",
        1: "tesseract",
        2: "none",
    }
    _ENGINE_TO_ID: dict[Literal["winocr", "tesseract", "none"], int] = {
        value: key for key, value in _ID_TO_ENGINE.items()
    }

    def __init__(self, value: OcrConfiguration, parent: Optional[QWidget] = None):
        super().__init__(parent=parent, title="OCR")

        engine_widget = QWidget(self)
        winocr = QRadioButton("Windows 標準", parent=engine_widget)
        tesseract = QRadioButton("Tesseract OCR", parent=engine_widget)
        none = QRadioButton("使用しない", parent=engine_widget)
        self._engine = QButtonGroup(engine_widget)
        self._engine.addButton(winocr, self._ENGINE_TO_ID["winocr"])
        self._engine.addButton(tesseract, self._ENGINE_TO_ID["tesseract"])
        self._engine.addButton(none, self._ENGINE_TO_ID["none"])
        self._engine.button(self._ENGINE_TO_ID[value.engine]).setChecked(True)
        engine_layout = QHBoxLayout(engine_widget)
        engine_layout.setContentsMargins(0, 0, 0, 0)
        engine_layout.addWidget(winocr)
        engine_layout.addWidget(tesseract)
        engine_layout.addWidget(none)
        engine_widget.setLayout(engine_layout)

        layout = QFormLayout(self)
        layout.setLabelAlignment(_FORM_ALIGNMENT_FLAG)
        layout.addRow("エンジン", engine_widget)
        self.setLayout(layout)

    def output(self) -> OcrConfiguration:
        return OcrConfiguration(engine=self._ID_TO_ENGINE[self._engine.checkedId()])


class GuiGroup(QGroupBox):

    def __init__(self, value: GuiConfiguration, parent: Optional[QWidget] = None):
        super().__init__(parent=parent, title="GUI")

        self._uses_buttons = QCheckBox("ボタンを表示する", parent=self)
        self._uses_buttons.setChecked(value.uses_buttons)

        layout = QFormLayout(self)
        layout.setLabelAlignment(_FORM_ALIGNMENT_FLAG)
        layout.addRow(self._uses_buttons)
        self.setLayout(layout)

    def output(self) -> GuiConfiguration:
        return GuiConfiguration(uses_buttons=self._uses_buttons.isChecked())


class Control(QWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        on_save: Optional[Callable[[], Any]] = None,
        on_cancel: Optional[Callable[[], Any]] = None,
    ):
        super().__init__(parent=parent)

        save_button = QPushButton("保存", parent=self)
        if on_save:
            save_button.pressed.connect(on_save)
        cancel_button = QPushButton("キャンセル", parent=self)
        if on_cancel:
            cancel_button.pressed.connect(on_cancel)

        layout = QHBoxLayout(self)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)


class ConfigurationDialog(QDialog):

    def __init__(
        self,
        value: Configuration,
        parent: Optional[QWidget] = None,
        save: Optional[Callable[[Configuration], Any]] = None,
    ):
        super().__init__(parent)
        self._save = save
        self._is_saved = False

        self.setWindowTitle("設定")
        set_window_icon(self)

        tab = QTabWidget(self)
        tab.setAccessibleName("設定タブ")

        tab_obs = QWidget(tab)
        self._web_socket_server = WebSocketServerGroup(
            parent=tab_obs,
            value=value.web_socket_server,
        )
        self._capture_device = CaptureDeviceGroup(
            parent=tab_obs,
            value=value.capture_device,
        )
        tab_obs_layout = QVBoxLayout(tab_obs)
        tab_obs_layout.addWidget(self._web_socket_server)
        tab_obs_layout.addWidget(self._capture_device)
        tab_obs.setLayout(tab_obs_layout)
        tab.addTab(tab_obs, "OBS 接続")

        tab_notification = QWidget(tab)
        self._notification = NotificationGroup(
            parent=tab_notification,
            value=value.notification,
        )
        self._bouyomichan = BouyomichanGroup(
            parent=tab_notification,
            value=value.bouyomichan,
        )
        self._voicevox = VoicevoxGroup(parent=tab_notification, value=value.voicevox)
        self._switch_notification_engine(self._notification.engine)
        self._notification.engine_clicked.connect(self._switch_notification_engine)
        tab_notification_layout = QVBoxLayout(tab_notification)
        tab_notification_layout.addWidget(self._notification)
        tab_notification_layout.addWidget(self._bouyomichan)
        tab_notification_layout.addWidget(self._voicevox)
        tab_notification.setLayout(tab_notification_layout)
        tab.addTab(tab_notification, "読み上げ")

        tab_others = QWidget(tab)
        self._ocr = OcrGroup(parent=tab_others, value=value.ocr)
        self._gui = GuiGroup(parent=tab_others, value=value.gui)
        tab_others_layout = QVBoxLayout(tab_others)
        tab_others_layout.addWidget(self._ocr)
        tab_others_layout.addWidget(self._gui)
        tab_others.setLayout(tab_others_layout)
        tab.addTab(tab_others, "その他")

        control = Control(self, on_save=self._on_save, on_cancel=self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(tab)
        layout.addWidget(control)

        tab.focusWidget()

    @property
    def is_saved(self) -> bool:
        return self._is_saved

    def output(self) -> Configuration:
        return Configuration(
            web_socket_server=self._web_socket_server.output(),
            capture_device=self._capture_device.output(),
            notification=self._notification.output(),
            bouyomichan=self._bouyomichan.output(),
            voicevox=self._voicevox.output(),
            ocr=self._ocr.output(),
            gui=self._gui.output(),
        )

    def _switch_notification_engine(self, value: str) -> None:
        self._bouyomichan.hide()
        self._voicevox.hide()

        match value:
            case "bouyomichan":
                self._bouyomichan.show()
            case "voicevox":
                self._voicevox.show()

    def _on_save(self) -> None:
        if self._save:
            self._save(self.output())

        QMessageBox.information(
            self,
            "保存成功",
            "設定を保存しました. アプリを再起動します.",
            QMessageBox.StandardButton.Ok,
        )
        self._is_saved = True
        self.close()
