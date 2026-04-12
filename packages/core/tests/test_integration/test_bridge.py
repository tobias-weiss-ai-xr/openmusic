"""Bridge integration tests.

Exercise real bridge file I/O (temp dirs, config JSON, stem copying,
cleanup).  Node.js subprocess is mocked unless the effects engine is
built and available.
"""

import json
import os
import shutil
import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from openmusic.bridge.typescript_bridge import BridgeError, TypeScriptBridge


def _make_minimal_wav(
    path: Path,
    duration_ms: int = 100,
    sample_rate: int = 48000,
    channels: int = 1,
) -> Path:
    """Create a minimal valid WAV file (silent PCM-16) at *path*."""
    num_samples = int(sample_rate * duration_ms / 1000)
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = num_samples * block_align
    file_size = 36 + data_size

    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", file_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))  # PCM format code
        f.write(struct.pack("<H", channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        f.write(b"\x00" * data_size)
    return path


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    return _make_minimal_wav(tmp_path / "stem.wav", duration_ms=50)


@pytest.fixture
def bridge_config_dict() -> dict:
    return {
        "sampleRate": 48000,
        "channels": 2,
        "duration": 60,
        "bpm": 125,
        "key": "Dm",
        "effects": {
            "filter": {"type": "lowpass", "frequency": 800, "Q": 2.0},
            "delay": {"delayTime": 0.375, "feedback": 0.35, "wetLevel": 0.4},
            "reverb": {"duration": 3.0, "decay": 2.5, "wetLevel": 0.3},
        },
        "pattern": {"style": "dub_techno", "variation": 0.3},
    }


class TestBridgeCallWithConfigJSON:
    """Bridge writes config JSON and calls Node.js subprocess."""

    def test_bridge_writes_config_json_to_temp_dir(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        captured_config = {}

        def intercept(cmd, **kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured_config.update(json.load(f))
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            result = bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert result == output_path
        assert captured_config["bpm"] == 125
        assert captured_config["key"] == "Dm"
        assert captured_config["sampleRate"] == 48000

    def test_bridge_copies_input_stems_to_temp_dir(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        stem_files_found = []

        def intercept(cmd, **kw):
            cwd = kw.get("cwd", "")
            input_dir = os.path.join(cwd, "input")
            if os.path.exists(input_dir):
                stem_files_found.extend(os.listdir(input_dir))
            # Create output file in temp dir
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert len(stem_files_found) == 1
        assert stem_files_found[0].startswith("stem_")
        assert stem_files_found[0].endswith(".wav")

    def test_bridge_config_has_input_stems_array(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        captured_config = {}

        def intercept(cmd, **kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured_config.update(json.load(f))
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert "inputStems" in captured_config
        stems = captured_config["inputStems"]
        assert isinstance(stems, list)
        assert len(stems) == 1
        assert stems[0]["role"] == "stem"
        assert "path" in stems[0]

    def test_bridge_config_merges_user_config(self, sample_wav: Path) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")
        custom_config = {
            "sampleRate": 44100,
            "bpm": 130,
            "key": "Am",
            "duration": 120,
        }

        captured_config = {}

        def intercept(cmd, **kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured_config.update(json.load(f))
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=custom_config,
            )

        assert captured_config["sampleRate"] == 44100
        assert captured_config["bpm"] == 130
        assert captured_config["key"] == "Am"
        assert captured_config["duration"] == 120

    def test_bridge_multiple_stems(
        self, tmp_path: Path, bridge_config_dict: dict
    ) -> None:
        stem1 = _make_minimal_wav(tmp_path / "stem1.wav", duration_ms=50)
        stem2 = _make_minimal_wav(tmp_path / "stem2.wav", duration_ms=50)
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(tmp_path / "output.wav")

        captured_config = {}

        def intercept(cmd, **kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured_config.update(json.load(f))
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            result = bridge.call_audio_engine(
                input_files=[str(stem1), str(stem2)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert result == output_path
        assert len(captured_config["inputStems"]) == 2


class TestBridgeConfigValidation:
    """Bridge error handling for invalid configurations."""

    def test_bridge_raises_on_nonzero_exit(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        with patch("openmusic.bridge.typescript_bridge.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Error: invalid config"
            )
            with pytest.raises(BridgeError, match="Effects processing failed"):
                bridge.call_audio_engine(
                    input_files=[str(sample_wav)],
                    output_path=output_path,
                    config=bridge_config_dict,
                )

    def test_bridge_includes_stderr_in_error(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        with patch("openmusic.bridge.typescript_bridge.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2, stderr="TypeError: expected number, got string"
            )
            with pytest.raises(BridgeError) as exc_info:
                bridge.call_audio_engine(
                    input_files=[str(sample_wav)],
                    output_path=output_path,
                    config=bridge_config_dict,
                )

            assert "TypeError: expected number" in str(exc_info.value)

    def test_bridge_raises_on_missing_input_file(
        self, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = "/tmp/output.wav"

        with pytest.raises((FileNotFoundError, OSError)):
            bridge.call_audio_engine(
                input_files=["/nonexistent/path/stem.wav"],
                output_path=output_path,
                config=bridge_config_dict,
            )

    def test_bridge_handles_empty_input_list(
        self, tmp_path: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(tmp_path / "output.wav")

        captured_config = {}

        def intercept(cmd, **kw):
            idx = cmd.index("--config") + 1
            with open(cmd[idx]) as f:
                captured_config.update(json.load(f))
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            result = bridge.call_audio_engine(
                input_files=[],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert result == output_path
        assert captured_config["inputStems"] == []


class TestBridgeTempDirectoryCleanup:
    """Temp directories are cleaned up after bridge calls."""

    def test_temp_dir_removed_after_success(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        captured_tmpdir = None

        def intercept(cmd, **kw):
            nonlocal captured_tmpdir
            captured_tmpdir = kw.get("cwd")
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert captured_tmpdir is not None
        assert not os.path.exists(captured_tmpdir)

    def test_temp_dir_removed_after_failure(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        captured_tmpdir = None

        def intercept(cmd, **kw):
            nonlocal captured_tmpdir
            captured_tmpdir = kw.get("cwd")
            return MagicMock(returncode=1, stderr="Error")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            with pytest.raises(BridgeError):
                bridge.call_audio_engine(
                    input_files=[str(sample_wav)],
                    output_path=output_path,
                    config=bridge_config_dict,
                )

        assert captured_tmpdir is not None
        assert not os.path.exists(captured_tmpdir)

    def test_temp_dir_has_openmusic_prefix(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        captured_tmpdir = None

        def intercept(cmd, **kw):
            nonlocal captured_tmpdir
            captured_tmpdir = kw.get("cwd")
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert captured_tmpdir is not None
        assert "openmusic-" in os.path.basename(captured_tmpdir)

        captured_tmpdir = None

        def intercept(cmd, **kw):
            nonlocal captured_tmpdir
            captured_tmpdir = kw.get("cwd")
            # Create output file in temp dir
            cwd = kw.get("cwd")
            if cwd:
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert "openmusic-" in os.path.basename(captured_tmpdir or "")

    def test_temp_dir_has_input_and_output_subdirs(
        self, sample_wav: Path, bridge_config_dict: dict
    ) -> None:
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        output_path = str(sample_wav.parent / "output.wav")

        created_dirs = []

        def intercept(cmd, **kw):
            cwd = kw.get("cwd")
            if cwd:
                # Create output file in temp dir
                output_dir = os.path.join(cwd, "output")
                os.makedirs(output_dir, exist_ok=True)
                output_file = os.path.join(output_dir, "processed.wav")
                Path(output_file).touch()
                # Track created dirs
                for entry in ["input", "output"]:
                    full = os.path.join(cwd, entry)
                    if os.path.exists(full):
                        created_dirs.append(entry)
            return MagicMock(returncode=0, stderr="")

        with patch(
            "openmusic.bridge.typescript_bridge.subprocess.run", side_effect=intercept
        ):
            bridge.call_audio_engine(
                input_files=[str(sample_wav)],
                output_path=output_path,
                config=bridge_config_dict,
            )

        assert "input" in created_dirs
        assert "output" in created_dirs

    def test_cleanup_explicit_call_removes_nested_files(self) -> None:
        tmpdir = tempfile.mkdtemp(prefix="openmusic-test-")
        nested = os.path.join(tmpdir, "input")
        os.makedirs(nested)
        Path(os.path.join(nested, "stem.wav")).touch()

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        bridge.cleanup(tmpdir)

        assert not os.path.exists(tmpdir)


class TestBridgeIsAvailable:
    """TypeScriptBridge.is_available checks Node.js and effects bin."""

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_available_when_both_exist(self, mock_exists, mock_which) -> None:
        mock_which.return_value = "/usr/bin/node"
        mock_exists.return_value = True
        bridge = TypeScriptBridge(effects_bin="/fake/dist/index.js")
        assert bridge.is_available() is True

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_unavailable_without_node(self, mock_exists, mock_which) -> None:
        mock_which.return_value = None
        mock_exists.return_value = True
        bridge = TypeScriptBridge(effects_bin="/fake/dist/index.js")
        assert bridge.is_available() is False

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_unavailable_without_effects_bin(self, mock_exists, mock_which) -> None:
        mock_which.return_value = "/usr/bin/node"
        mock_exists.return_value = False
        bridge = TypeScriptBridge(effects_bin="/fake/dist/index.js")
        assert bridge.is_available() is False
