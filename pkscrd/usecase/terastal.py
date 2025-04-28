from pkscrd.core.notification.model import TeraTypeNotification
from pkscrd.core.terastal.model import TeraTypeDetectionSummary


def notify_tera_type(summary: TeraTypeDetectionSummary) -> TeraTypeNotification:
    return TeraTypeNotification(
        primary=summary.primary.type,
        possible=[item.type for item in summary.possible],
    )
