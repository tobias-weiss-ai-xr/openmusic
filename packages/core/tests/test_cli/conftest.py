"""Fixture to mock heavy dependencies (pedalboard, scipy, etc.) that crash or are
unavailable on this system, to allow CLI-level tests to import cleanly."""

import sys
from unittest.mock import MagicMock

# Mock pedalboard before any test imports trigger the real module
# This avoids the Illegal Instruction crash from pedalboard_native
pedalboard_mock = MagicMock()
pedalboard_mock.load_plugin = MagicMock()
pedalboard_mock.Pedalboard = MagicMock()
pedalboard_mock.__version__ = "0.9.0"

sys.modules["pedalboard"] = pedalboard_mock
sys.modules["pedalboard_native"] = MagicMock()


