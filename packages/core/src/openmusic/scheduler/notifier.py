"""Webhook notification support for scheduled jobs.

Supports Telegram Bot API and Discord webhooks for sending
notifications on job success, failure, or start.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class NotificationEvent(Enum):
    """Events that can trigger a notification."""

    ON_START = "on_start"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"


@dataclass
class NotifierConfig:
    """Configuration for webhook notifications."""

    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    discord_webhook_url: Optional[str] = None

    # Which events trigger notifications (all by default)
    notify_on: set[NotificationEvent] = field(
        default_factory=lambda: {
            NotificationEvent.ON_SUCCESS,
            NotificationEvent.ON_FAILURE,
        }
    )

    @property
    def is_configured(self) -> bool:
        """Check if at least one notification channel is configured."""
        return bool(
            (self.telegram_token and self.telegram_chat_id)
            or self.discord_webhook_url
        )


def _send_telegram(
    token: str, chat_id: str, message: str, parse_mode: str = "HTML"
) -> bool:
    """Send a message via Telegram Bot API."""
    try:
        import requests  # type: ignore
    except ImportError:
        logger.warning("requests library not available, cannot send Telegram notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            logger.info("Telegram notification sent successfully")
            return True
        else:
            logger.warning(f"Telegram API returned error: {result}")
            return False
    except Exception as e:
        logger.warning(f"Failed to send Telegram notification: {e}")
        return False


def _send_discord(webhook_url: str, message: str) -> bool:
    """Send a message via Discord webhook."""
    try:
        import requests  # type: ignore
    except ImportError:
        logger.warning("requests library not available, cannot send Discord notification")
        return False

    payload = {
        "content": message,
        "allowed_mentions": {"parse": []},
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Discord notification sent successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to send Discord notification: {e}")
        return False


def _format_message(
    event: NotificationEvent,
    job_name: str,
    command: str,
    output: Optional[str] = None,
    error: Optional[str] = None,
) -> str:
    """Format a notification message based on the event."""
    emoji_map = {
        NotificationEvent.ON_START: "▶️",
        NotificationEvent.ON_SUCCESS: "✅",
        NotificationEvent.ON_FAILURE: "❌",
    }
    emoji = emoji_map.get(event, "ℹ️")

    title_map = {
        NotificationEvent.ON_START: "Job Started",
        NotificationEvent.ON_SUCCESS: "Job Completed",
        NotificationEvent.ON_FAILURE: "Job Failed",
    }
    title = title_map.get(event, "Job Update")

    msg = f"{emoji} <b>OpenMusic — {title}</b>\n"
    msg += f"📋 <b>Job:</b> {job_name}\n"
    msg += f"⚙️ <b>Command:</b> <code>{command}</code>\n"

    if output:
        max_output = 500
        truncated = output[:max_output]
        if len(output) > max_output:
            truncated += "..."
        msg += f"\n<pre>{truncated}</pre>\n"

    if error:
        msg += f"\n🚨 <b>Error:</b>\n<pre>{error[:500]}</pre>\n"

    return msg


def notify(
    config: NotifierConfig,
    event: NotificationEvent,
    job_name: str,
    command: str,
    output: Optional[str] = None,
    error: Optional[str] = None,
) -> bool:
    """Send a notification through configured channels.

    Args:
        config: Notifier configuration.
        event: The event that triggered this notification.
        job_name: Human-readable name for the job.
        command: The command that was executed.
        output: Optional command output.
        error: Optional error message.

    Returns:
        True if at least one channel sent successfully.
    """
    if not config.is_configured:
        logger.debug("No notification channels configured, skipping")
        return False

    if event not in config.notify_on:
        logger.debug(f"Notification for {event.value} is disabled in config")
        return False

    message = _format_message(event, job_name, command, output, error)
    success = False

    if config.telegram_token and config.telegram_chat_id:
        if _send_telegram(config.telegram_token, config.telegram_chat_id, message):
            success = True

    if config.discord_webhook_url:
        if _send_discord(config.discord_webhook_url, message):
            success = True

    return success
