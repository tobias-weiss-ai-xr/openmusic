"""pytest conftest — mocks pedalboard (crashes on Python 3.14) and skips optional dep tests."""

import sys
from unittest.mock import MagicMock

_pb = MagicMock()
_pb.load_plugin = MagicMock()
_pb.Pedalboard = MagicMock()
_pb.__version__ = "0.9.0"
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
