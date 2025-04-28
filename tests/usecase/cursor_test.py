from typing import Optional
from unittest.mock import AsyncMock, NonCallableMock, sentinel

import pytest

from pkscrd.core.cursor.model import Cursor, PokemonCursor, PokemonCursorScene
from pkscrd.core.cursor.service import CommandCursorReader, PokemonCursorReader
from pkscrd.core.move.model import Move
from pkscrd.core.move.service import MoveReader
from pkscrd.core.notification.model import (
    CommandCursorNotification,
    MoveCursorNotification,
    PokemonCursorNotification,
    SelectionCompleteButtonNotification,
    UnknownCursorNotification,
)
from pkscrd.core.scene.model import ImageScene
from pkscrd.usecase.cursor import CursorUseCase
from pkscrd.usecase.team import TeamUseCase


class TestCursorUseCase:

    @pytest.fixture
    def command_reader(self) -> NonCallableMock:
        return NonCallableMock(CommandCursorReader)

    @pytest.fixture
    def pokemon_reader(self) -> PokemonCursorReader:
        mock = NonCallableMock(PokemonCursorReader)
        mock.read = AsyncMock()
        return mock

    @pytest.fixture
    def move_reader(self) -> NonCallableMock:
        mock = NonCallableMock(MoveReader)
        mock.read_selected = AsyncMock()
        return mock

    @pytest.fixture
    def ally_team(self) -> NonCallableMock:
        mock = NonCallableMock(TeamUseCase)
        mock.current = [(1, 0), None]
        return mock

    @pytest.fixture
    def sut(
        self,
        command_reader: NonCallableMock,
        pokemon_reader: NonCallableMock,
        move_reader: NonCallableMock,
        ally_team: NonCallableMock,
    ) -> CursorUseCase:
        return CursorUseCase(
            command_reader=command_reader,
            pokemon_reader=pokemon_reader,
            move_reader=move_reader,
            ally_team=ally_team,
        )

    @pytest.mark.asyncio
    async def test_リクエストがなければ通知しない(self, sut: CursorUseCase):
        assert not await sut.handle(ImageScene.SELECTION, sentinel.img)

    _SELECTION_CASES = {
        "ポケモンカーソルなし": (None, SelectionCompleteButtonNotification()),
        "ポケモンカーソルあり": (
            Cursor(index=0, content=sentinel.selection_cursor),
            PokemonCursorNotification(
                scene=PokemonCursorScene.SELECTION,
                cursor=Cursor(index=0, content=sentinel.selection_cursor),
            ),
        ),
    }

    @pytest.mark.parametrize(
        ("cursor", "expected"),
        _SELECTION_CASES.values(),
        ids=_SELECTION_CASES.keys(),
    )
    @pytest.mark.asyncio
    async def test_選出画面では選出ポケモンカーソルを通知する(
        self,
        sut: CursorUseCase,
        pokemon_reader: NonCallableMock,
        ally_team: NonCallableMock,
        cursor: Optional[PokemonCursor],
        expected: PokemonCursorNotification | SelectionCompleteButtonNotification,
    ):
        pokemon_reader.read.return_value = cursor

        sut.request()
        assert await sut.handle(ImageScene.SELECTION, sentinel.img) == expected
        pokemon_reader.read.assert_called_once_with(
            sentinel.img,
            PokemonCursorScene.SELECTION,
            team=[(1, 0), None],
        )

    _COMMAND_CASES = {
        "カーソルなし": (None, CommandCursorNotification(cursor=None)),
        "カーソルあり": (
            Cursor(index=1, content=None),
            CommandCursorNotification(cursor=Cursor(index=1, content=None)),
        ),
    }

    @pytest.mark.parametrize(
        ("cursor", "expected"),
        _COMMAND_CASES.values(),
        ids=_COMMAND_CASES.keys(),
    )
    @pytest.mark.asyncio
    async def test_指示画面では指示カーソルを通知する(
        self,
        sut: CursorUseCase,
        command_reader: NonCallableMock,
        cursor: Optional[Cursor[None]],
        expected: CommandCursorNotification,
    ):
        command_reader.read.return_value = cursor

        sut.request()
        assert await sut.handle(ImageScene.COMMAND, sentinel.img) == expected
        command_reader.read.assert_called_once_with(sentinel.img)

    _MOVE_CURSOR_CASES = {
        "選択中の技なし": (None, MoveCursorNotification(cursor=None)),
        "選択中の技あり": (
            (1, sentinel.selected_move),
            MoveCursorNotification(
                cursor=Cursor(index=1, content=sentinel.selected_move),
            ),
        ),
    }

    @pytest.mark.parametrize(
        ("selection", "expected"),
        _MOVE_CURSOR_CASES.values(),
        ids=_MOVE_CURSOR_CASES.keys(),
    )
    @pytest.mark.asyncio
    async def test_技選択画面では技カーソルを通知する(
        self,
        sut: CursorUseCase,
        move_reader: NonCallableMock,
        selection: Optional[tuple[int, Optional[Move]]],
        expected: MoveCursorNotification,
    ):
        move_reader.read_selected.return_value = selection

        sut.request()
        assert await sut.handle(ImageScene.COMMAND_MOVE, sentinel.img) == expected
        move_reader.read_selected.assert_called_once_with(
            ImageScene.COMMAND_MOVE,
            sentinel.img,
        )

    @pytest.mark.asyncio
    async def test_ポケモン選択画面ではポケモンカーソルを通知する(
        self,
        sut: CursorUseCase,
        pokemon_reader: NonCallableMock,
    ):
        pokemon_reader.read.return_value = sentinel.cursor

        sut.request()
        assert await sut.handle(
            ImageScene.COMMAND_POKEMON,
            sentinel.img,
        ) == PokemonCursorNotification(
            scene=PokemonCursorScene.COMMAND_POKEMON,
            cursor=sentinel.cursor,
        )
        pokemon_reader.read.assert_called_once_with(
            sentinel.img,
            PokemonCursorScene.COMMAND_POKEMON,
            team=[(1, 0), None],
        )

    @pytest.mark.asyncio
    async def test_非対応画面では不明カーソルを通知する(self, sut: CursorUseCase):
        sut.request()
        actual = await sut.handle(ImageScene.UNKNOWN, sentinel.img)
        assert actual == UnknownCursorNotification()
