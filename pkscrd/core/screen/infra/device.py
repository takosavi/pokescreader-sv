import dataclasses
import types
from typing import Iterator, Optional, Type

import cv2
from cv2.typing import MatLike
from cv2_enumerate_cameras import enumerate_cameras


class CaptureDeviceClient:
    """
    映像キャプチャデバイスとの接続クライアント.
    インデックス変化に耐えられるよう, 名前ベースで解決することが特徴.
    接続が切れた場合, 再接続できるようにしている.
    """

    def __init__(self, name: str) -> None:
        self._name = name
        self._capture: Optional[cv2.VideoCapture] = None
        self._api_preference = cv2.CAP_MSMF

    def ensure_connection(self) -> Optional[bool]:
        """
        デバイスとの接続を保証する.

        Returns:
            デバイスとの接続を保証できたら True.
            デバイスが見つかったものの接続ができなければ False.
            デバイスが見つからなければ None.
        """
        if self._capture and self._capture.isOpened():
            return True

        cam = next(
            (cam for cam in get_devices() if cam.name == self._name),
            None,
        )
        if cam is None:
            return None

        self._capture = cv2.VideoCapture(cam.index, _API_PREFERENCE)
        if not self._capture.isOpened():
            return False

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        return True

    def read(self) -> Optional[MatLike]:
        if not self._capture:
            return None
        ret, frame = self._capture.read()
        return frame if ret else None

    def reconnect(self) -> bool:
        if self._capture:
            self._capture.release()
        return self.ensure_connection()

    def __enter__(self) -> "CaptureDeviceClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[types.TracebackType],
    ) -> bool:
        if self._capture:
            self._capture.release()
        return False


@dataclasses.dataclass(frozen=True)
class Device:
    index: int
    name: str


def get_devices() -> Iterator[Device]:
    return (
        Device(index=cam.index, name=cam.name)
        for cam in enumerate_cameras(_API_PREFERENCE)
    )


_API_PREFERENCE = cv2.CAP_MSMF
