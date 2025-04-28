from typing import Optional
from unittest.mock import Mock, NonCallableMock, sentinel

import pytest
from pytest_mock import MockerFixture

from pkscrd.core.terastal.model import (
    TeraType,
    TeraTypeDetection,
    TeraTypeDetectionSummary,
)
from pkscrd.core.terastal.service.terastal import (
    TerastalDetector,
    summarize_tera_type_detections,
)
from pkscrd.core.terastal.service.teratype import TeraTypeDetector
from pkscrd.core.terastal.service.omen import TerastalOmenDetector


class TestTerastalDetector:

    @pytest.fixture
    def omen_detector(self) -> NonCallableMock:
        mock = NonCallableMock(TerastalOmenDetector)
        mock.detect.return_value = False
        return mock

    @pytest.fixture
    def type_detector(self) -> NonCallableMock:
        mock = NonCallableMock(TeraTypeDetector)
        mock.detect.return_value = []
        return mock

    @pytest.fixture
    def summarize(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            "pkscrd.core.terastal.service.terastal.summarize_tera_type_detections",
            return_value=sentinel.summary,
        )

    @pytest.fixture
    def detector(
        self,
        omen_detector: NonCallableMock,
        type_detector: NonCallableMock,
    ) -> TerastalDetector:
        return TerastalDetector(
            omen_detector,
            type_detector,
            buffer_size=2,
            max_omen_wait_count=2,
        )

    def test_前兆を指定回数を超えて待つと判定中状態が解除される(
        self,
        detector: TerastalDetector,
        omen_detector: NonCallableMock,
        type_detector: NonCallableMock,
    ):
        # 初期状態は非判定中
        assert not detector.is_detecting

        # 前兆判定ではないときは判定を開始しない
        assert not detector.detect(sentinel.image)
        assert not detector.is_detecting

        # ここから前兆入り
        omen_detector.detect.return_value = True

        assert not detector.detect(sentinel.image)
        assert detector.is_detecting
        assert not detector.detect(sentinel.image)
        assert detector.is_detecting
        assert not detector.detect(sentinel.image)
        assert not detector.is_detecting

        assert omen_detector.detect.call_count == 4
        omen_detector.detect.assert_called_with(sentinel.image)
        type_detector.detect.assert_not_called()

    def test_前兆が切れてから指定回数までのスコアの合計を返す(
        self,
        detector: TerastalDetector,
        omen_detector: NonCallableMock,
        type_detector: NonCallableMock,
        summarize: Mock,
    ):
        omen_detector.detect.return_value = True
        assert not detector.detect(sentinel.image)

        # 前兆を抜ける
        omen_detector.detect.return_value = False
        type_detector.detect.return_value = [
            TeraTypeDetection(TeraType.FIRE, 1.0),
            TeraTypeDetection(TeraType.WATER, 2.0),
        ]

        assert not detector.detect(sentinel.image)
        assert detector.is_detecting

        type_detector.detect.return_value = [
            TeraTypeDetection(TeraType.WATER, 1.0),
            TeraTypeDetection(TeraType.ELECTRIC, 2.0),
        ]
        assert (
            detector.detect(
                sentinel.image,
                map_func=sentinel.map_func,
            )
            is sentinel.summary
        )
        assert not detector.is_detecting

        assert omen_detector.detect.call_count == 2
        assert type_detector.detect.call_count == 2
        type_detector.detect.assert_called_with(
            sentinel.image,
            map_func=sentinel.map_func,
        )
        summarize.assert_called_once_with(
            [
                TeraTypeDetection(TeraType.WATER, 3.0),
                TeraTypeDetection(TeraType.ELECTRIC, 2.0),
                TeraTypeDetection(TeraType.FIRE, 1.0),
            ],
        )


class Test_summarize_tera_type_detections:

    @pytest.mark.parametrize(
        ("detections", "expected"),
        (
            ([], None),
            (
                [
                    TeraTypeDetection(TeraType.FIRE, 1.0),
                    TeraTypeDetection(TeraType.WATER, 0.752),
                    TeraTypeDetection(TeraType.ELECTRIC, 0.751),
                    TeraTypeDetection(TeraType.GRASS, 0.75),
                ],
                TeraTypeDetectionSummary(
                    primary=TeraTypeDetection(TeraType.FIRE, 1.0),
                    possible=[
                        TeraTypeDetection(TeraType.WATER, 0.752),
                        TeraTypeDetection(TeraType.ELECTRIC, 0.751),
                    ],
                ),
            ),
        ),
    )
    def test(
        self,
        detections: list[TeraTypeDetection],
        expected: Optional[TeraTypeDetectionSummary],
    ):
        assert summarize_tera_type_detections(detections) == expected
