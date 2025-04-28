import dataclasses
from typing import Callable, Generic, Mapping, Optional, TypeVar

from loguru import logger
from cv2.typing import MatLike

from pkscrd.core.hp.model import HpScene, VisibleHp
from pkscrd.core.hp.service import AllyHpReader, recognize_opponent_hps
from pkscrd.core.notification.model import AllyHpNotification, OpponentHpNotification

_Value = TypeVar("_Value")


class MoveHpUseCase(Generic[_Value]):
    """
    行動中 HP 変動の通知を制御する.
    表示されたあと一度でも変化したあと, 変化が止まった, または消失したときの HP を通知する.
    """

    def __init__(self, eq: Optional[Callable[[_Value, _Value], bool]] = None) -> None:
        self._eq = eq or _default_eq

        self._prev: Optional[_Value] = None
        self._stable = False

    def handle(self, curr: Optional[_Value]) -> Optional[_Value]:
        prev = self._prev
        self._prev = curr

        if curr is None:
            # もともと表示されていなかったか, 安定状態だったときは何もしない.
            if prev is None or self._stable:
                return None

            # そうでなければ不安定状態から非表示になっているので通知する.
            logger.debug("A Move HP become disappeared.")
            return prev

        # 初回表示時: 安定状態に変更する.
        if prev is None:
            self._stable = True
            return None

        changed = not self._eq(prev, curr)
        if changed:  # 変化中は不安定状態となり, 即座に通知することはない.
            self._stable = False
            return None

        if self._stable:
            return None
        logger.debug("A Move HP become stable.")
        self._stable = True
        return curr


@dataclasses.dataclass(frozen=True)
class HpNotification(Generic[_Value]):
    value: Optional[_Value] = None


class HpUseCase(Generic[_Value]):
    """HP の通知を制御する."""

    def __init__(self, move: MoveHpUseCase[_Value]) -> None:
        self._move = move

        self._current: Optional[_Value] = None
        self._requested = False
        self._command_event_requested = False

    @property
    def current(self) -> Optional[_Value]:
        return self._current

    def request(self) -> None:
        """イベントを要求する."""
        self._requested = True

    def request_next_command(self) -> None:
        """次に指示画面の HP が読まれときの通知を要求する."""
        self._command_event_requested = True

    def handle(
        self,
        current: Mapping[HpScene, _Value],
    ) -> Optional[HpNotification[_Value]]:
        self._update(current)

        if not self._requested:
            return None
        self._requested = False
        return HpNotification(self.current)

    def _update(self, curr: Mapping[HpScene, _Value]) -> None:
        # 通知をするかどうかに関わらず, 更新だけはしておく.
        move = self._move.handle(curr.get(HpScene.MOVE))

        command = curr.get(HpScene.COMMAND)
        if command is not None:
            self._current = command
            if self._command_event_requested:
                self._command_event_requested = False
                self.request()
            return

        if move is not None:
            self._current = move
            self.request()


class OpponentHpUseCase:

    def __init__(self, inner: HpUseCase[float]):
        self._inner = inner

    @property
    def current(self) -> Optional[float]:
        return self._inner.current

    def request(self) -> None:
        self._inner.request()

    def request_next_command(self) -> None:
        self._inner.request_next_command()

    # HACK no async
    async def handle(self, image: MatLike) -> Optional[OpponentHpNotification]:
        n = self._inner.handle(recognize_opponent_hps(image))
        return None if n is None else OpponentHpNotification(ratio=n.value)

    @staticmethod
    def create() -> "OpponentHpUseCase":
        return OpponentHpUseCase(HpUseCase(move=MoveHpUseCase(eq=_opponent_eq)))


class AllyHpUseCase:

    def __init__(self, reader: AllyHpReader, inner: HpUseCase[VisibleHp]) -> None:
        self._reader = reader
        self._inner = inner

    def request(self) -> None:
        self._inner.request()

    def request_next_command(self) -> None:
        self._inner.request_next_command()

    async def handle(self, image: MatLike) -> Optional[AllyHpNotification]:
        n = self._inner.handle(await self._reader.read(image))
        if not n:
            return None
        return AllyHpNotification(value=n.value)

    @staticmethod
    def of(reader: AllyHpReader) -> "AllyHpUseCase":
        inner: HpUseCase[VisibleHp] = HpUseCase(move=MoveHpUseCase())
        return AllyHpUseCase(reader, inner)


def _default_eq(lhs: _Value, rhs: _Value) -> bool:
    return lhs == rhs


def _opponent_eq(lhs: float, rhs: float) -> bool:
    return abs(lhs - rhs) < 0.005
