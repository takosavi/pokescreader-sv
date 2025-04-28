from typing import Optional

import cv2.typing

from pkscrd.core.move.service import MoveReader
from pkscrd.core.notification.model import MovesNotification
from pkscrd.core.scene.model import ImageScene


class MoveUseCase:

    def __init__(self, reader: MoveReader) -> None:
        self._reader = reader
        self._requested = False

    def request(self) -> None:
        self._requested = True

    async def handle(
        self,
        scene: ImageScene,
        image: cv2.typing.MatLike,
    ) -> Optional[MovesNotification]:
        if not self._requested:
            return None
        self._requested = False

        return MovesNotification(items=await self._reader.read(scene, image))
