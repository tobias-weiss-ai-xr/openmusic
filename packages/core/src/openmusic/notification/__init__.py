"""Notification module — completion alerts via webhook and email."""

from openmusic.notification.config import NotificationConfig
from openmusic.notification.notifier import Notifier, NotificationEvent, NotificationError

__all__ = [
    "NotificationConfig",
    "NotificationEvent",
    "NotificationError",
    "Notifier",
]
