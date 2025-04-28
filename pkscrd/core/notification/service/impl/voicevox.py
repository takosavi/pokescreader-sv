from queue import Full, Queue

from loguru import logger
from returns.pipeline import is_successful

from pkscrd.core.notification.infra.voicevox import VoiceVoxClient
from pkscrd.core.notification.service.talker import Talker
from pkscrd.core.tolerance.service import Tolerance


class VoicevoxTalker(Talker):
    """
    VOICEVOX を使ってテキストを読み上げる.
    音声合成が終わるまで待機するので, 非同期的に呼び出すことが望ましい.
    """

    _POST_PHONEME_LENGTH_BASE = 1.0

    def __init__(
        self,
        client: VoiceVoxClient,
        queue_: Queue[bytes],
        tolerance: Tolerance,
        *,
        speaker: int = 0,
        volume_scale: float = 1.0,
        speed_scale: float = 1.7,
        sampling_rate: int = 16000,
        uses_stereo: bool = True,
    ):
        self._client = client
        self._queue = queue_
        self._tolerance = tolerance
        self._speaker = speaker
        self._volume_scale = volume_scale
        self._speed_scale = speed_scale
        self._sampling_rate = sampling_rate
        self._uses_stereo = uses_stereo

    def __call__(self, text: str) -> None:
        query_result = self._tolerance.handle(
            lambda: self._client.audio_query(text, speaker=self._speaker)
        )
        if not is_successful(query_result):
            return

        query = query_result.unwrap()
        query["volumeScale"] = self._volume_scale
        query["speedScale"] = self._speed_scale
        query["outputSamplingRate"] = self._sampling_rate
        query["outputStereo"] = self._uses_stereo
        query["prePhonemeLength"] = 0.0
        query["postPhonemeLength"] = self._POST_PHONEME_LENGTH_BASE / self._speed_scale
        query["pauseLengthScale"] = 0.8 / self._speed_scale
        wav_result = self._tolerance.handle(
            lambda: self._client.synthesis(query, speaker=self._speaker)
        )
        if not is_successful(wav_result):
            return

        with wav_result.unwrap() as wav:
            try:
                self._queue.put_nowait(wav.readframes(wav.getnframes()))
            except Full:
                logger.warning(
                    "発話待ちが多すぎるため, 発話がスキップされました: {}",
                    text,
                )
