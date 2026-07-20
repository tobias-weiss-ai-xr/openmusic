"""Notification configuration dataclass for completion alerts."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NotificationConfig:
    """Configuration for completion notifications.

    Supports webhook (HTTP POST) and/or email (SMTP) notification
    channels. All fields are optional — configure only the channels
    you want to use.
    """

    # -- Webhook --
    webhook_url: Optional[str] = None
    """URL to POST a JSON payload on completion (e.g. Slack, Discord)."""

    webhook_secret: Optional[str] = None
    """Optional shared secret for HMAC-SHA256 signing of webhook payloads."""

    # -- Email (SMTP) --
    email_to: Optional[str] = None
    """Recipient email address(es), comma-separated for multiple."""

    email_from: Optional[str] = None
    """Sender email address (default: openmusic@localhost)."""

    smtp_server: Optional[str] = None
    """SMTP relay hostname (e.g. smtp.gmail.com)."""

    smtp_port: int = 587
    """SMTP port (default: 587 for STARTTLS)."""

    smtp_username: Optional[str] = None
    """SMTP AUTH username (usually the full email address)."""

    smtp_password: Optional[str] = None
    """SMTP AUTH password or app-specific token."""

    smtp_use_tls: bool = True
    """Enable STARTTLS (default: True). Set False for SSL-only ports."""

    # -- Event filtering --
    notify_on_success: bool = True
    """Send notification when generation completes successfully."""

    notify_on_failure: bool = True
    """Send notification when generation fails."""

    # -- Convenience helpers --
    @classmethod
    def from_webhook_url(cls, url: str, secret: Optional[str] = None) -> "NotificationConfig":
        """Quick config for webhook-only notifications."""
        return cls(webhook_url=url, webhook_secret=secret)

    @property
    def is_configured(self) -> bool:
        """Whether at least one notification channel is configured."""
        return bool(self.webhook_url) or bool(self.email_to and self.smtp_server)
