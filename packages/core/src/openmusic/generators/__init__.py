"""Audio generator protocol and implementations for OpenMusic."""

from openmusic.generators.base import AudioGenerator
from openmusic.generators.stable_audio import StableAudioGenerator

__all__ = [
    "AudioGenerator",
    "StableAudioGenerator",
]
