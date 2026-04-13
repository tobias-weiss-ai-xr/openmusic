"""OpenMusic effects module - audio effects for offline processing."""

from .base import Effect
from .compression import SidechainCompression
from .delay import MultiTapDelay
from .granular_delay import GranularDelay
from .saturation import TapeSaturation
from .stereo import MidSideStereoWidener
from .lfo import LFOModulationEngine

# Native Python DSP effects using Spotify Pedalboard
# Import lazily to avoid breaking tests when modules not yet created
__all__ = [
    "TapeSaturation",
    "MultiTapDelay",
    "GranularDelay",
    "SidechainCompression",
    "MidSideStereoWidener",
    "LFOModulationEngine",
    "PedalboardEffectsChain",
    "Envelope",
    "LFO",
    "RandomWalk",
    "MasteringChain",
]


def __getattr__(name: str):
    """Lazy import for DSP effects modules."""
    if name == "PedalboardEffectsChain":
        from openmusic.effects.pedalboard_chain import PedalboardEffectsChain as _cls

        return _cls
    if name in ("Envelope", "LFO", "RandomWalk"):
        from openmusic.effects.automation import (
            Envelope as _Env,
            LFO as _LFO,
            RandomWalk as _RW,
        )

        if name == "Envelope":
            return _Env
        elif name == "LFO":
            return _LFO
        elif name == "RandomWalk":
            return _RW
    if name == "MasteringChain":
        from openmusic.effects.mastering import MasteringChain as _cls

        return _cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
