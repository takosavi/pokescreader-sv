from unittest.mock import Mock, sentinel

from pytest import fixture
from pytest_mock import MockerFixture

from pkscrd.core.notification.model import TeamDirection, TeamNotification
from pkscrd.core.pokemon.model import PokemonId
from pkscrd.usecase.team import TeamUseCase
from pkscrd.core.scene.model import ImageScene


class TestTeamUseCase:

    class Test_自動通知あり:

        @fixture(autouse=True)
        def recognize(self, mocker: MockerFixture) -> Mock:
            mock = mocker.patch("pkscrd.usecase.team.recognize_opponent_team")
            mock.side_effect = (iter([PokemonId(1, 2)]), iter([PokemonId(3, 4)]))
            return mock

        @fixture
        def sut(self) -> TeamUseCase:
            return TeamUseCase.of_opponent()

        def test_リクエストがないとき_通知しない(
            self,
            sut: TeamUseCase,
            recognize: Mock,
        ):
            assert not sut.handle(ImageScene.SELECTION, sentinel.image)
            recognize.assert_not_called()

        def test_リクエストがあるとき_通知する(
            self,
            sut: TeamUseCase,
            recognize: Mock,
        ):
            sut.request()
            assert sut.handle(
                ImageScene.UNKNOWN,
                sentinel.image,
            ) == TeamNotification(direction=TeamDirection.OPPONENT, team=[])
            recognize.assert_not_called()

        def test_リクエストがなく_更新リクエストがあり_更新可能なシーンではない_更新せず通知もしない(
            self,
            sut: TeamUseCase,
            recognize: Mock,
        ):
            sut.request_update()
            assert not sut.handle(ImageScene.UNKNOWN, sentinel.image1)
            recognize.assert_not_called()

        def test_リクエストがなく_更新リクエストがあり_更新可能なシーンのとき_更新して通知する(
            self,
            sut: TeamUseCase,
            recognize: Mock,
        ):
            sut.request_update()
            assert sut.handle(
                ImageScene.SELECTION,
                sentinel.image1,
                map_func=sentinel.map_func,
            ) == TeamNotification(
                direction=TeamDirection.OPPONENT,
                team=[PokemonId(1, 2)],
            )
            recognize.assert_called_once_with(sentinel.image1, sentinel.map_func)

        def test_リクエストがあり_更新リクエストがあり_更新可能なシーンのとき_リクエストを更新時に消費する(
            self,
            sut: TeamUseCase,
        ):
            sut.request(with_types=True)
            sut.request_update()
            assert sut.handle(
                ImageScene.SELECTION,
                sentinel.image1,
            ) == TeamNotification(
                direction=TeamDirection.OPPONENT,
                team=[PokemonId(1, 2)],
                with_types=True,
            )

            assert not sut.handle(ImageScene.SELECTION, sentinel.image2)

    class Test_自動通知なし:

        @fixture(autouse=True)
        def recognize(self, mocker: MockerFixture) -> Mock:
            mock = mocker.patch("pkscrd.usecase.team.recognize_ally_team_for_selection")
            mock.side_effect = (iter([PokemonId(1, 2)]), iter([PokemonId(3, 4)]))
            return mock

        @fixture
        def sut(self) -> TeamUseCase:
            return TeamUseCase.of_ally(uses_auto_callback=False)

        def test_リクエストがなく_更新リクエストがあり_更新可能なシーンのとき_更新して通知しない(
            self,
            sut: TeamUseCase,
            recognize: Mock,
        ):
            sut.request_update()
            assert not sut.handle(
                ImageScene.SELECTION,
                sentinel.image1,
                map_func=sentinel.map_func,
            )
            recognize.assert_called_once_with(sentinel.image1, sentinel.map_func)
