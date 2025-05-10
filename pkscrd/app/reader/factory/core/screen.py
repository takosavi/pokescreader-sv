import asyncio
import contextlib
from typing import AsyncIterator, Iterator, Optional

from loguru import logger

from pkscrd.app.settings.model import CaptureDeviceSettings, ObsSettings, ScreenSettings
from pkscrd.app.settings.error import SettingsError
from pkscrd.core.screen.infra.device import CaptureDeviceClient
from pkscrd.core.screen.service import ScreenFetcher
from pkscrd.core.screen.service.impl.device import DeviceScreenFetcher
from pkscrd.core.screen.service.impl.obs import ObsRecovery, ObsScreenFetcher
from pkscrd.core.screen.infra.obs import ObsClient
from pkscrd.core.tolerance.model import ToleranceCallback
from pkscrd.core.tolerance.service import AsyncTolerance


@contextlib.asynccontextmanager
async def using_obs_screen_fetcher(
    settings: ObsSettings,
    *,
    tolerance_callback: Optional[ToleranceCallback] = None,
    warning_error_count: int = 5,
    fatal_error_count: int = 15,
    recovery_sleep_in_seconds: float = 5.0,
) -> AsyncIterator[ScreenFetcher]:
    """
    設定からインスタンスを作成する.

    Raises:
        ConfigurationError: 設定に問題がありそうなとき.
    """
    async with ObsClient.create(port=settings.port, password=settings.password) as obs:
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
            await obs.get_source_screenshot(settings.source)
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
        yield ObsScreenFetcher(obs, settings.source, tolerance)


@contextlib.contextmanager
def using_device_screen_fetcher(
    settings: CaptureDeviceSettings,
    *,
    tolerance_callback: Optional[ToleranceCallback] = None,
) -> Iterator[DeviceScreenFetcher]:
    with CaptureDeviceClient(settings.name) as client:
        res = client.ensure_connection()
        if res is None:
            raise SettingsError(
                "指定された映像キャプチャデバイスが見つかりませんでした."
                " デバイスが接続されているか, デバイス名が正しいか確認してください."
            )

        # ウォームアップを兼ねて初回読み込みを行う.
        if not res:
            raise SettingsError(
                "映像キャプチャデバイスに接続できませんでした."
                " 他のアプリケーションで使用されていないか確認してください."
                " OBS Studio と同時使用する場合, スクリーン設定を OBS Studio"
                " に変更することも検討してください."
            )

        # ウォームアップを兼ねて初回読み込みを行う.
        if client.read() is None:
            raise SettingsError("映像キャプチャデバイスから映像を取得できませんでした.")

        async def recover() -> bool:
            await asyncio.sleep(5)
            return bool(client.reconnect())

        tolerance = AsyncTolerance(
            event_handler=tolerance_callback,
            recovery=recover,
            warning_count=5,
            fatal_count=15,
        )
        yield DeviceScreenFetcher(client, tolerance)


@contextlib.asynccontextmanager
async def using_screen_fetcher(
    screen: ScreenSettings,
    obs: Optional[ObsSettings],
    capture: Optional[CaptureDeviceSettings],
    *,
    obs_tolerance_callback: Optional[ToleranceCallback] = None,
    capture_tolerance_callback: Optional[ToleranceCallback] = None,
) -> AsyncIterator[ScreenFetcher]:
    match screen.engine:
        case "obs":
            if not obs:
                raise SettingsError(
                    "OBS Studio 接続設定が見つかりません."
                    " 設定が正しいか確認するか, 他の接続方法を試してください."
                )
            async with using_obs_screen_fetcher(
                settings=obs,
                tolerance_callback=obs_tolerance_callback,
            ) as obs_screen_fetcher:
                yield obs_screen_fetcher
        case "capture-device":
            if not capture:
                raise SettingsError(
                    "映像キャプチャデバイス設定が見つかりません."
                    " 設定が正しいか確認するか, 他の接続方法を試してください."
                )
            with using_device_screen_fetcher(
                capture,
                tolerance_callback=capture_tolerance_callback,
            ) as device_screen_fetcher:
                yield device_screen_fetcher
