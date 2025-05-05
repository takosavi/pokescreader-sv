import base64
import contextlib
from typing import AsyncIterator

from loguru import logger
from simpleobsws import IdentificationParameters, Request, WebSocketClient  # type: ignore


class ObsClient:

    def __init__(self, client: WebSocketClient):
        self._client = client

    async def ensure_connection(self) -> bool:
        try:
            await self._client.connect()
        except Exception as error:
            logger.opt(exception=error).debug("Failed to connect to OBS Studio.")
            return False
        return True

    async def ensure_identified(self, timeout: int = 3) -> bool:
        return await self._client.wait_until_identified(timeout=timeout)

    async def get_source_screenshot(
        self,
        source: str,
        *,
        width: int = 1920,
        height: int = 1080,
        timeout: int = 3,
        image_format: str = "jpg",
    ) -> bytes:
        params = {
            "sourceName": source,
            "imageFormat": image_format,
            "imageWidth": width,
            "imageHeight": height,
            "imageCompressionQuality": 100,
        }
        req = Request("GetSourceScreenshot", params)
        res = await self._client.call(req, timeout=timeout)
        if not res.ok():
            logger.debug("{}", res.requestStatus)
            message = f"スクリーンショットの取得に失敗しました (映像ソース: {source})"
            raise RuntimeError(message)
        return base64.b64decode(res.responseData["imageData"].split(",")[1])

    @staticmethod
    @contextlib.asynccontextmanager
    async def create(port: int, password: str) -> AsyncIterator["ObsClient"]:
        parameters = IdentificationParameters(ignoreNonFatalRequestChecks=False)
        client = WebSocketClient(f"ws://[::1]:{port}", password, parameters)
        try:
            yield ObsClient(client)
        finally:
            await client.disconnect()
