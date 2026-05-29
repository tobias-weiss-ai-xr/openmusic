from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class AudioGenerator(Protocol):
    """Protocol for AI audio texture generators.

    Any audio generator used by OpenMusic must implement these methods
    so that MixOrchestrator can swap between generators transparently.
    """

    def generate_texture(
        self,
        prompt: str,
        duration: int = 60,
        bpm: int = 125,
        key: str = "Am",
    ) -> Path:
        """Generate an audio texture and return the path to the saved WAV file.

        Args:
            prompt: Text description of the desired audio texture.
            duration: Target duration in seconds.
            bpm: Beats per minute for rhythmic generation.
            key: Musical key (e.g. "Dm", "Am", "C").

        Returns:
            Path to a WAV file containing the generated audio.
        """
        ...

    @classmethod
    def is_available(cls) -> bool:
        """Check whether this generator's dependencies are installed."""
        ...

    @classmethod
    def get_gpu_info(cls) -> dict:
        """Return GPU capability info: name, vram_gb, available, tier."""
        ...
