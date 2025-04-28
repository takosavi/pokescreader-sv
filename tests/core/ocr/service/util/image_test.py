import cv2.typing
import numpy as np
from pytest import mark

from pkscrd.core.ocr.service.util.image import crop_by_mask


class Test_crop_by_mask:

    _CASES = {
        "標準的": (
            np.reshape(np.arange(27, dtype=np.uint8), (3, 3, 3)),
            np.array([[0, 0, 0], [0, 255, 0], [0, 0, 0]], dtype=np.uint8),
            0,
            np.array([[[12, 13, 14]]], dtype=np.uint8),
            np.array([[255]], dtype=np.uint8),
        ),
        "バッファ付き": (
            np.reshape(np.arange(75, dtype=np.uint8), (5, 5, 3)),
            np.array(
                [
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 255, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                ],
                dtype=np.uint8,
            ),
            1,
            np.array(
                [
                    [[18, 19, 20], [21, 22, 23], [24, 25, 26]],
                    [[33, 34, 35], [36, 37, 38], [39, 40, 41]],
                    [[48, 49, 50], [51, 52, 53], [54, 55, 56]],
                ],
                dtype=np.uint8,
            ),
            np.array([[0, 0, 0], [0, 255, 0], [0, 0, 0]], dtype=np.uint8),
        ),
        "バッファは元のサイズを超えない": (
            np.array([[[1, 2, 3]]], dtype=np.uint8),
            np.array([[255]], dtype=np.uint8),
            1,
            np.array([[[1, 2, 3]]], dtype=np.uint8),
            np.array([[255]], dtype=np.uint8),
        ),
        "マスクがすべて0のとき, バッファに関わらず空行列を返す": (
            np.reshape(np.arange(75, dtype=np.uint8), (5, 5, 3)),
            np.zeros((5, 5, 3), dtype=np.uint8),
            1,
            np.zeros((0, 0, 3), dtype=np.uint8),
            np.zeros((0, 0), dtype=np.uint8),
        ),
    }

    @mark.parametrize(
        ("image", "mask", "buffer", "expected_image", "expected_mask"),
        _CASES.values(),
        ids=_CASES.keys(),
    )
    def test(
        self,
        image: cv2.typing.MatLike,
        mask: cv2.typing.MatLike,
        buffer: int,
        expected_image: cv2.typing.MatLike,
        expected_mask: cv2.typing.MatLike,
    ):
        image_cropped, mask_cropped = crop_by_mask(image, mask, buffer=buffer)
        assert np.all(image_cropped == expected_image)
        assert np.all(mask_cropped == expected_mask)
