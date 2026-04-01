"""Tape saturation effect for OpenMusic.

Implements soft-clipping using tanh function to emulate analog tape saturation.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class TapeSaturation(Effect):
    """Tape saturation effect using soft-clipping.

    Uses tanh function to create warm, analog-style saturation. The effect
    can be adjusted with drive control and optional bias tone.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the TapeSaturation effect."""
        self.name = "tape_saturation"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with tape saturation.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - drive: Saturation amount (0-100, default 50)
                   - wet_dry_mix: Wet/dry balance (0-100, default 50)
                   - bias_tone: Optional bias tone frequency in Hz (default None)

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters with defaults
        drive = float(params.get("drive", 50))
        wet_dry_mix = float(params.get("wet_dry_mix", 50))
        bias_tone = params.get("bias_tone", None)

        # Normalize drive to 0-10 range for tanh
        drive_normalized = drive / 10.0

        # Apply saturation: output = tanh(drive * input) / tanh(drive)
        # This normalizes the output to prevent clipping
        saturated = np.tanh(drive_normalized * audio) / np.tanh(drive_normalized + 1e-7)

        # Apply wet/dry mix
        mix_ratio = wet_dry_mix / 100.0
        output = audio * (1.0 - mix_ratio) + saturated * mix_ratio

        # Add optional bias tone (low-frequency oscillator)
        if bias_tone is not None and isinstance(bias_tone, dict):
            output = self._add_bias_tone(output, bias_tone, audio.shape)

        return output

    def _add_bias_tone(
        self, audio: np.ndarray, bias_params: Dict[str, Any], shape: tuple
    ) -> np.ndarray:
        """Add optional bias tone to the audio.

        Args:
            audio: Input audio
            bias_params: Dictionary with 'frequency' and 'amplitude'
            shape: Output shape

        Returns:
            Audio with bias tone added
        """
        frequency = float(bias_params.get("frequency", 50))
        amplitude = float(bias_params.get("amplitude", 0.01))

        # Generate bias tone
        sample_rate = 48000  # Default sample rate
        n_samples = shape[-1]
        t = np.arange(n_samples) / sample_rate

        bias_waveform = amplitude * np.sin(2 * np.pi * frequency * t)

        # Add to audio
        if len(shape) == 1:
            return audio + bias_waveform
        else:
            # Stereo: apply to both channels
            return audio + bias_waveform[np.newaxis, :]
