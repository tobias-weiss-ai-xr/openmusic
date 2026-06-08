"""Tests for cli.stream module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from openmusic.cli.main import main
from openmusic.cli.stream import StreamManager, stream


@pytest.fixture
def audio_file():
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(b"dummy")
    tmp.close()
    yield tmp.name
    Path(tmp.name).unlink(missing_ok=True)


class TestStreamCommandGroup:
    def test_stream_group_registered(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stream", "--help"])
        assert result.exit_code == 0
        assert "Live stream" in result.output or "stream" in result.output

    def test_start_requires_audio(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["start"])
        assert result.exit_code != 0
        assert "audio" in result.output.lower() or "Error" in result.output


class TestStreamStartCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["start", "--help"])
        assert result.exit_code == 0
        assert "--audio" in result.output
        assert "--platform" in result.output

    def test_nonexistent_audio_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            stream, ["start", "--audio", "/nonexistent/file.wav", "--stream-key", "test"]
        )
        assert result.exit_code != 0

    def test_unsupported_platform_errors(self):
        runner = CliRunner()
        result = runner.invoke(
            stream,
            [
                "start",
                "--audio",
                "/tmp/test.wav",
                "--platform",
                "nonexistent",
                "--stream-key",
                "test",
            ],
        )
        assert result.exit_code != 0


class TestStreamStopCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["stop", "--help"])
        assert result.exit_code == 0


class TestStreamStatusCommand:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(stream, ["status", "--help"])
        assert result.exit_code == 0


class TestStreamManager:
    """Unit tests for StreamManager with mocked subprocess."""

    def test_start_creates_process(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            assert manager.is_running

    def test_double_start_raises(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            with pytest.raises(RuntimeError, match="already running"):
                manager.start(audio_file, "youtube", "test_key")

    def test_stop_terminates_process(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            manager.stop()
            mock_proc.terminate.assert_called_once()
            assert not manager.is_running

    def test_stop_without_start_safe(self):
        manager = StreamManager()
        manager.stop()

    def test_get_status_not_running(self):
        manager = StreamManager()
        status = manager.get_status()
        assert status["running"] is False
        assert status["pid"] is None

    def test_get_status_running(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.pid = 12345
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            status = manager.get_status()
            assert status["running"] is True
            assert status["pid"] == 12345

    def test_cover_image_missing_warns(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
            patch("openmusic.cli.stream.logger") as mock_logger,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key", cover_image="/nonexistent/cover.png")
            mock_logger.warning.assert_called_once()
            assert "not found" in mock_logger.warning.call_args[0][0]

    def test_process_crash_detected(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.side_effect = [None, 1]
            mock_proc.stderr = iter([])
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            assert manager.is_running
            assert not manager.is_running

    def test_stop_kills_on_timeout(self, audio_file):
        manager = StreamManager()
        with (
            patch("openmusic.cli.stream._check_ffmpeg", return_value=True),
            patch("openmusic.cli.stream.subprocess.Popen") as mock_popen,
        ):
            mock_proc = MagicMock()
            mock_proc.poll.return_value = None
            mock_proc.stderr = iter([])
            mock_proc.wait.side_effect = [subprocess.TimeoutExpired("cmd", 10), None]
            mock_popen.return_value = mock_proc
            manager.start(audio_file, "youtube", "test_key")
            manager.stop()
            mock_proc.terminate.assert_called_once()
            mock_proc.kill.assert_called_once()
