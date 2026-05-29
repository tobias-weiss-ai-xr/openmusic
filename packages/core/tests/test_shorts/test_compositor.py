"""Tests for compositor module."""
from unittest.mock import patch, MagicMock

import pytest

from openmusic.shorts.compositor import (
    extract_audio_segment,
    merge_audio_video,
    convert_to_shorts,
    CompositorError,
)


class TestCompositor:
    def test_extract_audio_segment_calls_ffmpeg(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = extract_audio_segment("/input.flac", 30.0, 32.0, "/tmp/out.wav")
            assert result == "/tmp/out.wav"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ffmpeg" in args[0]
            assert "-ss" in args
            assert "30.0" in args
            assert "-t" in args
            assert "32.0" in args

    def test_merge_audio_video_calls_ffmpeg(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = merge_audio_video("/video.webm", "/audio.wav", "/output.mp4")
            assert result == "/output.mp4"
            args = mock_run.call_args[0][0]
            assert "ffmpeg" in args[0]
            assert "-i" in args
            assert "/video.webm" in args or "/audio.wav" in args

    def test_convert_to_shorts_calls_ffmpeg(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = convert_to_shorts("/input.mp4", "/output_shorts.mp4")
            assert result == "/output_shorts.mp4"
            args = mock_run.call_args[0][0]
            assert "ffmpeg" in args[0]
            cmd_str = " ".join(args)
            assert "scale" in cmd_str
            assert "pad" in cmd_str

    def test_compositor_error(self):
        err = CompositorError("test error")
        assert str(err) == "test error"
        assert isinstance(err, Exception)
