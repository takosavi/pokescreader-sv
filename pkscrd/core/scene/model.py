import enum
from typing import Optional


class ImageScene(enum.Enum):
    """画像が表現しているシーン."""

    UNKNOWN = enum.auto()
    SELECTION = enum.auto()
    SELECTION_SUMMARY = enum.auto()
    SELECTION_MOVES_AND_STATS = enum.auto()
    SELECTION_MEMORIES = enum.auto()
    SELECTION_COMPLETE = enum.auto()
    COMMAND = enum.auto()
    COMMAND_MOVE = enum.auto()
    COMMAND_POKEMON = enum.auto()
    COMMAND_POKEMON_SUMMARY = enum.auto()
    COMMAND_POKEMON_MOVES_AND_STATS = enum.auto()
    COMMAND_POKEMON_MEMORIES = enum.auto()
    COMMAND_CANCELING = enum.auto()
    COMMAND_TEAM = enum.auto()
    COMMAND_SITUATION = enum.auto()
    FIELD_MENU = enum.auto()
    LOBBY = enum.auto()


class SceneGroup(enum.Enum):
    """シーンが属する大まかな分類."""

    SELECTION = enum.auto()
    SELECTION_COMPLETE = enum.auto()
    COMMAND = enum.auto()


class Scene(enum.Enum):
    """プレイヤーが動画を通して認識するシーン."""

    UNKNOWN = enum.auto()
    SELECTION = enum.auto()
    SELECTION_SUMMARY = enum.auto()
    SELECTION_MOVES_AND_STATS = enum.auto()
    SELECTION_MEMORIES = enum.auto()
    SELECTION_COMPLETE = enum.auto()
    COMMAND = enum.auto()
    COMMAND_MOVE = enum.auto()
    COMMAND_POKEMON = enum.auto()
    COMMAND_POKEMON_SUMMARY = enum.auto()
    COMMAND_POKEMON_MOVES_AND_STATS = enum.auto()
    COMMAND_POKEMON_MEMORIES = enum.auto()
    COMMAND_CANCELING = enum.auto()
    COMMAND_TEAM = enum.auto()
    COMMAND_SITUATION = enum.auto()
    FIELD_MENU = enum.auto()
    LOBBY = enum.auto()

    @property
    def group(self) -> Optional[SceneGroup]:
        return _SCENE_TO_SCENE_BASE.get(self)


class SceneChange(enum.Enum):
    """シーン変化."""

    # HACK グループと同じドメインのような気がする.

    SELECTION_START = enum.auto()
    SELECTION_COMPLETE = enum.auto()
    COMMAND_START = enum.auto()


_SCENE_TO_SCENE_BASE: dict[Scene, SceneGroup] = {
    Scene.SELECTION: SceneGroup.SELECTION,
    Scene.SELECTION_SUMMARY: SceneGroup.SELECTION,
    Scene.SELECTION_MOVES_AND_STATS: SceneGroup.SELECTION,
    Scene.SELECTION_MEMORIES: SceneGroup.SELECTION,
    Scene.SELECTION_COMPLETE: SceneGroup.SELECTION_COMPLETE,
    Scene.COMMAND: SceneGroup.COMMAND,
    Scene.COMMAND_MOVE: SceneGroup.COMMAND,
    Scene.COMMAND_POKEMON: SceneGroup.COMMAND,
    Scene.COMMAND_POKEMON_SUMMARY: SceneGroup.COMMAND,
    Scene.COMMAND_POKEMON_MOVES_AND_STATS: SceneGroup.COMMAND,
    Scene.COMMAND_POKEMON_MEMORIES: SceneGroup.COMMAND,
    Scene.COMMAND_CANCELING: SceneGroup.COMMAND,
    Scene.COMMAND_TEAM: SceneGroup.COMMAND,
    Scene.COMMAND_SITUATION: SceneGroup.COMMAND,
}
