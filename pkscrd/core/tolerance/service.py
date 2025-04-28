from queue import Queue, Full
from typing import Awaitable, Callable, Optional, TypeVar

from loguru import logger
from returns.result import Failure, ResultE, Success

from pkscrd.core.tolerance.model import FatalError, ToleranceEvent, ToleranceCallback

_T = TypeVar("_T")


class Tolerance:
    """
    一定量のエラーが連続しない限り処理を続行させる.
    """

    def __init__(
        self,
        *,
        callback: Optional[ToleranceCallback] = None,
        warning_count: int = 5,
        fatal_count: int = 15,
    ):
        """
        Args:
            callback:
                連続エラー検知イベントに対するハンドラ.
                未設定時はイベントに対して何もしない.
            warning_count:
                警告イベントを発する連続エラー回数.
            fatal_count:
                致命的問題イベントを発する連続エラー回数.
        """
        self._handler = callback or _do_nothing
        self._counter = _ErrorCounter(
            callback=callback,
            warning_count=warning_count,
            fatal_count=fatal_count,
        )

    def handle(self, func: Callable[[], _T]) -> ResultE[_T]:
        """
        エラーを監視しながら関数を実行し, その結果を返す.
        エラーが発生した場合, その連続回数に応じたイベントを呼び出すことがある.

        Raises:
            FatalError: エラーが致命的に連続したとき.
        """
        try:
            result = func()
            self._counter.reset()
            return Success(result)
        except Exception as e:
            self._counter.handle(e)
            return Failure(e)


class AsyncTolerance:
    """
    一定量のエラーが連続しない限り処理を続行させる. (非同期版)
    """

    def __init__(
        self,
        *,
        event_handler: Optional[ToleranceCallback] = None,
        warning_count: int = 5,
        fatal_count: int = 15,
        recovery: Optional[Callable[[], Awaitable[bool]]] = None,
    ):
        """
        Args:
            event_handler:
                連続エラー検知イベントに対するハンドラ.
                未設定時はイベントに対して何もしない.
            warning_count:
                警告イベントを発する連続エラー回数.
            fatal_count:
                致命的問題イベントを発する連続エラー回数.
            recovery:
                警告イベント発生時に実行するリカバリ処理.
                リカバリに成功したら True, 失敗したら False を返すこと.
                未指定時は何もしない.
        """
        self._handler = event_handler or _do_nothing
        self._counter = _ErrorCounter(
            callback=event_handler,
            warning_count=warning_count,
            fatal_count=fatal_count,
        )
        self._recovery = recovery or _return_true_async

    async def handle(self, func: Callable[[], Awaitable[_T]]) -> ResultE[_T]:
        """
        エラーを監視しながら関数を実行し, その結果を返す.
        エラーが発生した場合, その連続回数に応じたイベントを呼び出すことがある.

        Raises:
            FatalError: エラーが致命的に連続したとき. またはリカバリが失敗したとき.
        """
        try:
            result = await func()
            self._counter.reset()
            return Success(result)
        except Exception as e:
            needs_recovery = self._counter.handle(e)
            if needs_recovery and not await self._recovery():
                self._handler(ToleranceEvent.RECOVERY_FAILED)
                raise FatalError()
            return Failure(e)


class QueuingToleranceCallback:
    """
    連続エラーイベントに対し, メッセージをキューに追加するイベントハンドラ.
    別スレッドのイベントを把握したいときに使用することを推奨する.
    """

    def __init__(
        self,
        errors: Queue[str],
        error_count_fatal_message: str,
        recovery_failed_message: str,
    ):
        self._errors = errors
        self._error_count_fatal_message = error_count_fatal_message
        self._recovery_failed_message = recovery_failed_message

    def __call__(self, event: ToleranceEvent) -> None:
        match event:
            case ToleranceEvent.ERROR_COUNT_FATAL:
                message = self._error_count_fatal_message
            case ToleranceEvent.RECOVERY_FAILED:
                message = self._recovery_failed_message
            case _:
                return
        try:
            self._errors.put_nowait(message)
        except Full:
            logger.debug("The error message queue is full.")


class _ErrorCounter:
    """連続エラーを記録し, エラー回数に応じたイベントを起動する."""

    def __init__(
        self,
        callback: Optional[ToleranceCallback] = None,
        warning_count: int = 5,
        fatal_count: int = 15,
    ):
        self._handler = callback or _do_nothing
        self._count = 0
        self._warning_count = warning_count
        self._fatal_count = fatal_count

    def reset(self) -> None:
        """成功扱いで連続エラー回数をリセットする."""
        self._count = 0

    def handle(self, error: Exception) -> bool:
        """
        エラーを記録し, 連続回数に応じてイベントハンドラを呼び出す.

        Returns:
            リカバリが必要であれば True, そうでなければ False.
        Raises:
            FatalError: エラー回数が致命的に連続したとき.
        """
        self._count += 1
        logger.opt(exception=error).debug("Error count: {}", self._count)

        if self._count >= self._fatal_count:
            self._handler(ToleranceEvent.ERROR_COUNT_FATAL)
            raise FatalError()

        if self._count % self._warning_count == 0:
            self._handler(ToleranceEvent.ERROR_COUNT_WARNING)
            return True

        return False


def _do_nothing(*_args, **_kwargs) -> None: ...


async def _return_true_async(*_args, **_kwargs) -> bool:
    """非同期で True を返す. リカバリのダミー."""
    return True
