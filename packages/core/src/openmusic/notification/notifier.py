"""Notifier — sends completion alerts via webhook and/or email."""

import hashlib
import hmac
import json
import logging
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from openmusic.notification.config import NotificationConfig

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Raised when a notification channel fails."""


@dataclass
class NotificationEvent:
    """Payload describing a pipeline completion event."""

    status: str  # "success" | "failure"
    title: str
    output_path: Optional[str] = None
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    segment_count: Optional[int] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "status": self.status,
            "title": self.title,
            "output_path": self.output_path,
            "video_id": self.video_id,
            "video_url": self.video_url,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "segment_count": self.segment_count,
        }
        if self.metadata:
            d.update(self.metadata)
        return {k: v for k, v in d.items() if v is not None}


class WebhookSender:
    """Sends JSON payload to a webhook URL."""

    def __init__(self, url: str, secret: Optional[str] = None):
        self.url = url
        self.secret = secret

    def send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        if self.secret:
            signature = hmac.new(
                self.secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Signature-256"] = signature

        req = Request(
            self.url,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=30) as resp:
                status = resp.status
                if status < 200 or status >= 300:
                    raise NotificationError(
                        f"Webhook returned HTTP {status}: {resp.read().decode()}"
                    )
                logger.info("Webhook notification sent (%s)", status)
        except URLError as e:
            raise NotificationError(f"Webhook request failed: {e}") from e


class EmailSender:
    """Sends plain-text email via SMTP."""

    def __init__(self, cfg: NotificationConfig):
        self.cfg = cfg

    def send(self, subject: str, body: str) -> None:
        to = self.cfg.email_to
        from_ = self.cfg.email_from or "openmusic@localhost"
        assert to, "No recipient configured"
        assert self.cfg.smtp_server, "No SMTP server configured"

        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = from_
        msg["To"] = to

        try:
            if self.cfg.smtp_use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.cfg.smtp_server, self.cfg.smtp_port) as server:
                    server.starttls(context=context)
                    if self.cfg.smtp_username:
                        server.login(self.cfg.smtp_username, self.cfg.smtp_password or "")
                    server.sendmail(from_, [addr.strip() for addr in to.split(",")], msg.as_string())
            else:
                # SSL-only (e.g. port 465)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.cfg.smtp_server, self.cfg.smtp_port, context=context) as server:
                    if self.cfg.smtp_username:
                        server.login(self.cfg.smtp_username, self.cfg.smtp_password or "")
                    server.sendmail(from_, [addr.strip() for addr in to.split(",")], msg.as_string())
            logger.info("Email notification sent to %s", to)
        except (smtplib.SMTPException, OSError) as e:
            raise NotificationError(f"Email send failed: {e}") from e


class Notifier:
    """Composite notifier that dispatches to all configured channels."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self._webhook: Optional[WebhookSender] = None
        self._email: Optional[EmailSender] = None

        if config.webhook_url:
            self._webhook = WebhookSender(config.webhook_url, config.webhook_secret)
        if config.email_to and config.smtp_server:
            self._email = EmailSender(config)

    @classmethod
    def from_webhook_url(cls, url: str, secret: Optional[str] = None) -> "Notifier":
        """Create a notifier from a webhook URL alone."""
        return cls(NotificationConfig.from_webhook_url(url, secret))

    def notify(self, event: NotificationEvent) -> None:
        """Send notification for the given event through all configured channels.

        Failures are logged but not re-raised — the pipeline should not
        crash because a notification failed to send.
        """
        if not self.config.is_configured:
            logger.debug("No notification channels configured, skipping")
            return

        if event.status == "success" and not self.config.notify_on_success:
            logger.debug("Skipping success notification (disabled in config)")
            return
        if event.status == "failure" and not self.config.notify_on_failure:
            logger.debug("Skipping failure notification (disabled in config)")
            return

        payload = event.to_dict()

        if self._webhook:
            try:
                self._webhook.send(payload)
            except NotificationError as e:
                logger.warning("Webhook notification failed: %s", e)

        if self._email:
            try:
                subject = (
                    f"[OpenMusic] {'✅' if event.status == 'success' else '❌'} "
                    f"{event.title}"
                )
                lines = [
                    f"OpenMusic Pipeline: {event.title}",
                    f"Status: {event.status.upper()}",
                    "",
                ]
                if event.output_path:
                    lines.append(f"Output: {event.output_path}")
                if event.video_url:
                    lines.append(f"URL:    {event.video_url}")
                if event.duration_seconds is not None:
                    lines.append(f"Time:   {event.duration_seconds:.1f}s")
                if event.error_message:
                    lines.append(f"Error:  {event.error_message}")
                body = "\n".join(lines)
                self._email.send(subject, body)
            except NotificationError as e:
                logger.warning("Email notification failed: %s", e)
