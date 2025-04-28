import asyncio

import cv2
import cv2.typing
import numpy as np
from returns.result import ResultE

from pkscrd.core.screen.infra.obs import ObsClient
from pkscrd.core.screen.service import ScreenFetcher
from pkscrd.core.tolerance.service import AsyncTolerance


class ObsScreenFetcher(ScreenFetcher):
    """OBS を用いたスクリーン映像読み取り"""

    def __init__(
        self,
        obs: ObsClient,
        source: str,
        tolerance: AsyncTolerance,
    ):
        self._obs = obs
        self._source = source
        self._tolerance = tolerance

    async def fetch(self) -> ResultE[cv2.typing.MatLike]:
        return await self._tolerance.handle(self._fetch)

    async def _fetch(self) -> cv2.typing.MatLike:
        data = await self._obs.get_source_screenshot(self._source)
        return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)


class ObsRecovery:
    """OBS 接続障害の復旧処理"""

    def __init__(self, obs: ObsClient, sleep_in_seconds: float = 5.0):
        self._obs = obs
        self._sleep_in_seconds = sleep_in_seconds

    async def __call__(self) -> bool:
        await asyncio.sleep(self._sleep_in_seconds)
        return (
            await self._obs.ensure_connection() and await self._obs.ensure_identified()
        )
