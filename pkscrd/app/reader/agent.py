import asyncio
import time

from loguru import logger
from returns.pipeline import is_successful

from pkscrd.app.reader.controller.image import ImageController
from pkscrd.core.notification.service import Notifier
from pkscrd.core.screen.service import ScreenFetcher
from pkscrd.core.tolerance.model import FatalError


class ImageProcess:

    def __init__(
        self,
        fetcher: ScreenFetcher,
        controller: ImageController,
        notifier: Notifier,
    ):
        self._fetcher = fetcher
        self._controller = controller
        self._notifier = notifier

    async def __call__(self) -> None:
        if not is_successful(result := await self._fetcher.fetch()):
            return

        async for notification in self._controller.handle(result.unwrap()):
            self._notifier.notify(notification)


class ImageProcessAgent:
    """
    映像に関する処理を一定間隔で行うエージェント.

    - 映像を取得する.
    - 映像に関する処理を起動し, 通知を取得する.
    - 取得した通知を起動する.
    """

    def __init__(
        self,
        process: ImageProcess,
        *,
        interval_in_seconds: float = 0.1,
    ):
        self._process = process
        self._interval_in_seconds = interval_in_seconds
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True

    async def __call__(self) -> None:
        while not self._stopped:
            start = time.time()

            try:
                await self._process()
            except Exception as e:
                # エラーハンドラから送出されたエラーは処理を止めるためのものなので再送する.
                if isinstance(e, FatalError):
                    raise
                logger.opt(exception=e).warning(
                    "An error occurred while processing s screenshot.",
                )

            duration = time.time() - start
            if duration > self._interval_in_seconds:
                logger.debug("Polling interval is over: {:.4f}", duration)
                continue
            await asyncio.sleep(self._interval_in_seconds - duration)
