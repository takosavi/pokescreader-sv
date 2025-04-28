import contextlib
from queue import Queue, Empty
from threading import Thread
from typing import Any, Callable, Generic, Iterator, TypeVar

_T = TypeVar("_T")


class EventHandler(Generic[_T]):

    def __init__(self, queue: Queue[_T], consumer: Callable[[_T], Any]):
        self._queue = queue
        self._consumer = consumer
        self._runnable = True

    def __call__(self) -> None:
        while self._runnable:
            # 終了時にループを抜けられるよう, タイムアウトしながら続行する.
            try:
                data = self._queue.get(timeout=0.5)
            except Empty:
                continue

            self._consumer(data)

    def set_runnable(self, runnable: bool) -> None:
        self._runnable = runnable


@contextlib.contextmanager
def watch_queue(queue: Queue[_T], consumer: Callable[[_T], Any]) -> Iterator[None]:
    handler = EventHandler(queue, consumer)
    thread = Thread(target=handler, daemon=True)
    thread.start()

    yield

    handler.set_runnable(False)
    thread.join()
