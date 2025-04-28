from unittest.mock import AsyncMock, Mock, NonCallableMock, call, sentinel

from pytest import fixture, mark
from pytest_mock import MockerFixture

from pkscrd.core.hp.model import HpScene, VisibleHp
from pkscrd.core.hp.service import AllyHpReader, OcrAllyHpReader


class TestAllyHpReader:

    @fixture
    def recognize_gauge_(self, mocker: MockerFixture) -> Mock:
        mock = mocker.patch("pkscrd.core.hp.service.recognize_gauge")
        mock.return_value = False
        return mock

    @fixture
    def ocr_reader(self) -> NonCallableMock:
        mock = NonCallableMock(OcrAllyHpReader)
        mock.read = AsyncMock(return_value=None)
        return mock

    @fixture
    def reader(self, ocr_reader: NonCallableMock) -> AllyHpReader:
        return AllyHpReader(ocr_reader)

    @mark.asyncio
    async def test_ゲージが認識できないとき_空のmapを返す(
        self,
        reader: AllyHpReader,
        recognize_gauge_: Mock,
        ocr_reader: NonCallableMock,
    ):
        assert not await reader.read(sentinel.image)
        recognize_gauge_.assert_has_calls(
            (
                call(sentinel.image, HpScene.COMMAND, is_opponent=False),
                call(sentinel.image, HpScene.MOVE, is_opponent=False),
            )
        )
        ocr_reader.read.assert_not_called()

    @mark.asyncio
    async def test_ゲージが認識できるとき_OCR結果を返す(
        self,
        reader: AllyHpReader,
        recognize_gauge_: Mock,
        ocr_reader: NonCallableMock,
    ):
        recognize_gauge_.return_value = True
        ocr_reader.read = AsyncMock(side_effect=(None, VisibleHp(0, 1)))

        assert await reader.read(sentinel.image) == {HpScene.MOVE: VisibleHp(0, 1)}
        ocr_reader.read.assert_has_calls(
            (
                call(sentinel.image, HpScene.COMMAND),
                call(sentinel.image, HpScene.MOVE),
            )
        )
