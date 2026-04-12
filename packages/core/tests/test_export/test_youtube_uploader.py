"""Tests for export.youtube_uploader module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from openmusic.export.youtube_uploader import (
    OAuthNotConfiguredError,
    QuotaExceededError,
    YouTubeAPIUploader,
    YouTubeUploadConfig,
    YouTubeUploadError,
    YouTubeUploader,
    YouTubeUpFallback,
    YouTubeUpNotInstalledError,
)


class TestYouTubeUploadConfig:
    """Tests for YouTubeUploadConfig dataclass."""

    def test_create_with_defaults(self):
        config = YouTubeUploadConfig()
        assert config.title == "Dub Techno Mix"
        assert config.description == ""
        assert config.tags == ["dub techno", "electronic music"]
        assert config.category == "10"
        assert config.privacy == "private"
        assert config.made_for_kids is False
        assert config.publish_at is None
        assert config.thumbnail_path is None
        assert config.playlist_title is None
        assert config.client_secrets_file == "client_secrets.json"
        assert config.token_file == "youtube_token.json"

    def test_create_with_custom_values(self):
        config = YouTubeUploadConfig(
            title="Custom Title",
            description="Custom description",
            tags=["tag1", "tag2"],
            category="22",
            privacy="public",
            made_for_kids=True,
            publish_at="2025-12-31T23:59:59Z",
            thumbnail_path="thumb.png",
            playlist_title="My Playlist",
            client_secrets_file="custom_secrets.json",
        )
        assert config.title == "Custom Title"
        assert config.description == "Custom description"
        assert config.tags == ["tag1", "tag2"]
        assert config.category == "22"
        assert config.privacy == "public"
        assert config.made_for_kids is True
        assert config.publish_at == "2025-12-31T23:59:59Z"
        assert config.thumbnail_path == "thumb.png"
        assert config.playlist_title == "My Playlist"
        assert config.client_secrets_file == "custom_secrets.json"


class TestYouTubeUploadError:
    """Tests for YouTubeUploadError exceptions."""

    def test_base_exception(self):
        assert issubclass(YouTubeUploadError, Exception)

    def test_quota_exceeded_is_upload_error(self):
        assert issubclass(QuotaExceededError, YouTubeUploadError)

    def test_oauth_not_configured_is_upload_error(self):
        assert issubclass(OAuthNotConfiguredError, YouTubeUploadError)

    def test_youtube_up_not_installed_is_upload_error(self):
        assert issubclass(YouTubeUpNotInstalledError, YouTubeUploadError)


class TestYouTubeAPIUploader:
    """Tests for YouTubeAPIUploader."""

    def test_init_with_config(self):
        config = YouTubeUploadConfig(title="Test Video")
        uploader = YouTubeAPIUploader(config)
        assert uploader.config == config
        assert uploader.youtube is None
        assert uploader.credentials is None

    def test_authenticate_raises_when_secrets_missing(self):
        config = YouTubeUploadConfig(client_secrets_file="nonexistent.json")
        uploader = YouTubeAPIUploader(config)

        with pytest.raises(OAuthNotConfiguredError) as exc_info:
            uploader.authenticate()

        assert "OAuth client secrets file not found" in str(exc_info.value)

    def test_is_quota_exceeded_detects_quota_error(self):
        config = YouTubeUploadConfig()
        uploader = YouTubeAPIUploader(config)

        # Create mock HttpError with quota exceeded
        mock_error = MagicMock()
        mock_error.resp.status = 403
        mock_error.content = b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}'
        mock_error.error_details = [{"reason": "quotaExceeded"}]

        assert uploader._is_quota_exceeded(mock_error) is True

    def test_is_quota_exceeded_returns_false_for_other_errors(self):
        config = YouTubeUploadConfig()
        uploader = YouTubeAPIUploader(config)

        # Create mock HttpError without quota exceeded
        mock_error = MagicMock()
        mock_error.resp.status = 403
        mock_error.content = b'{"error": {"errors": [{"reason": "forbidden"}]}}'

        assert uploader._is_quota_exceeded(mock_error) is False

    def test_upload_raises_when_video_not_found(self):
        config = YouTubeUploadConfig()
        uploader = YouTubeAPIUploader(config)

        # Mock youtube service
        uploader.youtube = MagicMock()

        with pytest.raises(YouTubeUploadError) as exc_info:
            uploader.upload("nonexistent.mp4")

        assert "Video file not found" in str(exc_info.value)

    def test_set_thumbnail_raises_when_thumbnail_not_found(self):
        config = YouTubeUploadConfig()
        uploader = YouTubeAPIUploader(config)

        uploader.youtube = MagicMock()

        with pytest.raises(YouTubeUploadError) as exc_info:
            uploader.set_thumbnail("video_id", "nonexistent.png")

        assert "Thumbnail file not found" in str(exc_info.value)

    def test_add_to_playlist_raises_when_no_youtube_service(self):
        config = YouTubeUploadConfig()
        uploader = YouTubeAPIUploader(config)

        with pytest.raises(YouTubeUploadError) as exc_info:
            uploader.add_to_playlist("video_id", "Test Playlist")

        # Should try to authenticate first
        assert (
            "OAuth" in str(exc_info.value).lower()
            or "credentials" in str(exc_info.value).lower()
        )


class TestYouTubeUpFallback:
    """Tests for YouTubeUpFallback."""

    def test_init_with_config(self):
        config = YouTubeUploadConfig()
        fallback = YouTubeUpFallback(config)
        assert fallback.config == config

    def test_is_available_returns_false_when_not_installed(self):
        config = YouTubeUploadConfig()
        fallback = YouTubeUpFallback(config)

        # Mock youtube_up to not be installed
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "youtube_up":
                raise ImportError("No module named 'youtube_up'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            assert fallback.is_available() is False

    def test_upload_raises_without_youtube_up_installed(self):
        """Test that upload fails when youtube-up is not installed."""
        config = YouTubeUploadConfig()
        fallback = YouTubeUpFallback(config)

        # Create a temp directory with cookies file to pass file check
        with tempfile.TemporaryDirectory() as tmpdir:
            cookies_path = Path(tmpdir) / "cookies.txt"
            cookies_path.touch()
            fallback.config.cookies_file = str(cookies_path)

            # This should fail because youtube_up is not installed
            with pytest.raises(YouTubeUpNotInstalledError) as exc_info:
                fallback.upload("nonexistent.mp4")

            assert "youtube-up package not installed" in str(exc_info.value)


class TestYouTubeUploader:
    """Tests for YouTubeUploader (dual-backend orchestrator)."""

    def test_init_with_default_config(self):
        uploader = YouTubeUploader()
        assert uploader.config.title == "Dub Techno Mix"
        assert isinstance(uploader.api_uploader, YouTubeAPIUploader)
        assert isinstance(uploader.fallback_uploader, YouTubeUpFallback)

    def test_init_with_custom_config(self):
        config = YouTubeUploadConfig(title="Custom")
        uploader = YouTubeUploader(config)
        assert uploader.config.title == "Custom"

    @patch.object(YouTubeAPIUploader, "upload")
    def test_upload_uses_api_uploader_first(self, mock_api_upload):
        config = YouTubeUploadConfig()
        uploader = YouTubeUploader(config)

        mock_api_upload.return_value = "video123"

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            video_id = uploader.upload(str(video_path))

            assert video_id == "video123"
            mock_api_upload.assert_called_once()

    @patch.object(YouTubeUpFallback, "upload")
    @patch.object(YouTubeAPIUploader, "upload")
    def test_upload_falls_back_on_quota_error(
        self, mock_api_upload, mock_fallback_upload
    ):
        config = YouTubeUploadConfig()
        uploader = YouTubeUploader(config)

        # API uploader raises quota exceeded
        mock_api_upload.side_effect = QuotaExceededError("Quota exceeded")
        mock_fallback_upload.return_value = "video456"

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            video_id = uploader.upload(str(video_path))

            assert video_id == "video456"
            mock_api_upload.assert_called_once()
            mock_fallback_upload.assert_called_once()

    @patch.object(YouTubeUpFallback, "upload")
    @patch.object(YouTubeAPIUploader, "upload")
    def test_upload_falls_back_on_upload_error(
        self, mock_api_upload, mock_fallback_upload
    ):
        config = YouTubeUploadConfig()
        uploader = YouTubeUploader(config)

        # API uploader raises generic upload error
        mock_api_upload.side_effect = YouTubeUploadError("Upload failed")
        mock_fallback_upload.return_value = "video789"

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()

            video_id = uploader.upload(str(video_path))

            assert video_id == "video789"
            mock_api_upload.assert_called_once()
            mock_fallback_upload.assert_called_once()

    @patch.object(YouTubeUpFallback, "upload")
    @patch.object(YouTubeAPIUploader, "upload")
    @patch.object(YouTubeAPIUploader, "set_thumbnail")
    @patch.object(YouTubeAPIUploader, "add_to_playlist")
    def test_upload_sets_thumbnail_and_playlist_on_success(
        self,
        mock_add_playlist,
        mock_set_thumb,
        mock_api_upload,
        mock_fallback_upload,
    ):
        config = YouTubeUploadConfig(
            thumbnail_path="thumb.png",
            playlist_title="My Playlist",
        )
        uploader = YouTubeUploader(config)

        mock_api_upload.return_value = "video123"

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            thumb_path = Path(tmpdir) / "thumb.png"
            video_path.touch()
            thumb_path.touch()

            uploader.config.thumbnail_path = str(thumb_path)

            video_id = uploader.upload(str(video_path))

            assert video_id == "video123"
            mock_api_upload.assert_called_once()
            mock_set_thumb.assert_called_once_with("video123", str(thumb_path))
            mock_add_playlist.assert_called_once_with("video123", "My Playlist")
            mock_fallback_upload.assert_not_called()


class TestCLICommand:
    """Tests for CLI upload command."""

    def test_upload_command_exists(self):
        """Test that upload command is registered in CLI."""
        from openmusic.cli.main import main

        # Check that upload command exists in the main group
        commands = main.list_commands(None)
        assert "upload" in commands

    @patch("openmusic.cli.main.YouTubeUploader")
    def test_upload_command_calls_uploader(self, mock_uploader_class):
        from click.testing import CliRunner
        from openmusic.cli.main import main

        mock_uploader = MagicMock()
        mock_uploader.upload.return_value = "test_video_id"
        mock_uploader_class.return_value = mock_uploader

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            secrets_path = Path(tmpdir) / "client_secrets.json"
            cookies_path = Path(tmpdir) / "cookies.txt"
            video_path.touch()
            secrets_path.touch()
            cookies_path.touch()

            result = runner.invoke(
                main,
                [
                    "upload",
                    "--video",
                    str(video_path),
                    "--client-secrets",
                    str(secrets_path),
                    "--cookies",
                    str(cookies_path),
                    "--title",
                    "Test Video",
                    "--privacy",
                    "private",
                ],
            )

            assert result.exit_code == 0
            mock_uploader.upload.assert_called_once()

    @patch("openmusic.cli.main.YouTubeUploader")
    def test_upload_command_handles_upload_error(self, mock_uploader_class):
        from click.testing import CliRunner
        from openmusic.cli.main import main

        mock_uploader = MagicMock()
        mock_uploader.upload.side_effect = YouTubeUploadError("Upload failed")
        mock_uploader_class.return_value = mock_uploader

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            secrets_path = Path(tmpdir) / "client_secrets.json"
            cookies_path = Path(tmpdir) / "cookies.txt"
            video_path.touch()
            secrets_path.touch()
            cookies_path.touch()

            result = runner.invoke(
                main,
                [
                    "upload",
                    "--video",
                    str(video_path),
                    "--client-secrets",
                    str(secrets_path),
                    "--cookies",
                    str(cookies_path),
                ],
            )

            assert result.exit_code != 0
            assert "Upload failed" in result.output
