from pkscrd.core.scene.model import Scene, SceneGroup
from .hp import AllyHpUseCase
from .selection import SelectionUseCase


class AllyUseCase:
    """味方情報ユースケース."""

    def __init__(self, selection: SelectionUseCase, ally_hp: AllyHpUseCase):
        self._selection = selection
        self._ally_hp = ally_hp
        self._requested = False

    def request(self) -> None:
        """コールバック呼び出しを要求する."""
        self._requested = True

    def handle(self, scene: Scene) -> None:
        """シーンに応じて必要な要求を行う."""
        if not self._requested:
            return
        self._requested = False

        if scene.group in (SceneGroup.SELECTION, SceneGroup.SELECTION_COMPLETE):
            self._selection.request()
            return

        self._ally_hp.request()
