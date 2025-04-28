from typing import Optional, Literal, Annotated

from pydantic import BaseModel, Field


class ObsSettings(BaseModel):
    port: int  # HACK 範囲を決める.
    password: str
    source: str


class NotificationSettings(BaseModel):
    engine: Literal["bouyomichan", "voicevox"] = "bouyomichan"
    ally_hp_format: Literal["both", "numerator", "ratio"] = "both"


class BouyomichanSettings(BaseModel):
    port: int = 50080  # HACK 番号の範囲を決める
    speed: int = 150


class VoicevoxSettings(BaseModel):
    speaker: int = 0
    volume_scale: float = 1.0
    speed_scale: float = 1.5
    uses_stereo: bool = True


class RoutineSettings(BaseModel):
    notifies_ally_team: bool = False
    notifies_log: bool = True
    notifies_tera_type: bool = True


class GuiSettings(BaseModel):
    uses_buttons: bool = True


class OcrSettings(BaseModel):
    engine: Literal["winocr", "tesseract", "none"] = "winocr"


class AudioSettings(BaseModel):
    host_api: Optional[str] = None
    device_name: Optional[str] = None


class ScreenshotSettings(BaseModel):
    buffer_size: Annotated[int, Field(gt=0, le=10000)] = 1


class Settings(BaseModel):
    obs: ObsSettings
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    bouyomichan: BouyomichanSettings = Field(default_factory=BouyomichanSettings)
    voicevox: VoicevoxSettings = Field(default_factory=VoicevoxSettings)
    routine: RoutineSettings = Field(default_factory=RoutineSettings)
    gui: GuiSettings = Field(default_factory=GuiSettings)
    ocr: OcrSettings = Field(default_factory=OcrSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    screenshot: ScreenshotSettings = Field(default_factory=ScreenshotSettings)
