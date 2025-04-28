import os
from collections import deque
from datetime import datetime
from typing import Optional

import cv2
from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.notification.model import ScreenshotNotification


class ScreenshotUseCase:

    def __init__(
        self,
        buffer_size: int,
        *,
        dir_path: Optional[str] = None,
    ):
        self._buffers: deque[tuple[datetime, MatLike]] = deque(maxlen=buffer_size)
        self._dir_path = dir_path

        self._saving_requested = False

    def request_saving(self) -> None:
        self._saving_requested = True

    def handle(self, image: MatLike) -> Optional[ScreenshotNotification]:
        self._buffers.append((datetime.now(), image))

        if not self._saving_requested:
            return None
        self._saving_requested = False

        succeeded = all(
            save_image(image, timestamp, dir_path=self._dir_path)
            for timestamp, image in self._buffers
        )
        return ScreenshotNotification(succeeded=succeeded)


def save_image(
    image: MatLike,
    timestamp: Optional[datetime] = None,
    *,
    dir_path: Optional[str] = None,
) -> bool:
    """
    指定された画像をタイムスタンプ付きで保存する.
    保存が成功したら True, 失敗したら False を返す.
    """
    path = f"{timestamp or datetime.now():%Y-%m-%d-%H-%M-%S-%f}.jpg"
    if dir_path:
        path = os.path.join(dir_path, path)
    logger.debug("Write the image: {}", path)
    return cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, 100])
