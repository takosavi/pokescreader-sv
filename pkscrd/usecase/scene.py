from typing import Iterator

from loguru import logger

from pkscrd.core.notification.model import SceneChangeNotification
from pkscrd.core.scene.model import Scene, SceneChange, ImageScene
from pkscrd.core.scene.service import SceneChangeDetector, SelectionStartDetector
from .hp import AllyHpUseCase, OpponentHpUseCase
from .team import TeamUseCase


class SceneUseCase:

    def __init__(
        self,
        opponent_team: TeamUseCase,
        ally_team: TeamUseCase,
        opponent_hp: OpponentHpUseCase,
        ally_hp: AllyHpUseCase,
    ) -> None:
        self._opponent_team = opponent_team
        self._ally_team = ally_team
        self._opponent_hp = opponent_hp
        self._ally_hp = ally_hp
        self._change_detector = SceneChangeDetector()
        self._selection_start_detector = SelectionStartDetector()

        # ロギングのための前回状態の記録.
        self._current: Scene = Scene.UNKNOWN

    def handle(
        self,
        scene: Scene,
        image_scene: ImageScene,
    ) -> Iterator[SceneChangeNotification]:
        """画像からシーンに関する処理を行う."""
        if self._current != scene:
            logger.debug("Scene changed: {} -> {}", self._current, scene)
        self._current = scene

        self._selection_start_detector.update(scene)
        if self._selection_start_detector.detect(image_scene):
            self._opponent_team.request_update()
            self._ally_team.request_update()

        for change in self._change_detector.detect(scene):
            if change is SceneChange.COMMAND_START:
                self._opponent_hp.request_next_command()
                self._ally_hp.request_next_command()
            yield SceneChangeNotification(change)
