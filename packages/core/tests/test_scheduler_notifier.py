"""Tests for webhook notification support."""
from unittest.mock import patch, MagicMock

import pytest

from openmusic.scheduler.notifier import (
    NotifierConfig,
    NotificationEvent,
    notify,
)


class TestNotifierConfig:
    def test_is_configured_telegram(self):
        config = NotifierConfig(telegram_token="token", telegram_chat_id="chat")
        assert config.is_configured is True

    def test_is_configured_discord(self):
        config = NotifierConfig(discord_webhook_url="https://discord.com/webhook")
        assert config.is_configured is True

    def test_is_configured_none(self):
        config = NotifierConfig()
        assert config.is_configured is False

    def test_is_configured_partial_telegram(self):
        config = NotifierConfig(telegram_token="token")
        assert config.is_configured is False


class TestNotify:
    def test_no_channels_configured(self):
        config = NotifierConfig()
        result = notify(config, NotificationEvent.ON_SUCCESS, "test", "echo hi")
        assert result is False

    def test_event_not_in_notify_on(self):
        config = NotifierConfig(
            telegram_token="tok", telegram_chat_id="chat",
            notify_on={NotificationEvent.ON_FAILURE},
        )
        result = notify(config, NotificationEvent.ON_SUCCESS, "test", "echo hi")
        assert result is False

    @patch("requests.post")
    def test_telegram_success(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"ok": True})
        config = NotifierConfig(telegram_token="tok", telegram_chat_id="chat")
        result = notify(config, NotificationEvent.ON_SUCCESS, "test-job", "openmusic generate")
        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert "sendMessage" in mock_post.call_args[0][0]
        assert call_kwargs["json"]["chat_id"] == "chat"

    @patch("requests.post")
    def test_telegram_failure(self, mock_post):
        mock_post.return_value = MagicMock(ok=False, raise_for_status=MagicMock(side_effect=Exception("fail")))
        config = NotifierConfig(telegram_token="tok", telegram_chat_id="chat")
        result = notify(config, NotificationEvent.ON_FAILURE, "test-job", "openmusic generate", error="something broke")
        assert result is False

    @patch("requests.post")
    def test_discord_success(self, mock_post):
        mock_post.return_value = MagicMock(ok=True)
        config = NotifierConfig(discord_webhook_url="https://discord.com/webhook/abc")
        result = notify(config, NotificationEvent.ON_SUCCESS, "test-job", "openmusic generate")
        assert result is True

    @patch("requests.post")
    def test_telegram_and_discord_both(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"ok": True})
        config = NotifierConfig(
            telegram_token="tok", telegram_chat_id="chat",
            discord_webhook_url="https://discord.com/webhook/abc",
        )
        result = notify(config, NotificationEvent.ON_SUCCESS, "test", "echo hi")
        assert result is True
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_success_message_format(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"ok": True})
        config = NotifierConfig(telegram_token="tok", telegram_chat_id="chat")
        notify(config, NotificationEvent.ON_SUCCESS, "my-mix", "openmusic generate --length 2h", output="mix.flac")
        call_json = mock_post.call_args[1]["json"]
        assert "my-mix" in call_json["text"]
        assert "Completed" in call_json["text"]

    @patch("requests.post")
    def test_failure_message_format(self, mock_post):
        mock_post.return_value = MagicMock(ok=True, json=lambda: {"ok": True})
        config = NotifierConfig(telegram_token="tok", telegram_chat_id="chat")
        notify(config, NotificationEvent.ON_FAILURE, "my-mix", "openmusic generate", error="out of memory")
        call_json = mock_post.call_args[1]["json"]
        assert "Failed" in call_json["text"]
        assert "out of memory" in call_json["text"]

    def test_notify_attempts_send(self):
        config = NotifierConfig(telegram_token="tok", telegram_chat_id="chat")
        result = notify(config, NotificationEvent.ON_SUCCESS, "test", "echo hi")
        assert result is not None
