"""Tests for TypeScriptBridge."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from openmusic.bridge.typescript_bridge import (
    BridgeError,
    TypeScriptBridge,
)


class TestBridgeError:
    """Tests for the BridgeError exception."""

    def test_bridge_error_is_exception(self):
        assert issubclass(BridgeError, Exception)

    def test_bridge_error_message(self):
        err = BridgeError("something failed")
        assert str(err) == "something failed"

    def test_bridge_error_with_stderr(self):
        err = BridgeError("Effects processing failed", stderr="node: bad config")
        assert "Effects processing failed" in str(err)
        assert "node: bad config" in str(err)


class TestTypeScriptBridgeInit:
    """Tests for TypeScriptBridge.__init__."""

    def test_init_with_explicit_effects_bin(self):
        bridge = TypeScriptBridge(effects_bin="/custom/path/to/index.js")
        assert bridge.effects_bin == "/custom/path/to/index.js"

    def test_init_with_none_effects_bin_auto_detects(self):
        bridge = TypeScriptBridge(effects_bin=None)
        assert bridge.effects_bin is not None
        assert "packages" in bridge.effects_bin
        assert "effects" in bridge.effects_bin
        assert "dist" in bridge.effects_bin
        assert "index.js" in bridge.effects_bin

    def test_init_with_default_none(self):
        bridge = TypeScriptBridge()
        assert bridge.effects_bin is not None


class TestTypeScriptBridgeIsAvailable:
    """Tests for TypeScriptBridge.is_available."""

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_available_when_node_and_bin_exist(self, mock_exists, mock_which):
        mock_which.return_value = "/usr/bin/node"
        mock_exists.return_value = True

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        assert bridge.is_available() is True

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_unavailable_when_node_missing(self, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.return_value = True

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        assert bridge.is_available() is False

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_unavailable_when_bin_missing(self, mock_exists, mock_which):
        mock_which.return_value = "/usr/bin/node"
        mock_exists.return_value = False

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        assert bridge.is_available() is False

    @patch("openmusic.bridge.typescript_bridge.shutil.which")
    @patch("openmusic.bridge.typescript_bridge.os.path.exists")
    def test_unavailable_when_both_missing(self, mock_exists, mock_which):
        mock_which.return_value = None
        mock_exists.return_value = False

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        assert bridge.is_available() is False


def _mock_subprocess_result(returncode=0, stderr=""):
    return MagicMock(returncode=returncode, stderr=stderr)


def _mock_subprocess_with_output(cwd: str | None) -> MagicMock:
    """Create mock subprocess result that also creates output file."""
    if cwd is None:
        return _mock_subprocess_result()
    output_dir = os.path.join(cwd, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "processed.wav")
    Path(output_file).touch()
    return _mock_subprocess_result()


class TestTypeScriptBridgeCallAudioEngine:
    """Tests for TypeScriptBridge.call_audio_engine."""

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_returns_output_path(self, mock_copy2, mock_subprocess):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            def capture_run(cmd, **kwargs):
                cwd = kwargs.get("cwd")
                return _mock_subprocess_with_output(cwd)

            mock_subprocess.side_effect = capture_run

            result = bridge.call_audio_engine(
                input_files=[input_wav],
                output_path=output_path,
                config={"bpm": 125, "key": "Am"},
            )

            assert result == output_path

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_spawns_node_with_config(
        self, mock_copy2, mock_subprocess
    ):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        captured_cmd = None
        captured_cwd = None

        def capture_run(cmd, **kwargs):
            nonlocal captured_cmd, captured_cwd
            captured_cmd = cmd
            captured_cwd = kwargs.get("cwd")
            cwd = kwargs.get("cwd")
            return _mock_subprocess_with_output(cwd)

        mock_subprocess.side_effect = capture_run

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            bridge.call_audio_engine(
                input_files=[input_wav],
                output_path=output_path,
                config={"bpm": 125},
            )

            assert captured_cmd is not None
            assert "node" in captured_cmd[0]
            assert "/fake/effects/dist/index.js" in captured_cmd[1]
            assert "--config" in captured_cmd

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_writes_config_json(self, mock_copy2, mock_subprocess):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        captured_config = {}

        def capture_run(cmd, **kwargs):
            config_idx = cmd.index("--config") + 1
            with open(cmd[config_idx]) as f:
                captured_config.update(json.load(f))
            cwd = kwargs.get("cwd")
            return _mock_subprocess_with_output(cwd)

        mock_subprocess.side_effect = capture_run

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            bridge.call_audio_engine(
                input_files=[input_wav],
                output_path=output_path,
                config={"bpm": 125, "key": "Am", "duration": 180.0},
            )

            assert captured_config["bpm"] == 125
            assert captured_config["key"] == "Am"
            assert captured_config["duration"] == 180.0

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_copies_input_stems(self, mock_copy2, mock_subprocess):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        with tempfile.TemporaryDirectory() as tmpdir:
            stem1 = os.path.join(tmpdir, "stem1.wav")
            stem2 = os.path.join(tmpdir, "stem2.wav")
            Path(stem1).touch()
            Path(stem2).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            def capture_run(cmd, **kwargs):
                cwd = kwargs.get("cwd")
                return _mock_subprocess_with_output(cwd)

            mock_subprocess.side_effect = capture_run

            bridge.call_audio_engine(
                input_files=[stem1, stem2],
                output_path=output_path,
                config={"bpm": 125},
            )

            assert mock_copy2.call_count == 3  # 2 inputs + 1 output copy

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_raises_bridge_error_on_nonzero_exit(
        self, mock_copy2, mock_subprocess
    ):
        mock_subprocess.return_value = _mock_subprocess_result(
            returncode=1, stderr="Error: invalid config"
        )
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            with pytest.raises(BridgeError, match="Effects processing failed"):
                bridge.call_audio_engine(
                    input_files=[input_wav],
                    output_path=output_path,
                    config={"bpm": 125},
                )

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_includes_stderr_in_error(
        self, mock_copy2, mock_subprocess
    ):
        mock_subprocess.return_value = _mock_subprocess_result(
            returncode=2, stderr="TypeError: expected number"
        )
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            with pytest.raises(BridgeError) as exc_info:
                bridge.call_audio_engine(
                    input_files=[input_wav],
                    output_path=output_path,
                    config={"bpm": 125},
                )

            assert "TypeError: expected number" in str(exc_info.value)

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_uses_temp_dir_with_prefix(
        self, mock_copy2, mock_subprocess
    ):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        captured_cwd = None

        def capture_run(cmd, **kwargs):
            nonlocal captured_cwd
            captured_cwd = kwargs.get("cwd")
            cwd = kwargs.get("cwd")
            return _mock_subprocess_with_output(cwd)

        mock_subprocess.side_effect = capture_run

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            bridge.call_audio_engine(
                input_files=[input_wav],
                output_path=output_path,
                config={"bpm": 125},
            )

            assert captured_cwd is not None
            assert "openmusic-" in os.path.basename(captured_cwd)

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_creates_input_and_output_dirs(
        self, mock_copy2, mock_subprocess
    ):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        created_dirs = []

        original_makedirs = os.makedirs

        def track_makedirs(path, *args, **kwargs):
            created_dirs.append(path)
            return original_makedirs(path, *args, **kwargs)

        def capture_run(cmd, **kwargs):
            cwd = kwargs.get("cwd")
            return _mock_subprocess_with_output(cwd)

        mock_subprocess.side_effect = capture_run

        with patch("os.makedirs", side_effect=track_makedirs):
            with tempfile.TemporaryDirectory() as tmpdir:
                input_wav = os.path.join(tmpdir, "stem.wav")
                Path(input_wav).touch()
                output_path = os.path.join(tmpdir, "output.wav")

                bridge.call_audio_engine(
                    input_files=[input_wav],
                    output_path=output_path,
                    config={"bpm": 125},
                )

        dir_names = [os.path.basename(d) for d in created_dirs]
        assert "input" in dir_names
        assert "output" in dir_names


class TestTypeScriptBridgeCleanup:
    """Tests for TypeScriptBridge.cleanup."""

    def test_cleanup_removes_temp_directory(self):
        tmpdir = tempfile.mkdtemp(prefix="openmusic-test-")
        test_file = os.path.join(tmpdir, "test.txt")
        Path(test_file).touch()

        assert os.path.exists(tmpdir)

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        bridge.cleanup(tmpdir)

        assert not os.path.exists(tmpdir)

    def test_cleanup_nonexistent_dir_does_not_raise(self):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        bridge.cleanup("/nonexistent/path/that/does/not/exist")

    def test_cleanup_removes_nested_files(self):
        tmpdir = tempfile.mkdtemp(prefix="openmusic-test-")
        nested_dir = os.path.join(tmpdir, "input")
        os.makedirs(nested_dir)
        nested_file = os.path.join(nested_dir, "stem.wav")
        Path(nested_file).touch()

        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")
        bridge.cleanup(tmpdir)

        assert not os.path.exists(tmpdir)


class TestTypeScriptBridgeDefaultTimeout:
    """Tests for default timeout behavior."""

    @patch("openmusic.bridge.typescript_bridge.subprocess.run")
    @patch("openmusic.bridge.typescript_bridge.shutil.copy2")
    def test_call_audio_engine_has_default_timeout(self, mock_copy2, mock_subprocess):
        bridge = TypeScriptBridge(effects_bin="/fake/effects/dist/index.js")

        captured_timeout = None

        def capture_run(cmd, **kwargs):
            nonlocal captured_timeout
            captured_timeout = kwargs.get("timeout")
            cwd = kwargs.get("cwd")
            return _mock_subprocess_with_output(cwd)

        mock_subprocess.side_effect = capture_run

        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "stem.wav")
            Path(input_wav).touch()
            output_path = os.path.join(tmpdir, "output.wav")

            bridge.call_audio_engine(
                input_files=[input_wav],
                output_path=output_path,
                config={"bpm": 125},
            )

            assert captured_timeout == 600
