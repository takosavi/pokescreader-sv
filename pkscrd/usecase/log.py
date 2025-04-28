from typing import Optional

from cv2.typing import MatLike

from pkscrd.core.log.service import LogReader, LogStabilizer
from pkscrd.core.notification.model import LogNotification
from pkscrd.core.scene.model import ImageScene


class LogUseCase:

    def __init__(self, reader: LogReader, stabilizer: LogStabilizer):
        self._reader = reader
        self._stabilizer = stabilizer

    async def handle(
        self,
        scene: ImageScene,
        image: MatLike,
    ) -> Optional[LogNotification]:
        log = self._stabilizer.handle(await self._reader.read(scene, image))
        return LogNotification(lines=log.lines) if log else None

    @staticmethod
    def create(reader: LogReader) -> "LogUseCase":
        return LogUseCase(reader, LogStabilizer())
