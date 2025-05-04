import cv2
from cv2.typing import MatLike
from returns.result import Result, ResultE

from pkscrd.core.screen.service import ScreenFetcher


class DirectScreenFetcher(ScreenFetcher):

    def __init__(self) -> None:
        # TODO インデックスを選ぶ
        # TODO release する
        # TODO リカバリ実装を入れる
        # TODO 接続エラーをユーザに通知する
        self._capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        if not self._capture.isOpened():
            raise RuntimeError("Failed to open capture")

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    async def fetch(self) -> ResultE[MatLike]:
        ret, frame = self._capture.read()
        if not ret:
            return Result.from_failure(RuntimeError("Failed to read a frame"))
        return Result.from_value(frame)
