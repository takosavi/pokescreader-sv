from typing import Callable, Iterable, Iterator, Optional

from cv2.typing import MatLike
from pnlib.pkmn import recognize_ally_team_for_selection, recognize_opponent_team

from pkscrd.core.notification.model import TeamDirection, TeamNotification
from pkscrd.core.pokemon.model import PokemonId, Team
from pkscrd.core.scene.model import ImageScene

type MapFunc = Callable[
    [Callable[[MatLike], Optional[tuple[int, int]]], Iterable[int]],
    Iterator[Optional[tuple[int, int]]],
]


class TeamUseCase:

    def __init__(
        self,
        direction: TeamDirection,
        recognize: Callable[
            [MatLike, Optional[MapFunc]],
            Iterator[Optional[PokemonId]],
        ],
        scene_predicate: Callable[[ImageScene], bool],
        *,
        uses_auto_notification: bool = False,
    ):
        self._direction = direction
        self._recognize = recognize
        self._scene_predicate = scene_predicate
        self._uses_auto_notification = uses_auto_notification

        self._current: Team = []
        self._requested = False
        self._update_requested = False
        self._with_types = False

    @property
    def current(self) -> Team:
        """現在のチームを返す."""
        return self._current

    def request(self, with_types: bool = False) -> None:
        """次の handle に伴う通知を要求する."""
        self._requested = True
        self._with_types = with_types

    def request_update(self) -> None:
        """次に可能な機会でチームの更新を要求する."""
        self._update_requested = True

    def handle(
        self,
        image_scene: ImageScene,
        image: MatLike,
        *,
        map_func: Optional[MapFunc] = None,
    ) -> Optional[TeamNotification]:
        """画像シーンを前提として画像を処理する"""
        if self._scene_predicate(image_scene):
            if self._update_requested or self._requested:
                self._current = list(self._recognize(image, map_func))

            if self._update_requested:
                self._update_requested = False  # 更新は済んでいるのでフラグを折る
                if self._uses_auto_notification:
                    self.request(with_types=self._with_types)

        if not self._requested:
            return None
        self._requested = False
        return TeamNotification(
            direction=self._direction,
            team=self.current,
            with_types=self._with_types,
        )

    @staticmethod
    def of_ally(uses_auto_callback: bool = False) -> "TeamUseCase":
        return TeamUseCase(
            TeamDirection.ALLY,
            _recognize_ally_team,
            _is_ally_team_shown,
            uses_auto_notification=uses_auto_callback,
        )

    @staticmethod
    def of_opponent() -> "TeamUseCase":
        return TeamUseCase(
            TeamDirection.OPPONENT,
            _recognize_opponent_team,
            _is_opponent_team_shown,
            uses_auto_notification=True,
        )


def _recognize_ally_team(
    image: MatLike,
    map_func: Optional[MapFunc],
) -> Iterator[Optional[PokemonId]]:
    return (
        PokemonId(*pokemon)  # type: ignore
        for pokemon in recognize_ally_team_for_selection(image, map_func)
    )


def _is_ally_team_shown(scene: ImageScene) -> bool:
    return scene is ImageScene.SELECTION


def _recognize_opponent_team(
    image: MatLike,
    map_func: Optional[MapFunc],
) -> Iterator[Optional[PokemonId]]:
    return (
        PokemonId(*pokemon)  # type: ignore
        for pokemon in recognize_opponent_team(image, map_func)
    )


def _is_opponent_team_shown(scene: ImageScene) -> bool:
    return scene in (ImageScene.SELECTION, ImageScene.SELECTION_COMPLETE)
