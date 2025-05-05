import dataclasses
from typing import Literal, Optional


@dataclasses.dataclass(frozen=True)
class ObsWebSocketServerConfiguration:
    port: int
    password: str


@dataclasses.dataclass(frozen=True)
class ObsCaptureDeviceConfiguration:
    source: str


@dataclasses.dataclass(frozen=True)
class ObsConfiguration:
    web_socket_server: ObsWebSocketServerConfiguration
    capture_device: ObsCaptureDeviceConfiguration


@dataclasses.dataclass(frozen=True)
class CaptureDeviceConfiguration:
    name: str


type ScreenEngine = Literal["capture-device", "obs"]


@dataclasses.dataclass(frozen=True)
class ScreenConfiguration:
    engine: ScreenEngine
    obs: ObsConfiguration
    capture_device: CaptureDeviceConfiguration


type NotificationEngine = Literal["bouyomichan", "voicevox"]
type AllyHpFormat = Literal["both", "numerator", "ratio"]


@dataclasses.dataclass(frozen=True)
class NotificationConfiguration:
    engine: NotificationEngine
    ally_hp_format: AllyHpFormat
    notifies_ally_team: bool
    notifies_log: bool
    notifies_tera_type: bool


@dataclasses.dataclass(frozen=True)
class AudioConfiguration:
    host_api: Optional[str] = None
    device_name: Optional[str] = None


@dataclasses.dataclass(frozen=True)
class BouyomichanConfiguration:
    speed: int


@dataclasses.dataclass(frozen=True)
class VoicevoxConfiguration:
    audio: AudioConfiguration
    volume_scale: float
    speed_scale: float
    uses_stereo: bool
    speaker: Optional[int] = None


@dataclasses.dataclass(frozen=True)
class OcrConfiguration:
    engine: Literal["winocr", "tesseract", "none"]


@dataclasses.dataclass(frozen=True)
class GuiConfiguration:
    uses_buttons: bool


@dataclasses.dataclass(frozen=True)
class Configuration:
    screen: ScreenConfiguration
    notification: NotificationConfiguration
    bouyomichan: BouyomichanConfiguration
    voicevox: VoicevoxConfiguration
    ocr: OcrConfiguration
    gui: GuiConfiguration
