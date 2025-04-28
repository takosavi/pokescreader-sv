from pkscrd.core.notification.infra.bouyomichan import BouyomichanClient
from pkscrd.core.notification.service.talker import Talker
from pkscrd.core.tolerance.service import Tolerance


class BouyomichanTalker(Talker):
    """棒読みちゃんを使ってテキストを読み上げる."""

    def __init__(
        self,
        client: BouyomichanClient,
        tolerance: Tolerance,
        *,
        speed: int = 150,
    ):
        self._client = client
        self._monitor = tolerance
        self._speed = speed

    def __call__(self, text: str) -> None:
        self._monitor.handle(lambda: self._client.talk(text, speed=self._speed))
