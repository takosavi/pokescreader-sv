import contextlib
from typing import Optional, Iterator

from pkscrd.app.settings.model import (
    NotificationSettings,
    BouyomichanSettings,
    VoicevoxSettings,
    AudioSettings,
)
from pkscrd.core.notification.service import (
    Talker,
    Notifier,
    Messenger,
    AllyHpFormatter,
    AllyHpFormat,
)
from pkscrd.core.pokemon.repos import load_pokemons
from pkscrd.core.pokemon.service import PokemonMapper
from pkscrd.core.tolerance.model import ToleranceCallback
from .talker import using_talker


def create_notifier(notification: NotificationSettings, talker: Talker) -> Notifier:
    messenger = Messenger(
        ally_hp_formatter=AllyHpFormatter(AllyHpFormat(notification.ally_hp_format)),
        pokemon_mapper=PokemonMapper(load_pokemons()),
    )
    return Notifier(messenger, talker)


@contextlib.contextmanager
def using_notifier(
    notification: NotificationSettings,
    bouyomichan: BouyomichanSettings,
    voicevox: VoicevoxSettings,
    audio: AudioSettings,
    *,
    bouyomichan_tolerance_callback: Optional[ToleranceCallback] = None,
    voicevox_tolerance_callback: Optional[ToleranceCallback] = None,
) -> Iterator[Notifier]:
    with using_talker(
        notification=notification,
        bouyomichan=bouyomichan,
        voicevox=voicevox,
        audio=audio,
        bouyomichan_tolerance_callback=bouyomichan_tolerance_callback,
        voicevox_tolerance_callback=voicevox_tolerance_callback,
    ) as talker:
        yield create_notifier(notification, talker)
