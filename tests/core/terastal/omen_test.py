import os

import cv2
import numpy as np

from pkscrd.core.terastal.service.omen import TerastalOmenDetector


class TestTerastalOmenDetector:
    _WHITE = np.zeros((1080, 1920, 3), dtype=np.uint8)
    _WHITE[:, :, :] = np.uint8(255)

    def test_build_model(self, tempdir: str) -> None:
        os.mkdir(os.path.join(tempdir, "omen"))
        cv2.imwrite(
            os.path.join(tempdir, "omen", "terastal-omen-inner.png"),
            self._WHITE,
        )
        cv2.imwrite(
            os.path.join(tempdir, "omen", "terastal-omen-outer.png"),
            self._WHITE,
        )

        model = TerastalOmenDetector.build_model(tempdir)

        expected_mask = np.zeros((1080, 1920), dtype=np.uint8)
        expected_mask[:, :] = np.uint8(255)
        assert np.array_equal(model.mask_inner, expected_mask)
        assert np.array_equal(model.mask_outer, expected_mask)
