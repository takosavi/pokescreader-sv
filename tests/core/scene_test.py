from unittest.mock import Mock, sentinel

from pnlib.scene import Scene as PnScene
from pytest import fixture, mark
from pytest_mock import MockerFixture

from pkscrd.core.scene.model import ImageScene, Scene, SceneChange
from pkscrd.core.scene.service import (
    SceneChangeDetector,
    SceneDetector,
    SelectionStartDetector,
    recognize_image_scene,
)


class Test_recognize_image_scene:

    @fixture
    def recognize(self, mocker: MockerFixture) -> Mock:
        return mocker.patch("pkscrd.core.scene.service._recognize_scene")

    def test_pnlibがNoneを返すとき_UNKNOWNを返す(self, recognize: Mock):
        recognize.return_value = None
        assert recognize_image_scene(sentinel.image) is ImageScene.UNKNOWN
        recognize.assert_called_once_with(sentinel.image)

    def test_pnlibがNone以外を返すとき_対応する画像シーンを返す(self, recognize: Mock):
        recognize.return_value = PnScene.COMMAND
        assert recognize_image_scene(sentinel.image) is ImageScene.COMMAND


class TestSceneDetector:

    @fixture
    def sut(self) -> SceneDetector:
        return SceneDetector(count_to_reset=3)

    def test_UNKNOWN以外の画像シーンを渡すと_対応するシーンを返す(
        self,
        sut: SceneDetector,
    ):
        assert sut.detect(ImageScene.COMMAND) is Scene.COMMAND

    def test_リセット回数までUNKNOWNを渡し続けると_UNKNOWNを返す(
        self,
        sut: SceneDetector,
    ):
        assert sut.detect(ImageScene.COMMAND) is Scene.COMMAND
        assert sut.detect(ImageScene.UNKNOWN) is Scene.COMMAND
        assert sut.detect(ImageScene.UNKNOWN) is Scene.COMMAND
        assert sut.detect(ImageScene.UNKNOWN) is Scene.UNKNOWN


class TestSceneChangeDetector:

    @fixture
    def detector(self) -> SceneChangeDetector:
        return SceneChangeDetector()

    def test_選出開始イベントをキックする(self, detector: SceneChangeDetector):
        events = detector.detect(Scene.SELECTION)
        assert SceneChange.SELECTION_START in list(events)

    def test_選出終了イベントをキックする(self, detector: SceneChangeDetector):
        events = detector.detect(Scene.SELECTION_COMPLETE)
        assert SceneChange.SELECTION_COMPLETE in list(events)

    def test_行動選択開始をキックする(self, detector: SceneChangeDetector):
        events = detector.detect(Scene.COMMAND)
        assert list(events) == [SceneChange.COMMAND_START]


class TestSelectionStartDetector:

    def test_初回_画像シーンがSELECTIONでなければ検知しない(self):
        sut = SelectionStartDetector()
        assert not sut.detect(ImageScene.SELECTION_SUMMARY)

    def test_初回_画像シーンがSELECTIONであれば検知する(self):
        sut = SelectionStartDetector()
        assert sut.detect(ImageScene.SELECTION)

    def test_選出中は検知しない(self):
        sut = SelectionStartDetector()
        sut.detect(ImageScene.SELECTION)
        assert not sut.detect(ImageScene.SELECTION)

    @mark.parametrize("scene", (Scene.SELECTION, Scene.SELECTION_SUMMARY))
    def test_シーンが選出画面グループであれば_選出中状態は解除されない(
        self,
        scene: Scene,
    ):
        sut = SelectionStartDetector()
        sut.detect(ImageScene.SELECTION)
        sut.update(scene)
        assert not sut.detect(ImageScene.SELECTION)

    @mark.parametrize("scene", (Scene.UNKNOWN, Scene.SELECTION_COMPLETE))
    def test_シーンが選出画面グループでなければ_選出中状態が解除される(
        self,
        scene: Scene,
    ):
        sut = SelectionStartDetector()
        sut.detect(ImageScene.SELECTION)
        sut.update(scene)
        assert sut.detect(ImageScene.SELECTION)
