import os

import cv2
import numpy as np

from pkscrd.core.terastal.model import TeraType
from pkscrd.core.terastal.service.teratype import TeraTypeDetector


class TestTeraTypeDetector:
    _WHITE = np.zeros((1080, 1920, 3), dtype=np.uint8)
    _WHITE[:, :, :] = np.uint8(255)

    def test_build_model_正常系(self, tempdir: str) -> None:
        os.mkdir(os.path.join(tempdir, "fire"))
        cv2.imwrite(os.path.join(tempdir, "fire", "example.jpg"), self._WHITE)

        models = list(TeraTypeDetector.build_model(tempdir))

        assert len(models) == 1
        assert models[0][0] is TeraType.FIRE
        expected = np.zeros((256, 256), dtype=np.float32)
        expected[0, 0] = np.float32(2_073_600)
        assert np.array_equal(models[0][1], expected)
