from typing import Optional

from loguru import logger

from pkscrd.app.settings.model import ObsSettings
from pkscrd.app.settings.error import SettingsError
from pkscrd.core.screen.service import ScreenFetcher
from pkscrd.core.screen.service.impl.obs import ObsRecovery, ObsScreenFetcher
from pkscrd.core.screen.infra.obs import ObsClient
from pkscrd.core.tolerance.model import ToleranceCallback
from pkscrd.core.tolerance.service import AsyncTolerance


async def create_screen_fetcher(
    config: ObsSettings,
    *,
    tolerance_callback: Optional[ToleranceCallback] = None,
    warning_error_count: int = 5,
    fatal_error_count: int = 15,
    recovery_sleep_in_seconds: float = 5.0,
) -> ScreenFetcher:
    """
    設定からインスタンスを作成する.

    Raises:
        ConfigurationError: 設定に問題がありそうなとき.
    """
    obs = ObsClient(port=config.port, password=config.password)
    if not await obs.ensure_connection():
        raise SettingsError(
            "OBS Studio との接続に失敗しました."
            " OBS Studio の WebSocket サーバが起動しているか,"
            " 接続設定 (特に port) が正しいか確認してください.",
        )
    if not await obs.ensure_identified():
        logger.debug("OBS Studio connection is not identified.")
        raise SettingsError(
            "OBS Studio との接続に失敗しました."
            " 接続設定 (特に password) が正しいか確認してください.",
        )

    # 一度お試しで映像取得してみる.
    try:
        await obs.get_source_screenshot(config.source)
    except Exception as error:
        logger.opt(exception=error).debug("Failed to get screenshot.")
        raise SettingsError(
            "OBS Studio からの映像取得が失敗しました."
            " 何度も失敗する場合, 映像ソースの設定 (source) が正しいか確認してください."
        )

    tolerance = AsyncTolerance(
        event_handler=tolerance_callback,
        recovery=ObsRecovery(obs, sleep_in_seconds=recovery_sleep_in_seconds),
        warning_count=warning_error_count,
        fatal_count=fatal_error_count,
    )
    return ObsScreenFetcher(obs, config.source, tolerance)
