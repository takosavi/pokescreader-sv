import httpx
from loguru import logger


class BouyomichanClient:

    def __init__(self, port: int = 50080):
        self._port = port
        self._client = httpx.Client()  # HACK 外で死活管理する.

    def talk(
        self,
        text: str,
        *,
        speed: int = 150,
        timeout: float = 3.0,
    ) -> None:
        try:
            res = self._client.get(
                f"http://localhost:{self._port}/talk",
                params={"text": text, "speed": str(speed)},
                timeout=timeout,
            )
        except httpx.TimeoutException as e:
            raise RuntimeError("棒読みちゃん連携がタイムアウトしました", e)
        except httpx.HTTPError as e:
            raise RuntimeError("棒読みちゃん連携リクエストが失敗しました", e)

        if res.status_code != httpx.codes.OK:
            raise RuntimeError(
                f"棒読みちゃん連携レスポンスが不正です: {res.status_code}"
            )
        logger.trace(res.text)
