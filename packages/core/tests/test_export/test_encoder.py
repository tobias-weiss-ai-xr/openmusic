"""Tests for export.encoder module."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openmusic.export.encoder import (
    AudioEncoder,
    AudioInfo,
    EncoderNotFoundError,
    EncodingError,
)


def _mock_subprocess_ok(stdout="", stderr=""):
    return MagicMock(returncode=0, stdout=stdout, stderr=stderr)


class TestEncoderNotFoundError:
    """Tests for EncoderNotFoundError."""

    def test_is_exception(self):
        assert issubclass(EncoderNotFoundError, Exception)

    def test_message(self):
        err = EncoderNotFoundError("ffmpeg not found")
        assert "ffmpeg not found" in str(err)


class TestEncodingError:
    """Tests for EncodingError."""

    def test_is_exception(self):
        assert issubclass(EncodingError, Exception)

    def test_message(self):
        err = EncodingError("encoding failed")
        assert "encoding failed" in str(err)

    def test_with_stderr(self):
        err = EncodingError("encoding failed", stderr="pipe broken")
        assert "encoding failed" in str(err)
        assert "pipe broken" in str(err)


class TestAudioInfo:
    """Tests for AudioInfo dataclass."""

    def test_create_with_all_fields(self):
        info = AudioInfo(
            format="flac",
            duration=180.5,
            sample_rate=48000,
            bitrate=800000,
            channels=2,
        )
        assert info.format == "flac"
        assert info.duration == 180.5
        assert info.sample_rate == 48000
        assert info.bitrate == 800000
        assert info.channels == 2


class TestAudioEncoderInit:
    """Tests for AudioEncoder.__init__."""

    def test_init_with_default_paths(self):
        encoder = AudioEncoder()
        assert encoder.ffmpeg_path is not None
        assert encoder.ffprobe_path is not None

    def test_init_with_custom_paths(self):
        encoder = AudioEncoder(
            ffmpeg_path="/custom/ffmpeg", ffprobe_path="/custom/ffprobe"
        )
        assert encoder.ffmpeg_path == "/custom/ffmpeg"
        assert encoder.ffprobe_path == "/custom/ffprobe"


class TestAudioEncoderIsAvailable:
    """Tests for AudioEncoder.is_available."""

    @patch("openmusic.export.encoder.shutil.which")
    def test_available_when_ffmpeg_found(self, mock_which):
        mock_which.return_value = "/usr/bin/ffmpeg"
        encoder = AudioEncoder()
        assert encoder.is_available() is True

    @patch("openmusic.export.encoder.shutil.which")
    def test_unavailable_when_ffmpeg_not_found(self, mock_which):
        mock_which.return_value = None
        encoder = AudioEncoder()
        assert encoder.is_available() is False


class TestAudioEncoderEncodeFlac:
    """Tests for AudioEncoder.encode_flac."""

    def test_encode_flac_returns_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = _mock_subprocess_ok()

                encoder = AudioEncoder()
                result = encoder.encode_flac(str(input_path), str(output_path))

                assert result == Path(output_path)

    def test_encode_flac_calls_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_flac(str(input_path), str(output_path))

            assert captured_cmd is not None
            assert "ffmpeg" in captured_cmd[0] or captured_cmd[0].endswith("ffmpeg")
            assert "-i" in captured_cmd
            assert str(input_path) in captured_cmd

    def test_encode_flac_uses_flac_codec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_flac(str(input_path), str(output_path))

            cmd_str = " ".join(captured_cmd)
            assert "-c:a" in cmd_str or "flac" in cmd_str.lower()

    def test_encode_flac_uses_24bit_depth(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_flac(str(input_path), str(output_path))

            cmd_str = " ".join(captured_cmd)
            assert "-sample_fmt" in cmd_str or "s24" in cmd_str

    def test_encode_flac_uses_48khz_sample_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_flac(str(input_path), str(output_path))

            cmd_str = " ".join(captured_cmd)
            assert "-ar" in cmd_str
            assert "48000" in cmd_str

    def test_encode_flac_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"
            output_path.touch()

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_flac(str(input_path), str(output_path))

            assert "-y" in captured_cmd

    def test_encode_flac_raises_encoding_error_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stderr="Conversion failed"
                )

                encoder = AudioEncoder()
                with pytest.raises(EncodingError):
                    encoder.encode_flac(str(input_path), str(output_path))

    def test_encode_flac_includes_stderr_in_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="Invalid codec")

                encoder = AudioEncoder()
                with pytest.raises(EncodingError) as exc_info:
                    encoder.encode_flac(str(input_path), str(output_path))

                assert "Invalid codec" in str(exc_info.value)

    def test_encode_flac_raises_encoder_not_found_when_ffmpeg_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            with patch("openmusic.export.encoder.shutil.which", return_value=None):
                encoder = AudioEncoder()
                with pytest.raises(EncoderNotFoundError):
                    encoder.encode_flac(str(input_path), str(output_path))

    def test_encode_flac_with_metadata(self):
        from openmusic.export.metadata import TrackMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.flac"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                meta = TrackMetadata(title="Dub Track", artist="Artist")
                encoder.encode_flac(str(input_path), str(output_path), metadata=meta)

            cmd_str = " ".join(captured_cmd)
            assert "title" in cmd_str.lower()
            assert "Dub Track" in cmd_str


class TestAudioEncoderEncodeMp3:
    """Tests for AudioEncoder.encode_mp3."""

    def test_encode_mp3_returns_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = _mock_subprocess_ok()

                encoder = AudioEncoder()
                result = encoder.encode_mp3(str(input_path), str(output_path))

                assert result == Path(output_path)

    def test_encode_mp3_calls_ffmpeg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_mp3(str(input_path), str(output_path))

            assert captured_cmd is not None
            assert "ffmpeg" in captured_cmd[0] or captured_cmd[0].endswith("ffmpeg")

    def test_encode_mp3_default_bitrate_320(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_mp3(str(input_path), str(output_path))

            cmd_str = " ".join(captured_cmd)
            assert "320k" in cmd_str

    def test_encode_mp3_custom_bitrate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_mp3(str(input_path), str(output_path), bitrate=192)

            cmd_str = " ".join(captured_cmd)
            assert "192k" in cmd_str

    def test_encode_mp3_uses_libmp3lame_codec(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.encode_mp3(str(input_path), str(output_path))

            cmd_str = " ".join(captured_cmd)
            assert "libmp3lame" in cmd_str

    def test_encode_mp3_raises_encoding_error_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stderr="MP3 encoding failed"
                )

                encoder = AudioEncoder()
                with pytest.raises(EncodingError):
                    encoder.encode_mp3(str(input_path), str(output_path))

    def test_encode_mp3_raises_encoder_not_found_when_ffmpeg_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            with patch("openmusic.export.encoder.shutil.which", return_value=None):
                encoder = AudioEncoder()
                with pytest.raises(EncoderNotFoundError):
                    encoder.encode_mp3(str(input_path), str(output_path))

    def test_encode_mp3_with_metadata(self):
        from openmusic.export.metadata import TrackMetadata

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.wav"
            input_path.touch()
            output_path = Path(tmpdir) / "output.mp3"

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok()

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                meta = TrackMetadata(title="Dub Track", artist="Artist")
                encoder.encode_mp3(str(input_path), str(output_path), metadata=meta)

            cmd_str = " ".join(captured_cmd)
            assert "title" in cmd_str.lower()
            assert "Dub Track" in cmd_str


class TestAudioEncoderGetFormatInfo:
    """Tests for AudioEncoder.get_format_info."""

    def test_get_format_info_returns_audio_info(self):
        ffprobe_json = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "flac",
                        "sample_rate": "48000",
                        "channels": 2,
                        "bit_rate": "800000",
                        "duration": "180.5",
                    }
                ],
                "format": {
                    "format_name": "flac",
                    "duration": "180.5",
                    "bit_rate": "800000",
                },
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "audio.flac"
            file_path.touch()

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = _mock_subprocess_ok(stdout=ffprobe_json)

                encoder = AudioEncoder()
                info = encoder.get_format_info(str(file_path))

                assert isinstance(info, AudioInfo)
                assert info.format == "flac"
                assert info.duration == 180.5
                assert info.sample_rate == 48000
                assert info.channels == 2

    def test_get_format_info_calls_ffprobe(self):
        ffprobe_json = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "mp3",
                        "sample_rate": "44100",
                        "channels": 2,
                        "bit_rate": "320000",
                        "duration": "200.0",
                    }
                ],
                "format": {
                    "format_name": "mp3",
                    "duration": "200.0",
                    "bit_rate": "320000",
                },
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "audio.mp3"
            file_path.touch()

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok(stdout=ffprobe_json)

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.get_format_info(str(file_path))

            assert captured_cmd is not None
            assert "ffprobe" in captured_cmd[0] or captured_cmd[0].endswith("ffprobe")
            assert "-show_format" in captured_cmd
            assert "-show_streams" in captured_cmd
            assert str(file_path) in captured_cmd

    def test_get_format_info_uses_json_output(self):
        ffprobe_json = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "wav",
                        "sample_rate": "48000",
                        "channels": 2,
                    }
                ],
                "format": {"format_name": "wav", "duration": "60.0"},
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "audio.wav"
            file_path.touch()

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok(stdout=ffprobe_json)

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.get_format_info(str(file_path))

            assert "-print_format" in captured_cmd
            assert "json" in captured_cmd

    def test_get_format_info_raises_on_ffprobe_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "audio.flac"
            file_path.touch()

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1, stderr="No such file")

                encoder = AudioEncoder()
                with pytest.raises(EncodingError):
                    encoder.get_format_info(str(file_path))

    def test_get_format_info_raises_on_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "audio.flac"
            file_path.touch()

            with patch("openmusic.export.encoder.subprocess.run") as mock_run:
                mock_run.return_value = _mock_subprocess_ok(stdout="not json")

                encoder = AudioEncoder()
                with pytest.raises(EncodingError):
                    encoder.get_format_info(str(file_path))


class TestAudioEncoderProbeCodecs:
    """Tests for AudioEncoder.probe_codecs."""

    def test_probe_codecs_returns_list(self):
        ffprobe_json = json.dumps(
            {
                "streams": [
                    {
                        "codec_type": "audio",
                        "codec_name": "flac",
                    }
                ]
            }
        )

        with patch("openmusic.export.encoder.subprocess.run") as mock_run:
            mock_run.return_value = _mock_subprocess_ok(stdout=ffprobe_json)

            encoder = AudioEncoder()
            codecs = encoder.probe_codecs()

            assert isinstance(codecs, list)

    def test_probe_codecs_calls_ffprobe_with_codecs_flag(self):
        with patch("openmusic.export.encoder.subprocess.run") as mock_run:
            mock_run.return_value = _mock_subprocess_ok(
                stdout=json.dumps({"streams": []})
            )

            captured_cmd = None

            def capture_run(cmd, **kw):
                nonlocal captured_cmd
                captured_cmd = cmd
                return _mock_subprocess_ok(stdout=json.dumps({"streams": []}))

            with patch(
                "openmusic.export.encoder.subprocess.run", side_effect=capture_run
            ):
                encoder = AudioEncoder()
                encoder.probe_codecs()

            assert captured_cmd is not None
            assert "ffprobe" in captured_cmd[0] or captured_cmd[0].endswith("ffprobe")
            assert "-codecs" in captured_cmd

    def test_probe_codecs_filters_to_relevant_codecs(self):
        ffprobe_json = json.dumps(
            {
                "streams": [
                    {"codec_type": "audio", "codec_name": "flac"},
                    {"codec_type": "video", "codec_name": "h264"},
                    {"codec_type": "audio", "codec_name": "mp3"},
                    {"codec_type": "audio", "codec_name": "aac"},
                    {"codec_type": "video", "codec_name": "vp9"},
                ]
            }
        )

        with patch("openmusic.export.encoder.subprocess.run") as mock_run:
            mock_run.return_value = _mock_subprocess_ok(stdout=ffprobe_json)

            encoder = AudioEncoder()
            codecs = encoder.probe_codecs()

            assert "flac" in codecs
            assert "mp3" in codecs
            # Should only include audio codecs we care about
            for c in codecs:
                assert c in ("flac", "mp3", "wav", "aac")
