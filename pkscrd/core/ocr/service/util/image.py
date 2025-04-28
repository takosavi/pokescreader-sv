import enum
from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from pkscrd.core.ocr.model import LogFormat, TextColor

_DEFAULT_PADDING = 10


def optimize(
    image: MatLike,
    *,
    text_color: TextColor = TextColor.WHITE,
    uses_blur: bool = False,
    padding: int = _DEFAULT_PADDING,
    left_top_width: int = 0,
    left_top_height: int = 0,
    left_top_min_ratio: float = 0.00,
    left_top_max_ratio: float = 1.00,
) -> Optional[MatLike]:
    image, text_color_ = _convert_text_color(image.copy(), text_color)
    mask = _MASK_FUNCTIONS[text_color_](image)

    # 先頭の画素が極端に多いか少ない場合, 読み取り対象が存在しないものとする.
    if left_top_width and left_top_height:
        left_top = mask[:left_top_height, :left_top_width]
        left_top_total = left_top.shape[0] * left_top.shape[1]
        count = np.count_nonzero(left_top)
        if count < left_top_total * left_top_min_ratio:
            return None
        if count > left_top_total * left_top_max_ratio:
            return None

    image, mask = crop_by_mask(image, mask, buffer=_CROPPING_BUFFER)
    if not all(mask.shape):
        return None

    image[mask == 0] = np.uint8(0)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.normalize(
        image,
        None,  # type: ignore
        0.0,
        255.0,
        cv2.NORM_MINMAX,
    )

    if uses_blur:
        image = cv2.GaussianBlur(image, ksize=(3, 3), sigmaX=0.0)

    return cv2.copyMakeBorder(
        image,
        padding,
        padding,
        padding,
        padding,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0),
    )


def optimize_log(
    image: MatLike,
    text_color: TextColor,
    fmt: LogFormat,
    *,
    padding: int = _DEFAULT_PADDING,
) -> Optional[MatLike]:
    character_size = fmt.line_height - fmt.line_interval
    return optimize(
        _mask_ruby(image, fmt),
        text_color=text_color,
        padding=padding,
        left_top_width=character_size * 2,
        left_top_height=character_size,
        left_top_min_ratio=0.05,
        left_top_max_ratio=0.90,
    )


def crop_by_mask(
    image: MatLike,
    mask: MatLike,
    *,
    buffer: int = 0,
) -> tuple[MatLike, MatLike]:
    """
    マスクされている領域が小さくなるように, 最大 `buffer` ピクセルを残して切り出す.
    """
    result = np.where(mask > 0)
    if not result[0].size:
        return (
            np.zeros((0, 0, *image.shape[2:]), dtype=image.dtype),
            np.zeros((0, 0), dtype=mask.dtype),
        )

    top = max(np.min(result[0]).item() - buffer, 0)
    bottom = min(np.max(result[0]).item() + 1 + buffer, image.shape[0])
    left = max(np.min(result[1]).item() - buffer, 0)
    right = min(np.max(result[1]).item() + 1 + buffer, image.shape[1])
    return image[top:bottom, left:right].copy(), mask[top:bottom, left:right].copy()


class _TextColor(enum.Enum):
    WHITE = enum.auto()
    WHITE_AND_YELLOW = enum.auto()
    WHITE_AND_YELLOW_AND_RED = enum.auto()
    GREY = enum.auto()


_CROPPING_BUFFER = 5
_TEXT_COLOR_MAP = {
    TextColor.WHITE: _TextColor.WHITE,
    TextColor.WHITE_AND_YELLOW: _TextColor.WHITE_AND_YELLOW,
    TextColor.WHITE_AND_YELLOW_AND_RED: _TextColor.WHITE_AND_YELLOW_AND_RED,
    TextColor.GREY: _TextColor.GREY,
}
_WHITE_LOWER = np.array((192, 192, 192), dtype=np.uint8)
_WHITE_UPPER = np.array((255, 255, 255), dtype=np.uint8)
_GRAY_LOWER = np.array((128, 128, 128), dtype=np.uint8)
_YELLOW_HSV_LOWER = np.array((20, 0, 184), dtype=np.uint8)
_YELLOW_HSV_UPPER = np.array((39, 255, 255), dtype=np.uint8)
_RED_HSV_LOWER = np.array((160, 0, 184), dtype=np.uint8)
_RED_HSV_UPPER = np.array((179, 255, 255), dtype=np.uint8)


def _convert_text_color(
    image: MatLike,
    text_color: TextColor,
) -> tuple[MatLike, _TextColor]:
    if text_color is TextColor.BLACK:
        image = np.uint8(255) - image
        text_color = TextColor.GREY
    return image, _TEXT_COLOR_MAP[text_color]


def _mask_ruby(image: MatLike, fmt: LogFormat) -> MatLike:
    """ルビを黒で塗り潰した画像のコピーを返す."""
    return cv2.rectangle(
        image.copy(),
        (0, fmt.line_height - fmt.line_interval),
        (image.shape[1], fmt.line_height),
        (0, 0, 0),
        cv2.FILLED,
    )


def _mask_background_for_white_text(image: MatLike) -> MatLike:
    """白文字に対するマスクを作成する."""
    return cv2.inRange(image, _WHITE_LOWER, _WHITE_UPPER)


def _mask_background_for_white_yellow_text(image: MatLike) -> MatLike:
    """白文字・黄文字混合に対するマスクを作成する."""
    white_mask = _mask_background_for_white_text(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    yellow_mask = cv2.inRange(hsv, _YELLOW_HSV_LOWER, _YELLOW_HSV_UPPER)
    return cv2.bitwise_or(white_mask, yellow_mask)


def _mask_background_for_white_yellow_red_text(image: MatLike) -> MatLike:
    """白文字・黄文字・赤文字混合に対するマスクを作成する."""
    white_mask = _mask_background_for_white_text(image)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    yellow_mask = cv2.inRange(hsv, _YELLOW_HSV_LOWER, _YELLOW_HSV_UPPER)
    red_mask = cv2.inRange(hsv, _RED_HSV_LOWER, _RED_HSV_UPPER)
    return cv2.bitwise_or(cv2.bitwise_or(white_mask, yellow_mask), red_mask)


def _mask_background_for_gray_text(image: MatLike) -> MatLike:
    return cv2.inRange(image, _GRAY_LOWER, _WHITE_UPPER)


_MASK_FUNCTIONS = {
    _TextColor.WHITE: _mask_background_for_white_text,
    _TextColor.WHITE_AND_YELLOW: _mask_background_for_white_yellow_text,
    _TextColor.WHITE_AND_YELLOW_AND_RED: _mask_background_for_white_yellow_red_text,
    _TextColor.GREY: _mask_background_for_gray_text,
}
