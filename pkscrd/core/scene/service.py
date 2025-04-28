from collections import deque
from typing import Iterator

import cv2.typing
from pnlib.scene import Scene as PnScene, recognize_scene as _recognize_scene

from .model import ImageScene, Scene, SceneGroup, SceneChange


def recognize_image_scene(image: cv2.typing.MatLike) -> ImageScene:
    """画像シーンを認識する."""
    if pn_scene := _recognize_scene(image):
        return _PN_SCENE_MAP.get(pn_scene, ImageScene.UNKNOWN)
    return ImageScene.UNKNOWN


class SceneDetector:
    """画像シーンの連続から, 現在のシーンを検出する."""

    _IMAGE_SCENE_TO_SCENE: dict[ImageScene, Scene] = {
        ImageScene.UNKNOWN: Scene.UNKNOWN,
        ImageScene.SELECTION: Scene.SELECTION,
        ImageScene.SELECTION_SUMMARY: Scene.SELECTION_SUMMARY,
        ImageScene.SELECTION_MOVES_AND_STATS: Scene.SELECTION_MOVES_AND_STATS,
        ImageScene.SELECTION_MEMORIES: Scene.SELECTION_MEMORIES,
        ImageScene.SELECTION_COMPLETE: Scene.SELECTION_COMPLETE,
        ImageScene.COMMAND: Scene.COMMAND,
        ImageScene.COMMAND_MOVE: Scene.COMMAND_MOVE,
        ImageScene.COMMAND_POKEMON: Scene.COMMAND_POKEMON,
        ImageScene.COMMAND_POKEMON_SUMMARY: Scene.COMMAND_POKEMON_SUMMARY,
        ImageScene.COMMAND_POKEMON_MOVES_AND_STATS: Scene.COMMAND_POKEMON_MOVES_AND_STATS,
        ImageScene.COMMAND_POKEMON_MEMORIES: Scene.COMMAND_POKEMON_MEMORIES,
        ImageScene.COMMAND_CANCELING: Scene.COMMAND_CANCELING,
        ImageScene.COMMAND_TEAM: Scene.COMMAND_TEAM,
        ImageScene.COMMAND_SITUATION: Scene.COMMAND_SITUATION,
        ImageScene.FIELD_MENU: Scene.FIELD_MENU,
        ImageScene.LOBBY: Scene.LOBBY,
    }

    def __init__(self, *, count_to_reset: int = 10) -> None:
        self._buffer: deque[ImageScene] = deque(maxlen=count_to_reset)

    def detect(self, image_scene: ImageScene) -> Scene:
        """現在の画像シーンを受け取り, シーンを検出して返す."""
        self._buffer.append(image_scene)

        # 一瞬認識されないことはあるので, シーンなしはバッファ全数分検知してから返す.
        last = next(
            (s for s in reversed(self._buffer) if s is not ImageScene.UNKNOWN),
            ImageScene.UNKNOWN,
        )
        return self._IMAGE_SCENE_TO_SCENE.get(last, Scene.UNKNOWN)


class SceneChangeDetector:
    """シーンの連続から, シーン変化を検出する."""

    def __init__(self) -> None:
        self._curr: Scene = Scene.UNKNOWN

    def detect(self, curr: Scene) -> Iterator[SceneChange]:
        """現在のシーンを受け取り, シーン変化群を検出して返す."""
        prev = self._curr
        self._curr = curr
        return self._detect(prev, curr)

    @staticmethod
    def _detect(prev: Scene, curr: Scene) -> Iterator[SceneChange]:
        if (
            curr.group is SceneGroup.SELECTION
            and prev.group is not SceneGroup.SELECTION
        ):
            yield SceneChange.SELECTION_START

        if (
            curr.group is SceneGroup.SELECTION_COMPLETE
            and prev.group is not SceneGroup.SELECTION_COMPLETE
        ):
            yield SceneChange.SELECTION_COMPLETE

        if curr.group is SceneGroup.COMMAND and prev.group is not SceneGroup.COMMAND:
            yield SceneChange.COMMAND_START


class SelectionStartDetector:
    """
    初回または選出画面グループを一度離れたあと,
    選出画面に遷移したことを検知する.

    選出中は他の画面に遷移することがあるので,
    自動通知を 1 度だけ行うことを実現する.
    """

    def __init__(self) -> None:
        self._in_selection = False

    def detect(self, image_scene: ImageScene) -> bool:
        """
        選出開始を検出する.
        一度検出すると選出中状態となり, update() で解除されるまで再検知しない.
        """
        if not self._in_selection and image_scene is ImageScene.SELECTION:
            self._in_selection = True
            return True
        return False

    def update(self, scene: Scene) -> None:
        """選出中状態を更新する."""
        if scene.group is not SceneGroup.SELECTION:
            self._in_selection = False


_PN_SCENE_MAP: dict[PnScene, ImageScene] = {
    PnScene.SELECTION: ImageScene.SELECTION,
    PnScene.SELECTION_SUMMARY: ImageScene.SELECTION_SUMMARY,
    PnScene.SELECTION_MOVES_AND_STATS: ImageScene.SELECTION_MOVES_AND_STATS,
    PnScene.SELECTION_MEMORIES: ImageScene.SELECTION_MEMORIES,
    PnScene.SELECTION_COMPLETE: ImageScene.SELECTION_COMPLETE,
    PnScene.COMMAND: ImageScene.COMMAND,
    PnScene.COMMAND_MOVE: ImageScene.COMMAND_MOVE,
    PnScene.COMMAND_POKEMON: ImageScene.COMMAND_POKEMON,
    PnScene.COMMAND_POKEMON_SUMMARY: ImageScene.COMMAND_POKEMON_SUMMARY,
    PnScene.COMMAND_POKEMON_MOVES_AND_STATS: ImageScene.COMMAND_POKEMON_MOVES_AND_STATS,
    PnScene.COMMAND_POKEMON_MEMORIES: ImageScene.COMMAND_POKEMON_MEMORIES,
    PnScene.COMMAND_CANCELING: ImageScene.COMMAND_CANCELING,
    PnScene.COMMAND_TEAM: ImageScene.COMMAND_TEAM,
    PnScene.COMMAND_SITUATION: ImageScene.COMMAND_SITUATION,
    PnScene.FIELD_MENU: ImageScene.FIELD_MENU,
    PnScene.LOBBY: ImageScene.LOBBY,
}
