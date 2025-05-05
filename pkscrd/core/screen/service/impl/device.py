import asyncio

from cv2.typing import MatLike
from returns.result import ResultE

from pkscrd.core.screen.infra.device import CaptureDeviceClient
from pkscrd.core.screen.service import ScreenFetcher
from pkscrd.core.tolerance.service import AsyncTolerance


class DeviceScreenFetcher(ScreenFetcher):
    """映像キャプチャデバイスから直接映像を読み込む."""

    def __init__(self, client: CaptureDeviceClient, tolerance: AsyncTolerance) -> None:
        self._client = client
        self._tolerance = tolerance

    async def fetch(self) -> ResultE[MatLike]:
        return await self._tolerance.handle(self._fetch)

    async def _fetch(self) -> MatLike:
        loop = asyncio.get_running_loop()
        image = await loop.run_in_executor(None, self._client.read)
        if image is None:
            raise RuntimeError("Failed to read a frame")
        return image
