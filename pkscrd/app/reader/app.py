import asyncio
import contextlib
import os
from concurrent.futures import ProcessPoolExecutor
from queue import Queue
from typing import Iterator, Optional

from PySide6.QtWidgets import QWidget, QMessageBox

from pkscrd.app.gui import set_window_icon
from pkscrd.app.settings.error import SettingsError
from pkscrd.app.settings.service import select_path, load_settings
from pkscrd.core.cursor.service import (
    CommandCursorReader,
    PokemonCursorReader,
    TextCursorReader,
)
from pkscrd.core.move.service import MoveReader
from pkscrd.core.hp.service import AllyHpReader
from pkscrd.usecase.ally import AllyUseCase
from pkscrd.usecase.cursor import CursorUseCase
from pkscrd.usecase.hp import AllyHpUseCase, OpponentHpUseCase
from pkscrd.usecase.move import MoveUseCase
from pkscrd.usecase.selection import SelectionUseCase
from pkscrd.usecase.team import TeamUseCase
from .agent import ImageProcess, ImageProcessAgent
from .controller.gui import GuiController, SettingsErrorDialog
from .error import (
    create_obs_tolerance_callback,
    create_bouyomichan_tolerance_callback,
    create_voicevox_tolerance_callback,
    watch_error,
)
from .factory.controller import create_image_controller
from .factory.core.notification import using_notifier
from .factory.core.ocr import create_ocr_engine
from .factory.core.screen import create_screen_fetcher
from .factory.core.screenshot import create_screenshot_use_case


@contextlib.contextmanager
def create_reader(
    loop: asyncio.AbstractEventLoop,
    max_workers: int = 3,
) -> Iterator[tuple[GuiController, ImageProcessAgent]]:
    """
    画面読み上げアプリケーションを作成する.

    Raises:
        SettingsError: 設定不備と思われるとき.
    """
    settings_path = select_path()
    settings = load_settings(select_path())
    errors: Queue[str] = Queue(maxsize=10)

    screen_fetcher = loop.run_until_complete(
        create_screen_fetcher(
            settings.obs,
            obs_tolerance_callback=create_obs_tolerance_callback(errors),
        )
    )
    ocr = loop.run_until_complete(create_ocr_engine(settings.ocr))

    opponent_team = TeamUseCase.of_opponent()
    opponent_hp = OpponentHpUseCase.create()
    ally_team = TeamUseCase.of_ally(
        uses_auto_callback=settings.routine.notifies_ally_team,
    )
    selection = SelectionUseCase(ally_team)
    ally_hp = AllyHpUseCase.of(AllyHpReader.create(ocr))
    ally = AllyUseCase(selection, ally_hp)
    move_reader = MoveReader.create(ocr)
    move = MoveUseCase(move_reader)
    cursor = CursorUseCase(
        command_reader=CommandCursorReader(),
        pokemon_reader=PokemonCursorReader(
            text_reader=(TextCursorReader(ocr)),
            ocr=ocr,
        ),
        move_reader=move_reader,
        ally_team=ally_team,
    )
    screenshot = create_screenshot_use_case(
        settings.screenshot,
        dir_path=os.path.dirname(settings_path),
    )

    gui = GuiController(
        opponent_team=opponent_team,
        opponent_hp=opponent_hp,
        ally=ally,
        move=move,
        cursor=cursor,
        screenshot=screenshot,
        uses_buttons=settings.gui.uses_buttons,
    )
    watch_error(gui, errors)

    with (
        ProcessPoolExecutor(max_workers) as executor,
        using_notifier(
            settings.notification,
            settings.bouyomichan,
            settings.voicevox,
            settings.audio,
            bouyomichan_tolerance_callback=create_bouyomichan_tolerance_callback(
                errors
            ),
            voicevox_tolerance_callback=create_voicevox_tolerance_callback(errors),
        ) as notifier,
    ):
        image = create_image_controller(
            settings.routine,
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
            ocr=ocr,
        )
        yield gui, ImageProcessAgent(ImageProcess(screen_fetcher, image, notifier))


def show_pnlib_error(parent: Optional[QWidget] = None) -> None:
    """
    pnlib 初期化エラーダイアログを表示する.
    """
    message_box = QMessageBox(parent)
    set_window_icon(message_box)
    message_box.setIcon(QMessageBox.Icon.Critical)
    message_box.setWindowTitle("起動エラー")
    message_box.setText(
        "起動に必要な情報の読み込みが失敗しました."
        " 何度も発生する場合, アプリが破損しているかもしれませんので,"
        " 一度アプリを消して再構成してください."
    )
    message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    message_box.exec_()


def run_settings_error(error: SettingsError) -> bool:
    """
    設定エラーダイアログを表示する.

    Args:
        error: 設定エラー例外
    Returns:
        設定変更が要求されたか.
    """
    dialog = SettingsErrorDialog(message=str(error))
    dialog.exec_()
    return dialog.needs_configuration
