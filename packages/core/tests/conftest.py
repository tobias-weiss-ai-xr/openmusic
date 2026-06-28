"""pytest conftest — mocks pedalboard (crashes on Python 3.14) and skips optional dep tests."""

import sys
from unittest.mock import MagicMock
import numpy as np


def _mock_pedalboard_call(audio, sample_rate):
    """Mock pedalboard call that returns audio with proper shape attributes."""
    # Return input audio unchanged but ensure it has proper shape
    if audio.ndim == 1:
        return np.column_stack([audio, audio])
    return audio


class MockPedalboard:
    """Mock Pedalboard class that returns proper numpy arrays when called."""

    def __init__(self, effects=None):
        self.effects = effects or []

    def __call__(self, audio, sample_rate):
        return _mock_pedalboard_call(audio, sample_rate)


# Create the mock pedalboard module
_pb = MagicMock()
_pb.__version__ = "0.9.0"
_pb.Pedalboard = MockPedalboard
_pb.load_plugin = MagicMock()

sys.modules["pedalboard"] = _pb
sys.modules["pedalboard_native"] = MagicMock()


def pytest_collection_modifyitems(config, items):
    skip_reasons = {}

    if not _import_ok("pyloudnorm"):
        skip_reasons["pyloudnorm"] = "pyloudnorm not installed"
    if not _import_ok("isobar"):
        skip_reasons["isobar"] = "isobar not installed"

    file_skips = {
        "test_loudness.py": "pyloudnorm",
        "test_midi_export.py": "isobar",
    }

    for item in items:
        nodeid = item.nodeid
        for filename, mod_key in file_skips.items():
            if f"/{filename}::" in nodeid and mod_key in skip_reasons:
                item.add_marker(pytest.mark.skip(reason=skip_reasons[mod_key]))


def _import_ok(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False
