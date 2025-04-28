import asyncio
import concurrent.futures
from typing import AsyncIterator, Optional

from cv2.typing import MatLike

from pkscrd.core.notification.model import Notification
from pkscrd.core.scene.service import SceneDetector, recognize_image_scene
from pkscrd.core.terastal.service import TerastalDetector
from pkscrd.usecase.ally import AllyUseCase
from pkscrd.usecase.cursor import CursorUseCase
from pkscrd.usecase.hp import AllyHpUseCase, OpponentHpUseCase
from pkscrd.usecase.log import LogUseCase
from pkscrd.usecase.move import MoveUseCase
from pkscrd.usecase.scene import SceneUseCase
from pkscrd.usecase.screenshot import ScreenshotUseCase
from pkscrd.usecase.selection import SelectionUseCase
from pkscrd.usecase.team import TeamUseCase
from pkscrd.usecase.terastal import notify_tera_type


class ImageController:
    """
    映像を受け取り処理を行うコントローラ.
    """

    def __init__(
        self,
        scene: SceneUseCase,
        ally: AllyUseCase,
        opponent_team: TeamUseCase,
        ally_team: TeamUseCase,
        selection: SelectionUseCase,
        opponent_hp: OpponentHpUseCase,
        ally_hp: AllyHpUseCase,
        move: MoveUseCase,
        cursor: CursorUseCase,
        screenshot: ScreenshotUseCase,
        log: Optional[LogUseCase] = None,
        terastal_detector: Optional[TerastalDetector] = None,
        executor: Optional[concurrent.futures.Executor] = None,
    ):
        self._scene = scene
        self._ally = ally
        self._opponent_team = opponent_team
        self._ally_team = ally_team
        self._selection = selection
        self._opponent_hp = opponent_hp
        self._ally_hp = ally_hp
        self._log = log
        self._move = move
        self._cursor = cursor
        self._terastal_detector = terastal_detector
        self._screenshot = screenshot
        self._map_func = executor.map if executor else None

        self._scene_detector = SceneDetector()

    async def handle(self, image: MatLike) -> AsyncIterator[Notification]:
        n: Optional[Notification]
        nt: Notification

        if n := self._screenshot.handle(image):
            yield n

        # 処理の優先度がつくテラスタルを最優先で処理
        if self._terastal_detector:
            tera_type_detection_summary = self._terastal_detector.detect(image)
            if tera_type_detection_summary:
                yield notify_tera_type(tera_type_detection_summary)
            # 高いリアルタイム性が求められるので, テラスタイプ判定中は他の処理は止める.
            if self._terastal_detector.is_detecting:
                return

        image_scene = recognize_image_scene(image)
        scene = self._scene_detector.detect(image_scene)
        for nt in self._scene.handle(scene, image_scene):
            yield nt
        self._ally.handle(scene)

        if n := self._opponent_team.handle(image_scene, image, map_func=self._map_func):
            yield n
        if n := self._ally_team.handle(image_scene, image, map_func=self._map_func):
            yield n
        if n := self._selection.handle(image_scene, image):
            yield n

        for n in await asyncio.gather(
            self._move.handle(image_scene, image),
            self._cursor.handle(image_scene, image),
            self._opponent_hp.handle(image),
            self._ally_hp.handle(image),
            self._log.handle(image_scene, image) if self._log else _none(),
        ):
            if n:
                yield n


async def _none() -> None:
    return None
