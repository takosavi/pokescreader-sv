from typing import Optional

from pkscrd.app.settings.model import ScreenshotSettings
from pkscrd.usecase.screenshot import ScreenshotUseCase


def create_screenshot_use_case(
    settings: ScreenshotSettings,
    *,
    dir_path: Optional[str] = None,
) -> ScreenshotUseCase:
    return ScreenshotUseCase(settings.buffer_size, dir_path=dir_path)
