from unittest.mock import AsyncMock, NonCallableMock, sentinel

from pytest import fixture, mark
from pytest_mock import MockerFixture

from pkscrd.core.hp.model import HpScene, VisibleHp
from pkscrd.core.notification.model import OpponentHpNotification, AllyHpNotification
from pkscrd.usecase.hp import (
    AllyHpUseCase,
    HpNotification,
    HpUseCase,
    MoveHpUseCase,
    OpponentHpUseCase,
)
from pkscrd.core.hp.service import AllyHpReader


class TestMoveHpUseCase:

    @fixture
    def sut(self) -> MoveHpUseCase[int]:
        return MoveHpUseCase()

    def test_初回表示から変化がなければ通知しない(self, sut: MoveHpUseCase[int]):
        assert sut.handle(1) is None
        assert sut.handle(1) is None
        assert sut.handle(None) is None
        assert sut.handle(2) is None

    def test_初回表示から変化が停止したときに通知する(self, sut: MoveHpUseCase[int]):
        assert sut.handle(1) is None
        assert sut.handle(2) is None
        assert sut.handle(2) == 2
        assert sut.handle(2) is None

    def test_初回表示から変化して消えたときに通知する(self, sut: MoveHpUseCase[int]):
        assert sut.handle(1) is None
        assert sut.handle(0) is None
        assert sut.handle(None) == 0


class TestHpUseCase:

    @fixture
    def move(self) -> NonCallableMock:
        mock = NonCallableMock(MoveHpUseCase)
        mock.handle.return_value = None
        return mock

    @fixture
    def sut(self, move: NonCallableMock) -> HpUseCase[int]:
        return HpUseCase(move=move)

    def test_常に行動中HPを更新する(self, sut: HpUseCase[int], move: NonCallableMock):
        sut.handle({HpScene.COMMAND: 1, HpScene.MOVE: sentinel.value})
        move.handle.assert_called_once_with(sentinel.value)

    def test_コマンドHP表示があるとき_現在値を更新する(self, sut: HpUseCase[int]):
        assert sut.handle({HpScene.COMMAND: 1}) is None
        assert sut.current == 1

    def test_コマンドHP表示がないとき_行動HP通知があれば現在値を更新し_それを通知する(
        self,
        sut: HpUseCase[int],
        move: NonCallableMock,
    ):
        move.handle.return_value = 1

        assert sut.handle({}) == HpNotification(1)
        assert sut.current == 1
        move.handle.assert_called_once_with(None)

    def test_通知要求があれば_更新有無に関わらず現在値を通知する(
        self,
        sut: HpUseCase[int],
    ):
        sut.request()
        assert sut.handle({}) == HpNotification(None)

        assert sut.handle({HpScene.COMMAND: 1}) is None

        sut.request()
        assert sut.handle({}) == HpNotification(1)

    def test_指示画面HP通知の要求があれば_次に更新されたときに通知する(
        self,
        sut: HpUseCase[int],
    ):
        sut.request_next_command()
        assert sut.handle({}) is None
        assert sut.handle({HpScene.COMMAND: 1}) == HpNotification(1)

    def test_通知要求と指示画面HP通知要求が重なったら_1回だけ処理される(
        self,
        sut: HpUseCase[int],
    ):
        sut.request()
        sut.request_next_command()
        assert sut.handle({HpScene.COMMAND: 1}) == HpNotification(1)
        assert sut.handle({HpScene.COMMAND: 1}) is None


@mark.asyncio
async def test_OpponentHpUseCase(mocker: MockerFixture):
    recognize = mocker.patch("pkscrd.usecase.hp.recognize_opponent_hps")
    recognize.side_effect = (
        {HpScene.COMMAND: 0.5},
        {HpScene.COMMAND: 0.5},
        {},
        {HpScene.MOVE: 0.4},
        {HpScene.MOVE: 0.3},
        {HpScene.MOVE: 0.3049},
    )

    controller = OpponentHpUseCase.create()
    assert controller.current is None

    assert await controller.handle(sentinel.image) is None
    recognize.assert_called_once_with(sentinel.image)

    controller.request_next_command()
    assert await controller.handle(sentinel.image) == OpponentHpNotification(ratio=0.5)
    assert controller.current == 0.5

    controller.request()
    assert await controller.handle(sentinel.image) == OpponentHpNotification(ratio=0.5)

    # HP 読み込みや差分判定を inject した部分の確認
    assert await controller.handle(sentinel.image) is None
    assert await controller.handle(sentinel.image) is None
    assert await controller.handle(sentinel.image) == OpponentHpNotification(
        ratio=0.3049,
    )


@mark.asyncio
async def test_AllyHpUseCase():
    reader = NonCallableMock(AllyHpReader)
    reader.read = AsyncMock(return_value={HpScene.COMMAND: VisibleHp(current=0, max=1)})

    controller = AllyHpUseCase.of(reader)

    assert await controller.handle(sentinel.image) is None
    reader.read.assert_called_once_with(sentinel.image)

    controller.request_next_command()
    assert await controller.handle(sentinel.image) == AllyHpNotification(
        value=VisibleHp(current=0, max=1),
    )

    controller.request()
    assert await controller.handle(sentinel.image) == AllyHpNotification(
        value=VisibleHp(current=0, max=1),
    )
