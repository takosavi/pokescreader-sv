from unittest.mock import AsyncMock, Mock, call

import pytest

from pkscrd.core.tolerance.model import ToleranceEvent, FatalError
from pkscrd.core.tolerance.service import AsyncTolerance, Tolerance


class TestTolerance:

    @pytest.fixture
    def callback(self) -> Mock:
        return Mock()

    def test_警告回数ごとに警告イベントを発する(self, callback: Mock) -> None:
        sut = Tolerance(callback=callback, warning_count=2)

        res = sut.handle(Mock(side_effect=RuntimeError("error 1")))
        assert str(res.failure()) == "error 1"
        callback.assert_not_called()

        res = sut.handle(Mock(side_effect=RuntimeError("error 2")))
        assert str(res.failure()) == "error 2"
        callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_WARNING)

        callback.reset_mock()

        sut.handle(Mock(side_effect=RuntimeError()))
        callback.assert_not_called()

        sut.handle(Mock(side_effect=RuntimeError()))
        callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_WARNING)

    def test_致命的回数に達すると致命的イベントを起動し_FatalErrorを送出する(
        self,
        callback: Mock,
    ) -> None:
        sut = Tolerance(callback=callback, fatal_count=2)

        sut.handle(Mock(side_effect=RuntimeError("error 1")))
        callback.assert_not_called()

        with pytest.raises(FatalError):
            sut.handle(Mock(side_effect=RuntimeError()))
        callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_FATAL)

        callback.reset_mock()

        with pytest.raises(FatalError):
            sut.handle(Mock(side_effect=RuntimeError()))
        callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_FATAL)


class TestAsyncTolerance:

    @pytest.fixture
    def callback(self) -> Mock:
        return Mock()

    class Test_リカバリなし:

        @pytest.mark.asyncio
        async def test_警告回数ごとに警告イベントを発する(
            self,
            callback: Mock,
        ) -> None:
            sut = AsyncTolerance(event_handler=callback, warning_count=2)

            res = await sut.handle(AsyncMock(side_effect=RuntimeError("error 1")))
            assert str(res.failure()) == "error 1"
            callback.assert_not_called()

            res = await sut.handle(AsyncMock(side_effect=RuntimeError("error 2")))
            assert str(res.failure()) == "error 2"
            callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_WARNING)

            callback.reset_mock()

            await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_not_called()

            await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_WARNING)

        @pytest.mark.asyncio
        async def test_致命的回数に達すると致命的イベントを起動し_FatalErrorを送出する(
            self,
            callback: Mock,
        ) -> None:
            sut = AsyncTolerance(event_handler=callback, fatal_count=2)

            await sut.handle(AsyncMock(side_effect=RuntimeError("error 1")))
            callback.assert_not_called()

            with pytest.raises(FatalError):
                await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_FATAL)

            callback.reset_mock()

            with pytest.raises(FatalError):
                await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_FATAL)

    class Test_リカバリあり:

        @pytest.fixture
        def recovery(self) -> AsyncMock:
            return AsyncMock()

        @pytest.fixture
        def sut(self, callback: Mock, recovery: AsyncMock) -> AsyncTolerance:
            return AsyncTolerance(
                event_handler=callback,
                warning_count=1,
                recovery=recovery,
            )

        @pytest.mark.asyncio
        async def test_警告と同時にリカバリする(
            self,
            sut: AsyncTolerance,
            callback: Mock,
            recovery: AsyncMock,
        ) -> None:
            recovery.return_value = True
            await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_called_once_with(ToleranceEvent.ERROR_COUNT_WARNING)
            recovery.assert_called_once_with()

        @pytest.mark.asyncio
        async def test_リカバリが失敗するとリカバリ失敗イベントを発し_FatalErrorを送出する(
            self,
            sut: AsyncTolerance,
            callback: Mock,
            recovery: AsyncMock,
        ) -> None:
            recovery.return_value = False
            with pytest.raises(FatalError):
                await sut.handle(AsyncMock(side_effect=RuntimeError()))
            callback.assert_has_calls(
                (
                    call(ToleranceEvent.ERROR_COUNT_WARNING),
                    call(ToleranceEvent.RECOVERY_FAILED),
                )
            )
            recovery.assert_called_once_with()
