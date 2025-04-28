from abc import ABC, abstractmethod

from cv2.typing import MatLike
from returns.result import ResultE


class ScreenFetcher(ABC):
    """スクリーン映像を取得する."""

    @abstractmethod
    async def fetch(self) -> ResultE[MatLike]:
        """スクリーンを読み取り, 読み取り結果を返却する."""
