from queue import Full, Queue

from loguru import logger

from pkscrd.core.notification.service.talker import Talker


class QueuingTalker(Talker):
    """
    発話内容を `queue` に追加する Talker.
    実体である Talker の遅延が大きいとき, メインスレッドの遅延を緩和するために使用する.
    代わりにエラーハンドリングは甘くなるので, 実体である Talker で十分に行うこと.
    """

    def __init__(self, queue: Queue[str]):
        self._queue = queue

    def __call__(self, text: str) -> None:
        try:
            self._queue.put_nowait(text)
        except Full:
            logger.warning(
                "発話待ちが多すぎるため, 発話がスキップされました. 発話内容: {}",
                text,
            )
