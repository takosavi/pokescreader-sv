from typing import Any, MutableMapping, Optional

from loguru import logger
from tomlkit.toml_file import TOMLFile, TOMLDocument

from pkscrd.app.settings.model import Settings
from pkscrd.app.settings.service import select_path
from .model import (
    Configuration,
    WebSocketServerConfiguration,
    CaptureDeviceConfiguration,
    NotificationConfiguration,
    BouyomichanConfiguration,
    VoicevoxConfiguration,
    AudioConfiguration,
    OcrConfiguration,
    GuiConfiguration,
)


def settings_to_conf(settings: Settings) -> Configuration:
    return Configuration(
        web_socket_server=WebSocketServerConfiguration(
            port=settings.obs.port,
            password=settings.obs.password,
        ),
        capture_device=CaptureDeviceConfiguration(
            source=settings.obs.source,
        ),
        notification=NotificationConfiguration(
            engine=settings.notification.engine,
            ally_hp_format=settings.notification.ally_hp_format,
            notifies_ally_team=settings.routine.notifies_ally_team,
            notifies_log=settings.routine.notifies_log,
            notifies_tera_type=settings.routine.notifies_tera_type,
        ),
        bouyomichan=BouyomichanConfiguration(speed=settings.bouyomichan.speed),
        voicevox=VoicevoxConfiguration(
            speaker=settings.voicevox.speaker,
            volume_scale=settings.voicevox.volume_scale,
            speed_scale=settings.voicevox.speed_scale,
            uses_stereo=settings.voicevox.uses_stereo,
            audio=AudioConfiguration(
                host_api=settings.audio.host_api,
                device_name=settings.audio.device_name,
            ),
        ),
        ocr=OcrConfiguration(engine=settings.ocr.engine),
        gui=GuiConfiguration(uses_buttons=settings.gui.uses_buttons),
    )


def save(output: Configuration, path: Optional[str] = None) -> None:
    path = path or select_path()
    settings_file = TOMLFile(path)
    try:
        settings = settings_file.read()
    except Exception as e:
        # 設定画面表示時に読み込んだ設定が再度読み込めないことは異常事態.
        # ユーザには通知せずに上書きする.
        logger.opt(exception=e).debug("Loading original TOML file failed.")
        settings = TOMLDocument()

    logger.debug("{}", output)

    obs = _ensure_mapping(settings, "obs")
    obs["port"] = output.web_socket_server.port
    obs["password"] = output.web_socket_server.password
    obs["source"] = output.capture_device.source

    notification = _ensure_mapping(settings, "notification")
    notification["engine"] = output.notification.engine
    notification["ally_hp_format"] = output.notification.ally_hp_format

    routine = _ensure_mapping(settings, "routine")
    routine["notifies_ally_team"] = output.notification.notifies_ally_team
    routine["notifies_log"] = output.notification.notifies_log
    routine["notifies_tera_type"] = output.notification.notifies_tera_type

    bouyomichan = _ensure_mapping(settings, "bouyomichan")
    bouyomichan["speed"] = output.bouyomichan.speed

    voicevox = _ensure_mapping(settings, "voicevox")
    _set_optional(voicevox, "speaker", output.voicevox.speaker)
    voicevox["volume_scale"] = output.voicevox.volume_scale
    voicevox["speed_scale"] = output.voicevox.speed_scale
    voicevox["uses_stereo"] = output.voicevox.uses_stereo

    audio = _ensure_mapping(settings, "audio")
    _set_optional(audio, "host_api", output.voicevox.audio.host_api)
    _set_optional(audio, "device_name", output.voicevox.audio.device_name)

    ocr = _ensure_mapping(settings, "ocr")
    ocr["engine"] = output.ocr.engine

    gui = _ensure_mapping(settings, "gui")
    gui["uses_buttons"] = output.gui.uses_buttons

    try:
        settings_file.write(settings)
    except Exception as e:
        logger.opt(exception=e).debug("Failed to write TOML file.")
        raise RuntimeError("設定ファイルへの書き込みが失敗しました.")


def _ensure_mapping(mapping: TOMLDocument, key: str) -> MutableMapping[str, Any]:
    if (
        key not in mapping
        or not hasattr((value := mapping[key]), "__getitem__")
        and hasattr(value, "__setitem__")
    ):
        mapping[key] = {}
    return mapping[key]  # type: ignore


def _set_optional(mapping: MutableMapping[str, Any], key: str, value: Any) -> None:
    if value is None:
        if key in mapping:
            del mapping[key]
        return

    mapping[key] = value
