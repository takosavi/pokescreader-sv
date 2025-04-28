import concurrent.futures
from typing import Optional

from pkscrd.app.reader.controller.image import ImageController
from pkscrd.app.settings.model import RoutineSettings
from pkscrd.core.log.service import LogReader
from pkscrd.core.ocr.service import OcrEngine
from pkscrd.core.terastal.service import TerastalDetector
from pkscrd.usecase.ally import AllyUseCase
from pkscrd.usecase.cursor import CursorUseCase
from pkscrd.usecase.hp import OpponentHpUseCase, AllyHpUseCase
from pkscrd.usecase.log import LogUseCase
from pkscrd.usecase.move import MoveUseCase
from pkscrd.usecase.scene import SceneUseCase
from pkscrd.usecase.screenshot import ScreenshotUseCase
from pkscrd.usecase.selection import SelectionUseCase
from pkscrd.usecase.team import TeamUseCase


def create_image_controller(
    settings: RoutineSettings,
    ally: AllyUseCase,
    opponent_team: TeamUseCase,
    ally_team: TeamUseCase,
    selection: SelectionUseCase,
    opponent_hp: OpponentHpUseCase,
    ally_hp: AllyHpUseCase,
    move: MoveUseCase,
    cursor: CursorUseCase,
    screenshot: ScreenshotUseCase,
    executor: concurrent.futures.Executor,
    ocr: OcrEngine,
) -> ImageController:
    log: Optional[LogUseCase] = None
    if settings.notifies_log:
        log = LogUseCase.create(LogReader.create(ocr))

    terastal_detector: Optional[TerastalDetector] = None
    if settings.notifies_tera_type:
        terastal_detector = TerastalDetector.create()

    return ImageController(
        scene=SceneUseCase(
            opponent_team=opponent_team,
            ally_team=ally_team,
            opponent_hp=opponent_hp,
            ally_hp=ally_hp,
        ),
        ally=ally,
        opponent_team=opponent_team,
        ally_team=ally_team,
        selection=selection,
        opponent_hp=opponent_hp,
        ally_hp=ally_hp,
        move=move,
        cursor=cursor,
        screenshot=screenshot,
        executor=executor,
        log=log,
        terastal_detector=terastal_detector,
    )
