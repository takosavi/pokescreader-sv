from typing import Optional

from PySide6.QtWidgets import QWidget
from loguru import logger

from pkscrd.app.settings.model import Settings
from pkscrd.app.settings.error import SettingsFileNotFoundError, SettingsError
from pkscrd.app.settings.service import load_settings
from .controller import ConfigurationDialog, check_using_initial_settings
from .service import settings_to_conf, save


def run_configuration(parent: Optional[QWidget] = None) -> bool:
    """
    設定画面を表示する.

    Returns:
        設定が保存されたら True, そうでなければ False.
    """
    try:
        settings = load_settings()
    except SettingsFileNotFoundError:
        settings = _create_initial_settings()
    except (SettingsFileNotFoundError, SettingsError) as e:
        logger.opt(exception=e).debug("The setting file is broken.")
        if not check_using_initial_settings():
            return False
        settings = _create_initial_settings()

    # HACK デフォルト値がある値は初期値を任せたい.
    value = settings_to_conf(settings)
    widget = ConfigurationDialog(parent=parent, value=value, save=save)
    widget.exec_()
    return widget.is_saved


def _create_initial_settings() -> Settings:
    return Settings()
