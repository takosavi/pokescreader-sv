from loguru import logger

from pkscrd.core.notification.model import Notification
from .messenger import Messenger
from .talker import Talker


class Notifier:
    """通知機能."""

    def __init__(self, messenger: Messenger, talker: Talker) -> None:
        self._messenger = messenger
        self._talker = talker

    def notify(self, notification: Notification) -> None:
        """通知する."""
        text = self._messenger.convert_to_text(notification)
        logger.debug("Notify: {}", text)
        self._talker(text)
