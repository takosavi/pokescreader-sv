import contextlib
from queue import Queue
from typing import Optional, Iterator

from loguru import logger

from pkscrd.app.settings.model import (
    BouyomichanSettings,
    VoicevoxSettings,
    AudioSettings,
    NotificationSettings,
)
from pkscrd.app.settings.error import SettingsError
from pkscrd.core.notification.infra.audio import (
    AudioClient,
    DefaultDeviceNotFoundError,
    DeviceNotFoundError,
    HostApiNotFoundError,
    select_output_device,
)
from pkscrd.core.notification.infra.bouyomichan import BouyomichanClient
from pkscrd.core.notification.infra.voicevox import VoiceVoxClient
from pkscrd.core.notification.service import Talker
from pkscrd.core.notification.service.impl.bouyomichan import BouyomichanTalker
from pkscrd.core.notification.service.impl.queuing import QueuingTalker
from pkscrd.core.notification.service.impl.voicevox import VoicevoxTalker
from pkscrd.core.tolerance.model import ToleranceCallback
from pkscrd.core.tolerance.service import Tolerance
from .util import watch_queue


def create_bouyomichan_talker(
    settings: BouyomichanSettings,
    *,
    tolerance_callback: Optional[ToleranceCallback] = None,
) -> Talker:
    """
    設定に対応するインスタンスを作成する.

    Raises:
        ConfigurationError: 設定に問題がありそうなとき.
    """
    client = BouyomichanClient(port=settings.port)
    try:
        client.talk(
            "棒読みちゃんとの接続を確認しました。",
            speed=settings.speed,
        )
    except Exception as error:
        logger.opt(exception=error).debug("Failed to connect to Bouyomichan.")
        raise SettingsError(
            "棒読みちゃんとの連携に失敗しました."
            " 何度も失敗する場合,"
            " 棒読みちゃんが起動しているか,"
            " HTTP 連携が有効になっているか,"
            f" HTTP 連携のポート番号が {settings.port} になっているか確認してください."
        )

    return BouyomichanTalker(
        client,
        Tolerance(callback=tolerance_callback, warning_count=2, fatal_count=4),
        speed=settings.speed,
    )


@contextlib.contextmanager
def using_voicevox_talker(
    voicevox: VoicevoxSettings,
    audio: AudioSettings,
    *,
    sample_rate: int = 24000,
    tolerance_callback: Optional[ToleranceCallback] = None,
) -> Iterator[Talker]:
    """
    設定に対応するインスタンスを作成する.

    Raises:
        ConfigurationError: 設定に問題がありそうなとき.
    """
    try:
        device = select_output_device(audio.host_api, audio.device_name)
    except (HostApiNotFoundError, DefaultDeviceNotFoundError):
        raise SettingsError(
            "オーディオプレイヤーの起動が失敗しました."
            " ホスト API の指定が正しいか確認してください."
        )
    except DeviceNotFoundError:
        raise SettingsError(
            "オーディオプレイヤーの起動が失敗しました."
            " デバイス名の指定が正しいか確認してください."
        )
    logger.debug("Audio output device: {}", device)

    audio_queue: Queue[bytes] = Queue(maxsize=10)
    client = VoiceVoxClient()
    try:
        client.initialize_speaker(voicevox.speaker)
        query = client.audio_query(
            "ヴォイスヴォックスとの接続を確認しました",
            speaker=voicevox.speaker,
        )
        query["volumeScale"] = voicevox.volume_scale
        query["speedScale"] = voicevox.speed_scale
        query["outputSamplingRate"] = sample_rate
        query["outputStereo"] = voicevox.uses_stereo
        query["prePhonemeLength"] = 0.0
        query["postPhonemeLength"] = _POST_PHONEME_LENGTH_BASE / voicevox.speed_scale
        wav = client.synthesis(query, speaker=voicevox.speaker)
    except Exception as error:
        logger.opt(exception=error).debug("Failed to connect to VOICEVOX.")
        raise SettingsError(
            "VOICEVOX との連携に失敗しました."
            " VOICEVOX が起動しているか, 話者の設定が正しいか確認してください."
        )

    logger.debug("Wav: {}", wav.getparams())
    audio_queue.put(wav.readframes(wav.getnframes()))

    inner_talker = VoicevoxTalker(
        client,
        audio_queue,
        Tolerance(callback=tolerance_callback, warning_count=2, fatal_count=4),
        speaker=voicevox.speaker,
        volume_scale=voicevox.volume_scale,
        speed_scale=voicevox.speed_scale,
        sampling_rate=sample_rate,
        uses_stereo=voicevox.uses_stereo,
    )

    text_queue: Queue[str] = Queue(maxsize=10)
    with (
        AudioClient.for_wave(wav, device_index=device.index) as audio_client,
        watch_queue(text_queue, inner_talker),
        watch_queue(audio_queue, audio_client.play),
    ):
        yield QueuingTalker(text_queue)


# HACK 共通化.
_POST_PHONEME_LENGTH_BASE = 1.0


@contextlib.contextmanager
def using_talker(
    notification: NotificationSettings,
    bouyomichan: BouyomichanSettings,
    voicevox: VoicevoxSettings,
    audio: AudioSettings,
    *,
    bouyomichan_tolerance_callback: Optional[ToleranceCallback] = None,
    voicevox_tolerance_callback: Optional[ToleranceCallback] = None,
) -> Iterator[Talker]:
    if notification.engine == "voicevox":
        with using_voicevox_talker(
            voicevox,
            audio,
            tolerance_callback=voicevox_tolerance_callback,
        ) as talker:
            yield talker
        return

    talker = create_bouyomichan_talker(
        bouyomichan,
        tolerance_callback=bouyomichan_tolerance_callback,
    )
    yield talker
