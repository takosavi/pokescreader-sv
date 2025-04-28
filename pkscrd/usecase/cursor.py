from typing import Optional

from cv2.typing import MatLike
from loguru import logger

from pkscrd.core.cursor.model import Cursor, PokemonCursorScene
from pkscrd.core.cursor.service import CommandCursorReader, PokemonCursorReader
from pkscrd.core.move.service import MoveReader
from pkscrd.core.notification.model import (
    CommandCursorNotification,
    CursorNotification,
    MoveCursorNotification,
    PokemonCursorNotification,
    SelectionCompleteButtonNotification,
    UnknownCursorNotification,
)
from pkscrd.core.scene.model import ImageScene
from .team import TeamUseCase


class CursorUseCase:

    def __init__(
        self,
        command_reader: CommandCursorReader,
        pokemon_reader: PokemonCursorReader,
        move_reader: MoveReader,
        ally_team: TeamUseCase,
    ):
        self._command_reader = command_reader
        self._pokemon_reader = pokemon_reader
        self._move_reader = move_reader
        self._ally_team = ally_team

        self._requested = False

    def request(self) -> None:
        self._requested = True

    async def handle(
        self,
        scene: ImageScene,
        image: MatLike,
    ) -> Optional[CursorNotification]:
        if not self._requested:
            return None
        self._requested = False
        logger.debug("Cursor recognition for scene: {}", scene)

        match scene:
            case ImageScene.SELECTION:
                return await self._handle_selection(image)
            case ImageScene.COMMAND:
                return self._handle_command(image)
            case ImageScene.COMMAND_MOVE:
                return await self._handle_command_move(image)
            case ImageScene.COMMAND_POKEMON:
                return await self._handle_command_pokemon(image)
            case _:
                return UnknownCursorNotification()

    async def _handle_selection(
        self,
        image: MatLike,
    ) -> PokemonCursorNotification | SelectionCompleteButtonNotification:
        cursor = await self._pokemon_reader.read(
            image,
            PokemonCursorScene.SELECTION,
            team=self._ally_team.current or None,
        )
        if not cursor:
            # 色によりカーソルが認識できないときは, 消去法で完了ボタンが選択されているとみなす.
            # HACK 認識ミスなどでも起きる事象なので, もっと本質的な方法を使いたい.
            return SelectionCompleteButtonNotification()

        return PokemonCursorNotification(
            scene=PokemonCursorScene.SELECTION,
            cursor=cursor,
        )

    def _handle_command(self, image: MatLike) -> CommandCursorNotification:
        return CommandCursorNotification(cursor=self._command_reader.read(image))

    async def _handle_command_move(self, image: MatLike) -> MoveCursorNotification:
        selection = await self._move_reader.read_selected(
            ImageScene.COMMAND_MOVE,
            image,
        )
        if not selection:
            return MoveCursorNotification(cursor=None)

        idx, move = selection
        return MoveCursorNotification(cursor=Cursor(index=idx, content=move))

    async def _handle_command_pokemon(
        self,
        image: MatLike,
    ) -> PokemonCursorNotification:
        cursor = await self._pokemon_reader.read(
            image,
            PokemonCursorScene.COMMAND_POKEMON,
            team=self._ally_team.current or None,
        )
        return PokemonCursorNotification(
            scene=PokemonCursorScene.COMMAND_POKEMON,
            cursor=cursor,
        )
