"""Fixture to mock heavy dependencies (pedalboard, video pipeline, etc.) that
crash or are unavailable on this system, to allow CLI-level tests to import cleanly."""

import sys
from unittest.mock import MagicMock

# Mock pedalboard before any test imports trigger the real module.
# This avoids the Illegal Instruction crash from pedalboard_native
# on CPUs that don't support the compiled instruction set.
pedalboard_mock = MagicMock()
pedalboard_mock.load_plugin = MagicMock()
pedalboard_mock.Pedalboard = MagicMock()
pedalboard_mock.__version__ = "0.9.0"

sys.modules["pedalboard"] = pedalboard_mock
sys.modules["pedalboard_native"] = MagicMock()

# Mock the full openmusic.video package to avoid importing heavy ML deps
# (langgraph, diffusers, transformers, accelerate) which may not be installed
# in development environments and are not needed for CLI-level testing.
video_mock = MagicMock()
video_mock.build_video_pipeline_graph = MagicMock()
sys.modules["openmusic.video"] = video_mock
