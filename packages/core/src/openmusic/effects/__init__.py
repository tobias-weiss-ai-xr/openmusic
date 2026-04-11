"""OpenMusic effects module - audio effects for offline processing."""

from .base import Effect
from .compression import SidechainCompression
from .delay import MultiTapDelay
from .granular_delay import GranularDelay
from .saturation import TapeSaturation
from .stereo import MidSideStereoWidener
from .lfo import LFOModulationEngine

__all__ = [
    "TapeSaturation",
    "MultiTapDelay",
    "GranularDelay",
    "SidechainCompression",
    "MidSideStereoWidener",
    "LFOModulationEngine",
]
