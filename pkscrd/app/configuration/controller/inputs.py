from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QMessageBox, QPushButton, QWidget
from loguru import logger

from pkscrd.app.configuration.model import AudioConfiguration
from pkscrd.core.notification.infra.audio import list_outputs
from pkscrd.core.notification.infra.voicevox import (
    VoiceVoxClient,
    Speaker,
    SpeakerStyle,
)

_UNDEFINED_LABEL = "(デフォルト)"


class AudioDeviceInput(QComboBox):

    def __init__(
        self,
        value: AudioConfiguration,
        parent: Optional[QWidget] = None,
        name: str = "オーディオデバイス",
    ):
        super().__init__(parent)
        self.setAccessibleName(name)

        self._host_api = next(
            (host_api for host_api in list_outputs() if "MME" in host_api.name),
            None,
        )
        self._devices: list[str] = []
        if self._host_api:
            self._devices = [device.name for device in self._host_api.devices]

        self.addItems([_UNDEFINED_LABEL] + self._devices)
        if value.device_name:
            self.setCurrentText(value.device_name)

    def output(self) -> AudioConfiguration:
        device_name = next(
            (device for device in self._devices if device == self.currentText()),
            None,
        )
        return AudioConfiguration(
            host_api=self._host_api.name if self._host_api and device_name else None,
            device_name=device_name,
        )


class VoicevoxSpeakerLoader(QThread):

    completed = Signal(list)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    def run(self) -> None:
        try:
            speakers = VoiceVoxClient().speakers(timeout=1.0)
        except Exception as e:
            logger.opt(exception=e).debug(
                "Failed to initialize the VOICEVOX speaker list."
            )
            return

        self.completed.emit(speakers)


class VoicevoxSpeakerInput(QWidget):

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        value: Optional[int] = None,
    ):
        super().__init__(parent=parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(240)
        self._initial_value = value
        self._speakers: list[Speaker] = []

        self._load_button = QPushButton("キャラクター一覧を読み込む")
        self._load_button.pressed.connect(self.load)

        self._speaker_input = QComboBox(self)
        self._speaker_input.setAccessibleName("キャラクター")
        self._speaker_input.hide()
        self._style_input = QComboBox(self)
        self._style_input.setAccessibleName("スタイル")
        self._style_input.setMinimumWidth(120)
        self._style_input.hide()
        self._speaker_input.currentIndexChanged.connect(self._on_change_speaker)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._load_button)
        layout.addWidget(self._speaker_input)
        layout.addWidget(self._style_input)
        self.setLayout(layout)

        loader = VoicevoxSpeakerLoader(self)
        loader.completed.connect(self.set_speakers)
        loader.start()

    def load(self) -> None:
        try:
            self.set_speakers(VoiceVoxClient().speakers(timeout=3.0))
        except RuntimeError as e:
            logger.opt(exception=e).debug("Failed to load speakers.")
            QMessageBox.critical(
                self,
                "エラー",
                "話者一覧の読み込みに失敗しました. VOICEVOX が起動しているか確認してください.",
                QMessageBox.StandardButton.Ok,
                QMessageBox.StandardButton.NoButton,
            )

    def set_speakers(self, speakers: list[Speaker]) -> None:
        self._speakers = speakers

        self._speaker_input.clear()
        self._speaker_input.addItems([s.name for s in speakers])
        if self._initial_value is not None:
            self._set_value(self._initial_value)

        load_button_has_focus = self._load_button.hasFocus()
        self._load_button.hide()
        self._speaker_input.show()
        self._style_input.show()
        if load_button_has_focus:
            self._speaker_input.setFocus()

    def output(self) -> Optional[int]:
        if style := self._style:
            return style.id
        return self._initial_value

    @property
    def _speaker(self) -> Optional[Speaker]:
        index = self._speaker_input.currentIndex()
        if index < 0:
            return None
        return self._speakers[index]

    @property
    def _style(self) -> Optional[SpeakerStyle]:
        if not (speaker := self._speaker):
            return None

        index = self._style_input.currentIndex()
        if index < 0:
            return None
        return speaker.styles[index]

    def _on_change_speaker(self) -> None:
        self._style_input.clear()

        if not (speaker := self._speaker):
            return
        self._style_input.addItems([s.name for s in speaker.styles])

    def _set_value(self, value: int) -> None:
        indexes = next(
            (
                (speaker_index, style_index)
                for speaker_index, speaker in enumerate(self._speakers)
                for style_index, style in enumerate(speaker.styles)
                if style.id == value
            ),
            None,
        )
        if indexes is None:
            return

        speaker_index, style_index = indexes
        self._speaker_input.setCurrentIndex(speaker_index)
        self._style_input.setCurrentIndex(style_index)
