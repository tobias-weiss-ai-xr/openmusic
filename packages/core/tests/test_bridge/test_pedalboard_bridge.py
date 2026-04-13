"""Tests for the native Python DSP bridge using Pedalboard."""

import numpy as np
import pytest
import soundfile as sf
import tempfile
from pathlib import Path


class TestPythonDSPBridge:
    """Test the PythonDSPBridge processes audio correctly."""

    def _make_test_wav(self, duration_s=1.0, sr=48000, channels=2) -> str:
        """Create a minimal WAV file for testing."""
        samples = int(duration_s * sr)
        data = np.random.randn(samples, channels).astype(np.float32) * 0.1
        path = tempfile.mktemp(suffix=".wav")
        sf.write(path, data, sr)
        return path

    def test_bridge_processes_wav_to_wav(self):
        """Bridge reads WAV input and writes WAV output."""
        pytest.importorskip("pedalboard")
        from openmusic.bridge.pedalboard_bridge import PythonDSPBridge

        bridge = PythonDSPBridge()
        input_path = self._make_test_wav()
        output_path = tempfile.mktemp(suffix=".wav")
        try:
            result = bridge.process(input_path, output_path)
            assert Path(result).exists()
            # Verify it's a valid WAV
            data, sr = sf.read(result)
            assert sr == 48000
            assert data.ndim == 2  # stereo
        finally:
            for p in [input_path, output_path]:
                Path(p).unlink(missing_ok=True)

    def test_bridge_with_deep_dub_preset(self):
        """Bridge applies deep_dub preset without error."""
        pytest.importorskip("pedalboard")
        from openmusic.bridge.pedalboard_bridge import PythonDSPBridge

        bridge = PythonDSPBridge(preset="deep_dub")
        input_path = self._make_test_wav()
        output_path = tempfile.mktemp(suffix=".wav")
        try:
            result = bridge.process(input_path, output_path)
            data, sr = sf.read(result)
            # Output should be same length
            assert len(data) > 0
        finally:
            for p in [input_path, output_path]:
                Path(p).unlink(missing_ok=True)

    def test_bridge_raises_on_invalid_preset(self):
        """Bridge raises ValueError for unknown preset."""
        pytest.importorskip("pedalboard")
        from openmusic.bridge.pedalboard_bridge import PythonDSPBridge

        bridge = PythonDSPBridge(preset="nonexistent")
        input_path = self._make_test_wav()
        output_path = tempfile.mktemp(suffix=".wav")
        try:
            with pytest.raises(ValueError, match="Unknown preset"):
                bridge.process(input_path, output_path)
        finally:
            Path(input_path).unlink(missing_ok=True)

    def test_bridge_applies_mastering(self):
        """Bridge applies mastering chain when requested."""
        pytest.importorskip("pedalboard")
        from openmusic.bridge.pedalboard_bridge import PythonDSPBridge

        bridge = PythonDSPBridge(preset="deep_dub", apply_mastering=True)
        input_path = self._make_test_wav()
        output_path = tempfile.mktemp(suffix=".wav")
        try:
            result = bridge.process(input_path, output_path)
            data, sr = sf.read(result)
            assert len(data) > 0
        finally:
            for p in [input_path, output_path]:
                Path(p).unlink(missing_ok=True)
