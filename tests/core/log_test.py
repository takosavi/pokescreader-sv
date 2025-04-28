from pytest import fixture

from pkscrd.core.log.model import LogType, Log
from pkscrd.core.log.service import (
    LogStabilizer,
)


class TestLogStabilizer:

    @fixture
    def stabilizer(self) -> LogStabilizer:
        return LogStabilizer()

    def test_連続で同等ログが取得できたら一度だけ返す(self, stabilizer: LogStabilizer):
        assert not stabilizer.handle(Log(LogType.GENERAL, ["foo"]))
        assert stabilizer.handle(Log(LogType.GENERAL, ["foo"])) == Log(
            LogType.GENERAL,
            ["foo"],
        )
        assert not stabilizer.handle(Log(LogType.GENERAL, ["foo"]))
