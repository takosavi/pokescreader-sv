from collections import deque
from typing import Optional

from cv2.typing import MatLike
from pnlib.selection import recognize_selection

from pkscrd.core.notification.model import SelectionNotification, SelectionItem
from pkscrd.core.scene.model import ImageScene
from pkscrd.core.selection.service import hidden_partially
from .team import TeamUseCase


class SelectionUseCase:

    def __init__(self, ally_team: TeamUseCase):
        self._ally_team = ally_team

        self._buffer: deque[list[Optional[int]]] = deque(maxlen=3)
        self._requested = False

    def request(self) -> None:
        self._requested = True

    def handle(
        self,
        scene: ImageScene,
        image: MatLike,
    ) -> Optional[SelectionNotification]:
        # 選出画面では選出を更新する.
        if scene is ImageScene.SELECTION:
            selections = recognize_selection(image)

            # 空から空への変換は記憶しておきたいので受け入れる. それ以外は部分的隠蔽を無視する.
            current = self._current()
            if not current or not hidden_partially(current, selections):
                self._buffer.append(selections)

        if not self._requested:
            return None
        self._requested = False
        team = self._ally_team.current
        return SelectionNotification(
            items=[
                (
                    SelectionItem(
                        index_in_team=index,
                        pokemon_id=team[index] if index < len(team) else None,
                    )
                    if index is not None
                    else None
                )
                for index in self._current()
            ]
        )

    def _current(self) -> list[Optional[int]]:
        # 一瞬認識されないことはあるので, 選出なしはバッファ全数分検知してから返す.
        return next(
            filter(
                None,
                # HACK Mypy 誤検知への対処.
                reversed(self._buffer),  # type: ignore[arg-type]
            ),
            [],
        )
