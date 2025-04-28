from abc import ABC, abstractmethod


class Talker(ABC):
    """テキストを読み上げる"""

    @abstractmethod
    def __call__(self, text: str) -> None: ...
