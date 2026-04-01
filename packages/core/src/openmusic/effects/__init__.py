"""OpenMusic effects module - audio effects for offline processing."""

from .base import Effect
from .saturation import TapeSaturation
from .delay import MultiTapDelay

__all__ = ["Effect", "TapeSaturation", "MultiTapDelay"]
