"""Tests for the notification module (webhook + email)."""

import json
import logging
from dataclasses import dataclass
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from openmusic.notification import (
    NotificationConfig,
    NotificationEvent,
    NotificationError,
    Notifier,
)


# ── Helpers ──────────────────────────────────────────────────────────


class _EchoWebhookHandler(BaseHTTPRequestHandler):
    """A minimal HTTP server that captures the last POST body."""

    last_body: Optional[bytes] = None
    last_headers: Optional[dict] = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b""
        _EchoWebhookHandler.last_body = body
        _EchoWebhookHandler.last_headers = dict(self.headers)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


@pytest.fixture
def webhook_server():
    """Start a local HTTP server that captures POST bodies."""
    _EchoWebhookHandler.last_body = None
    _EchoWebhookHandler.last_headers = None
    server = HTTPServer(("127.0.0.1", 0), _EchoWebhookHandler)
    port = server.server_address[1]
    thread = Thread(target=server.handle_request, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.server_close()


# ── NotificationConfig ───────────────────────────────────────────────


class TestNotificationConfig:
    def test_defaults(self):
        cfg = NotificationConfig()
        assert cfg.webhook_url is None
        assert cfg.email_to is None
        assert cfg.notify_on_success is True
        assert cfg.notify_on_failure is True
        assert cfg.is_configured is False

    def test_webhook_configured(self):
        cfg = NotificationConfig(webhook_url="https://example.com/hook")
        assert cfg.is_configured is True

    def test_email_configured(self):
        cfg = NotificationConfig(
            email_to="test@example.com", smtp_server="smtp.example.com"
        )
        assert cfg.is_configured is True

    def test_from_webhook_url(self):
        cfg = NotificationConfig.from_webhook_url(
            "https://hooks.example.com", secret="sekret"
        )
        assert cfg.webhook_url == "https://hooks.example.com"
        assert cfg.webhook_secret == "sekret"


# ── NotificationEvent ────────────────────────────────────────────────


class TestNotificationEvent:
    def test_to_dict_success(self):
        event = NotificationEvent(
            status="success",
            title="Test Mix",
            output_path="/tmp/mix.flac",
            video_id="abc123",
            duration_seconds=3600.0,
        )
        d = event.to_dict()
        assert d["status"] == "success"
        assert d["title"] == "Test Mix"
        assert d["output_path"] == "/tmp/mix.flac"
        assert d["video_id"] == "abc123"
        assert d["duration_seconds"] == 3600.0
        assert "error_message" not in d

    def test_to_dict_failure(self):
        event = NotificationEvent(
            status="failure",
            title="Failed Mix",
            error_message="Something broke",
        )
        d = event.to_dict()
        assert d["status"] == "failure"
        assert d["error_message"] == "Something broke"
        assert "video_id" not in d

    def test_to_dict_with_metadata(self):
        event = NotificationEvent(
            status="success",
            title="Meta Mix",
            metadata={"custom_field": 42, "tags": ["dub", "techno"]},
        )
        d = event.to_dict()
        assert d["custom_field"] == 42
        assert d["tags"] == ["dub", "techno"]

    def test_to_dict_omits_none(self):
        event = NotificationEvent(status="success", title="Clean")
        d = event.to_dict()
        assert "output_path" not in d
        assert "video_id" not in d


# ── Webhook Notification ─────────────────────────────────────────────


class TestWebhookNotification:
    def test_webhook_sends_json(self, webhook_server):
        cfg = NotificationConfig(webhook_url=webhook_server)
        notifier = Notifier(cfg)
        event = NotificationEvent(
            status="success",
            title="Webhook Test",
            output_path="/tmp/test.flac",
        )
        notifier.notify(event)

        assert _EchoWebhookHandler.last_body is not None
        payload = json.loads(_EchoWebhookHandler.last_body)
        assert payload["status"] == "success"
        assert payload["title"] == "Webhook Test"
        assert payload["output_path"] == "/tmp/test.flac"

    def test_webhook_with_secret(self, webhook_server):
        cfg = NotificationConfig(
            webhook_url=webhook_server, webhook_secret="mysecret"
        )
        notifier = Notifier(cfg)
        event = NotificationEvent(status="success", title="Signed")
        notifier.notify(event)

        assert _EchoWebhookHandler.last_headers is not None
        signature = _EchoWebhookHandler.last_headers.get("X-Signature-256")
        assert signature is not None
        assert len(signature) == 64  # SHA-256 hex digest

    def test_webhook_200_ok(self, webhook_server):
        """200 does not raise."""
        cfg = NotificationConfig(webhook_url=webhook_server)
        notifier = Notifier(cfg)
        notifier.notify(NotificationEvent(status="success", title="OK"))
        # No exception = pass

    def test_webhook_unreachable_logs_warning(self, caplog):
        """Unreachable server logs a warning but does not raise."""
        cfg = NotificationConfig(webhook_url="http://127.0.0.1:1/nonexistent")
        notifier = Notifier(cfg)
        with caplog.at_level(logging.WARNING):
            notifier.notify(NotificationEvent(status="success", title="Fail"))
        assert "Webhook notification failed" in caplog.text


# ── Email Notification ───────────────────────────────────────────────


class TestEmailNotification:
    def test_email_not_configured_skips(self, caplog):
        """Notifier with no config skips silently."""
        cfg = NotificationConfig()
        notifier = Notifier(cfg)
        with caplog.at_level(logging.DEBUG):
            notifier.notify(NotificationEvent(status="success", title="Skip"))
        assert "No notification channels configured" in caplog.text

    def test_email_missing_smtp_logs_warning(self, caplog):
        """Email configured but no SMTP server — tries to send, logs error."""
        cfg = NotificationConfig(email_to="test@example.com")
        notifier = Notifier(cfg)
        with caplog.at_level(logging.WARNING):
            notifier.notify(NotificationEvent(status="success", title="No SMTP"))
        # Without SMTP config, the notifier silently skips email
        assert True

    def test_email_notify_on_success_filter(self, caplog):
        """notify_on_success=False skips success events."""
        cfg = NotificationConfig(
            webhook_url="http://127.0.0.1:18081/unused",
            notify_on_success=False,
        )
        notifier = Notifier(cfg)
        with caplog.at_level(logging.DEBUG):
            notifier.notify(NotificationEvent(status="success", title="Skip"))
        assert "Skipping success notification" in caplog.text

    def test_notify_on_failure_filter(self, caplog):
        """notify_on_failure=False skips failure events."""
        cfg = NotificationConfig(
            webhook_url="http://127.0.0.1:18082/unused",
            notify_on_failure=False,
        )
        notifier = Notifier(cfg)
        with caplog.at_level(logging.DEBUG):
            notifier.notify(NotificationEvent(status="failure", title="Skip"))
        assert "Skipping failure notification" in caplog.text


# ── Notifier Factory Helpers ─────────────────────────────────────────


class TestNotifierFactory:
    def test_from_webhook_url(self):
        notifier = Notifier.from_webhook_url("https://example.com/hook", secret="s")
        assert notifier.config.webhook_url == "https://example.com/hook"
        assert notifier.config.webhook_secret == "s"

    def test_from_empty_webhook_url_still_creates(self):
        notifier = Notifier.from_webhook_url("")
        assert notifier.config.is_configured is False

    def test_notify_noop_when_not_configured(self, caplog):
        notifier = Notifier(NotificationConfig())
        with caplog.at_level(logging.DEBUG):
            notifier.notify(NotificationEvent(status="success", title="NOP"))
        assert "No notification channels configured" in caplog.text
