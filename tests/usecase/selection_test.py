from unittest.mock import Mock, NonCallableMock, sentinel

from pytest import fixture, mark
from pytest_mock import MockerFixture

from pkscrd.core.notification.model import SelectionNotification, SelectionItem
from pkscrd.core.pokemon.model import PokemonId
from pkscrd.usecase.selection import SelectionUseCase
from pkscrd.core.scene.model import ImageScene
from pkscrd.usecase.team import TeamUseCase


class TestSelectionUseCase:

    @fixture(autouse=True)
    def recognize(self, mocker: MockerFixture) -> Mock:
        return mocker.patch("pkscrd.usecase.selection.recognize_selection")

    @fixture
    def ally_team(self) -> Mock:
        mock = NonCallableMock(TeamUseCase)
        mock.current = []
        return mock

    @fixture
    def sut(self, ally_team: Mock) -> SelectionUseCase:
        return SelectionUseCase(ally_team)

    _NOT_SELECTION_CASES = {
        "選出中ではない": ImageScene.SELECTION_COMPLETE,
        "選出中のスタック画面": ImageScene.SELECTION_SUMMARY,
    }

    @mark.parametrize(
        "scene",
        _NOT_SELECTION_CASES.values(),
        ids=_NOT_SELECTION_CASES.keys(),
    )
    def test_選出画面以外は認識しない(
        self,
        sut: SelectionUseCase,
        recognize: Mock,
        scene: ImageScene,
    ):
        sut.handle(scene, sentinel.image)
        recognize.recognize.assert_not_called()

    def test_要求を受けたら更新後の選出でコールバックを呼び出す(
        self,
        sut: SelectionUseCase,
        recognize: Mock,
    ):
        recognize.return_value = [1]
        sut.request()
        assert sut.handle(ImageScene.SELECTION, sentinel.img) == SelectionNotification(
            items=[SelectionItem(index_in_team=1)],
        )

    def test_選出画面で選出を検出し_チームを使って情報を埋める(
        self,
        sut: SelectionUseCase,
        recognize: Mock,
        ally_team: Mock,
    ):
        recognize.return_value = [2, 0, 4]
        ally_team.current = [PokemonId(1, 2), PokemonId(3, 4), None, PokemonId(5, 6)]

        sut.request()
        assert sut.handle(ImageScene.SELECTION, sentinel.img) == SelectionNotification(
            items=[
                SelectionItem(index_in_team=2, pokemon_id=None),
                SelectionItem(index_in_team=0, pokemon_id=PokemonId(1, 2)),
                SelectionItem(index_in_team=4, pokemon_id=None),
            ],
        )
        recognize.assert_called_once_with(sentinel.img)

    def test_選出画面で規定回数選出なしを受け付けるまで直前の選出を返す(
        self,
        sut: SelectionUseCase,
        recognize: Mock,
    ):
        recognize.return_value = [1]
        expected_normally = SelectionNotification(
            items=[SelectionItem(index_in_team=1)],
        )

        sut.request()
        assert sut.handle(ImageScene.SELECTION, sentinel.img) == expected_normally

        recognize.return_value = []
        for _ in range(2):
            sut.request()
            assert sut.handle(ImageScene.SELECTION, sentinel.img) == expected_normally

        sut.request()
        assert sut.handle(ImageScene.SELECTION, sentinel.img) == SelectionNotification(
            items=[],
        )
