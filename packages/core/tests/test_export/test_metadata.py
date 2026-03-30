"""Tests for export.metadata module."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openmusic.export.metadata import TrackMetadata, embed_metadata


class TestTrackMetadata:
    """Tests for TrackMetadata dataclass."""

    def test_create_with_all_fields(self):
        meta = TrackMetadata(
            title="Deep Dub",
            artist="Test Artist",
            album="Dub Sessions",
            genre="Dub Techno",
            year=2025,
            bpm=125,
            key="Am",
        )
        assert meta.title == "Deep Dub"
        assert meta.artist == "Test Artist"
        assert meta.album == "Dub Sessions"
        assert meta.genre == "Dub Techno"
        assert meta.year == 2025
        assert meta.bpm == 125
        assert meta.key == "Am"

    def test_all_fields_optional(self):
        meta = TrackMetadata()
        assert meta.title is None
        assert meta.artist is None
        assert meta.album is None
        assert meta.genre is None
        assert meta.year is None
        assert meta.bpm is None
        assert meta.key is None

    def test_partial_fields(self):
        meta = TrackMetadata(title="Track 1", bpm=128)
        assert meta.title == "Track 1"
        assert meta.bpm == 128
        assert meta.artist is None


class TestEmbedMetadata:
    """Tests for embed_metadata function."""

    def _mock_subprocess_ok(self):
        return MagicMock(returncode=0, stderr="")

    def _make_capture_run(self):
        captured = {}

        def capture_run(cmd, **kw):
            captured["cmd"] = cmd
            output_file = cmd[-1]
            Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        return capture_run, captured

    def test_embed_metadata_calls_ffmpeg_with_correct_args(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="Test Track", artist="Artist")
            capture_run, _ = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ) as mock_run:
                embed_metadata(str(input_file), meta, "flac")

                args, kwargs = mock_run.call_args
                cmd = args[0]
                assert "ffmpeg" in cmd[0] or cmd[0].endswith("ffmpeg")
                assert "-i" in cmd
                assert str(input_file) in cmd
                assert "-y" in cmd

    def test_embed_metadata_includes_title_in_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="My Track")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "metadata" in cmd_str.lower()
            assert "title" in cmd_str.lower()
            assert "My Track" in cmd_str

    def test_embed_metadata_includes_artist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.mp3"
            input_file.touch()

            meta = TrackMetadata(artist="DJ Producer")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "mp3")

            cmd_str = " ".join(captured["cmd"])
            assert "artist" in cmd_str.lower()
            assert "DJ Producer" in cmd_str

    def test_embed_metadata_includes_album(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(album="Full Album")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "album" in cmd_str.lower()
            assert "Full Album" in cmd_str

    def test_embed_metadata_includes_genre(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(genre="Dub Techno")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "genre" in cmd_str.lower()
            assert "Dub Techno" in cmd_str

    def test_embed_metadata_includes_year(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(year=2025)
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "date" in cmd_str.lower() or "year" in cmd_str.lower()
            assert "2025" in cmd_str

    def test_embed_metadata_includes_bpm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(bpm=125)
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "bpm" in cmd_str.lower()
            assert "125" in cmd_str

    def test_embed_metadata_includes_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(key="Am")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "key" in cmd_str.lower()
            assert "Am" in cmd_str

    def test_embed_metadata_skips_none_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="Only Title")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "title" in cmd_str.lower()
            assert "Only Title" in cmd_str
            assert "None" not in cmd_str

    def test_embed_metadata_uses_capture_and_discard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="Test")
            capture_run, captured = self._make_capture_run()

            with patch(
                "openmusic.export.metadata.subprocess.run", side_effect=capture_run
            ):
                embed_metadata(str(input_file), meta, "flac")

            cmd_str = " ".join(captured["cmd"])
            assert "-c" in cmd_str
            assert "copy" in cmd_str

    def test_embed_metadata_raises_on_ffmpeg_failure(self):
        from openmusic.export.metadata import EmbeddingError

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="Test")

            with patch("openmusic.export.metadata.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stderr="Error: invalid data"
                )

                with pytest.raises(EmbeddingError):
                    embed_metadata(str(input_file), meta, "flac")

    def test_embed_metadata_includes_stderr_in_error(self):
        from openmusic.export.metadata import EmbeddingError

        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "output.flac"
            input_file.touch()

            meta = TrackMetadata(title="Test")

            with patch("openmusic.export.metadata.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1, stderr="AviSynth error: bad filter"
                )

                with pytest.raises(EmbeddingError) as exc_info:
                    embed_metadata(str(input_file), meta, "flac")

                assert "AviSynth error" in str(exc_info.value)
