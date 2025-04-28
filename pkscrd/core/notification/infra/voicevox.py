import wave
from io import BytesIO
from typing import Callable, Collection, Optional

import httpx
from pydantic import BaseModel, TypeAdapter


class SpeakerStyle(BaseModel):
    id: int
    name: str


class Speaker(BaseModel):
    name: str
    styles: list[SpeakerStyle]


class VoiceVoxClient:

    def __init__(self, port: int = 50021):
        self._port = port
        self._base_url = f"http://localhost:{self._port}"
        self._client = httpx.Client()  # HACK 外で生存管理する.

    def speakers(self, timeout: float = 3.0) -> list[Speaker]:
        res = self._handle_error(
            lambda: self._client.get(f"{self._base_url}/speakers", timeout=timeout)
        )
        return TypeAdapter(list[Speaker]).validate_json(res.content)

    def initialize_speaker(self, speaker: int, timeout: float = 3.0) -> None:
        self._handle_error(
            lambda: self._client.post(
                f"{self._base_url}/initialize_speaker",
                params={"speaker": str(speaker), "skip_reinit": "true"},
                timeout=timeout,
            ),
            acceptable_status_codes={httpx.codes.NO_CONTENT},
        )

    def audio_query(
        self,
        text: str,
        speaker: int = 0,
        timeout: float = 3.0,
    ) -> dict:
        res = self._handle_error(
            lambda: self._client.post(
                f"{self._base_url}/audio_query",
                params={"text": text, "speaker": str(speaker)},
                timeout=timeout,
            )
        )
        return res.json()

    def synthesis(
        self,
        query: dict,
        speaker: int = 0,
        timeout: float = 3.0,
    ) -> wave.Wave_read:
        res = self._handle_error(
            lambda: self._client.post(
                f"{self._base_url}/synthesis",
                params={"speaker": str(speaker)},
                json=query,
                timeout=timeout,
            )
        )
        return wave.Wave_read(BytesIO(res.content))

    @staticmethod
    def _handle_error(
        func: Callable[[], httpx.Response],
        acceptable_status_codes: Optional[Collection[int]] = None,
    ) -> httpx.Response:
        try:
            res = func()
        except httpx.TimeoutException as e:
            raise RuntimeError("VoiceVox連携リクエストがタイムアウトしました", e)
        except httpx.HTTPError as e:
            raise RuntimeError("VoiceVox連携リクエストが失敗しました", e)

        acceptable_status_codes = acceptable_status_codes or {httpx.codes.OK}
        if res.status_code not in acceptable_status_codes:
            raise RuntimeError(f"VoiceVox連携レスポンスが不正です: {res.status_code}")

        return res
