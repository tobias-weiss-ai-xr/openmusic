"""Mid-side stereo processing for OpenMusic dub techno generation.

Implements mid-side stereo processing for control over stereo imaging,
including independent EQ/compression of mid (center) and side (stereo) channels.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class MidSideStereoWidener(Effect):
    """Mid-side stereo widener for dub techno spatial effects.

    Processes audio using mid-side encoding to independently control the
    center (mid) and stereo (side) information. Allows stereo width
    adjustment, independent EQ, and side channel compression.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the MidSideStereoWidener effect."""
        self.name = "mid_side_widener"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with mid-side stereo processing.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio (passed through unchanged)
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - stereo_width: Width multiplier (0-2, 1=normal, <1=narrower, >1=wider)
                   - mid_eq: Dictionary with 'frequency', 'gain_db', 'Q' (optional)
                   - side_eq: Dictionary with 'frequency', 'gain_db', 'Q' (optional)
                   - side_compression: Dictionary with 'threshold_db', 'ratio', 'attack_ms',
                                        'release_ms' (optional)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters with defaults
        stereo_width = float(params.get("stereo_width", 1.0))
        mid_eq_params = params.get("mid_eq", {})
        side_eq_params = params.get("side_eq", {})
        side_comp_params = params.get("side_compression", {})
        sample_rate = int(params.get("sample_rate", 48000))

        # Clamp stereo_width to valid range
        stereo_width = np.clip(stereo_width, 0.0, 2.0)

        # Handle mono audio - pass through unchanged
        if len(audio.shape) == 1:
            return audio.copy()

        # Must be stereo
        if audio.shape[0] != 2:
            raise ValueError("Mid-side processing requires stereo audio (2 channels)")

        left = audio[0]
        right = audio[1]

        # M/S encoding
        # M = (L + R) / sqrt(2)  (center/mono information)
        # S = (L - R) / sqrt(2)  (stereo/side information)
        mid = (left + right) / np.sqrt(2)
        side = (left - right) / np.sqrt(2)

        # Process mid channel with EQ
        if mid_eq_params:
            mid = self._apply_eq(mid, mid_eq_params, sample_rate)

        # Process side channel with EQ and compression
        if side_eq_params:
            side = self._apply_eq(side, side_eq_params, sample_rate)

        if side_comp_params:
            side = self._apply_compression(side, side_comp_params, sample_rate)

        # M/S decoding with stereo width control
        # L' = M + S * width
        # R' = M - S * width
        # Normalize by sqrt(2) to maintain level
        widthed_side = side * stereo_width
        output_left = (mid + widthed_side) / np.sqrt(2)
        output_right = (mid - widthed_side) / np.sqrt(2)

        return np.stack([output_left, output_right])

    def _apply_eq(
        self,
        audio: np.ndarray,
        eq_params: Dict[str, Any],
        sample_rate: int,
    ) -> np.ndarray:
        """Apply EQ to audio using simple bell filter.

        Args:
            audio: Mono audio input
            eq_params: Dictionary with 'frequency', 'gain_db', 'Q'
            sample_rate: Audio sample rate

        Returns:
            Processed audio with EQ applied
        """
        frequency = float(eq_params.get("frequency", 1000))
        gain_db = float(eq_params.get("gain_db", 0))
        Q = float(eq_params.get("Q", 1.0))

        # Convert gain from dB to linear
        gain_linear = 10 ** (gain_db / 20.0)

        # Simple frequency domain approach using FFT
        ft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / sample_rate)

        # Calculate bandwidth from Q
        bandwidth = frequency / Q

        # Create bell response
        # Normalize frequency for Gaussian response
        response = np.exp(-0.5 * ((freqs - frequency) / (bandwidth / 2)) ** 2)

        # Interpolate between no gain (0) and full gain based on response
        gain_curve = 1.0 + response * (gain_linear - 1.0)

        # Apply gain to frequency domain
        ft_eq = ft * gain_curve

        # Convert back to time domain
        audio_eq = np.fft.irfft(ft_eq, n=len(audio))

        return audio_eq

    def _apply_compression(
        self,
        audio: np.ndarray,
        comp_params: Dict[str, Any],
        sample_rate: int,
    ) -> np.ndarray:
        """Apply simple compression to audio.

        Args:
            audio: Mono audio input
            comp_params: Dictionary with 'threshold_db', 'ratio', 'attack_ms', 'release_ms'
            sample_rate: Audio sample rate

        Returns:
            Processed audio with compression applied
        """
        threshold_db = float(comp_params.get("threshold_db", -20))
        ratio = float(comp_params.get("ratio", 4))
        attack_ms = float(comp_params.get("attack_ms", 10))
        release_ms = float(comp_params.get("release_ms", 200))

        # Convert threshold from dB to linear
        threshold_linear = 10 ** (threshold_db / 20.0)

        # Calculate attack and release coefficients
        attack_coeff = np.exp(-1.0 / (attack_ms / 1000.0 * sample_rate))
        release_coeff = np.exp(-1.0 / (release_ms / 1000.0 * sample_rate))

        # Create envelope using absolute value
        envelope = np.zeros(len(audio))
        current_env = 0.0

        for i in range(len(audio)):
            peak = abs(audio[i])

            if peak > current_env:
                current_env = peak + (current_env - peak) * attack_coeff
            else:
                current_env = peak + (current_env - peak) * release_coeff

            envelope[i] = current_env

        # Calculate gain reduction
        gain_reduction = np.ones(len(audio))

        for i in range(len(audio)):
            if envelope[i] > threshold_linear:
                overshoot_db = 20 * np.log10(envelope[i] / threshold_linear)
                reduction_db = overshoot_db * (1 - 1 / ratio)
                gain_reduction[i] = 10 ** (-reduction_db / 20.0)
            else:
                gain_reduction[i] = 1.0

        # Smooth gain changes
        smoothed_gain = np.zeros(len(audio))
        current_gain = 1.0

        for i in range(len(gain_reduction)):
            if gain_reduction[i] < current_gain:
                current_gain = (
                    gain_reduction[i]
                    + (current_gain - gain_reduction[i]) * attack_coeff
                )
            else:
                current_gain = (
                    gain_reduction[i]
                    + (current_gain - gain_reduction[i]) * release_coeff
                )

            smoothed_gain[i] = current_gain

        # Apply compression
        return audio * smoothed_gain
