"""Sidechain compression effect for OpenMusic dub techno generation.

Implements a compressor with envelope follower to create the pumping
sidechain effect characteristic of dub techno.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class SidechainCompression(Effect):
    """Sidechain compression effect for dub techno pumping.

    Compresses audio when the signal level exceeds threshold, creating
    the classic "pumping" sidechain effect used in dub techno to duck
    pads and ambience when the kick drum hits.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the SidechainCompression effect."""
        self.name = "sidechain_compression"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with sidechain compression.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - threshold_db: Compression threshold in dB (-60 to 0, default -20)
                   - ratio: Compression ratio (1:1 to 20:1, default 4)
                   - attack_ms: Attack time in ms (1-100, default 10)
                   - release_ms: Release time in ms (10-1000, default 200)
                   - knee_db: Soft knee width in dB (0-12, default 4)
                   - wet_dry_mix: Wet/dry balance (0-100%, default 70%)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters with defaults
        threshold_db = float(params.get("threshold_db", -20))
        ratio = float(params.get("ratio", 4))
        attack_ms = float(params.get("attack_ms", 10))
        release_ms = float(params.get("release_ms", 200))
        knee_db = float(params.get("knee_db", 4))
        wet_dry_mix = float(params.get("wet_dry_mix", 70))
        sample_rate = int(params.get("sample_rate", 48000))

        # Clamp parameters to valid ranges
        threshold_db = np.clip(threshold_db, -60, 0)
        ratio = np.clip(ratio, 1, 20)
        attack_ms = np.clip(attack_ms, 1, 100)
        release_ms = np.clip(release_ms, 10, 1000)
        knee_db = np.clip(knee_db, 0, 12)
        wet_dry_mix = np.clip(wet_dry_mix, 0, 100)

        # Determine audio format
        is_stereo = len(audio.shape) > 1 and audio.shape[0] == 2

        if is_stereo:
            # Process each channel independently
            left_output = self._process_mono(
                audio[0],
                threshold_db,
                ratio,
                attack_ms,
                release_ms,
                knee_db,
                wet_dry_mix,
                sample_rate,
            )
            right_output = self._process_mono(
                audio[1],
                threshold_db,
                ratio,
                attack_ms,
                release_ms,
                knee_db,
                wet_dry_mix,
                sample_rate,
            )
            return np.stack([left_output, right_output])
        else:
            return self._process_mono(
                audio,
                threshold_db,
                ratio,
                attack_ms,
                release_ms,
                knee_db,
                wet_dry_mix,
                sample_rate,
            )

    def _process_mono(
        self,
        audio: np.ndarray,
        threshold_db: float,
        ratio: float,
        attack_ms: float,
        release_ms: float,
        knee_db: float,
        wet_dry_mix: float,
        sample_rate: int,
    ) -> np.ndarray:
        """Process mono audio with sidechain compression.

        Args:
            audio: Mono audio input
            threshold_db: Compression threshold in decibels
            ratio: Compression ratio (e.g., 4 = 4:1 compression)
            attack_ms: Attack time in milliseconds
            release_ms: Release time in milliseconds
            knee_db: Soft knee width in decibels
            wet_dry_mix: Wet/dry mix ratio (0-100)
            sample_rate: Audio sample rate

        Returns:
            Processed mono audio
        """
        # Handle empty input
        if len(audio) == 0:
            return audio.copy()

        # Convert threshold from dB to linear amplitude
        threshold_linear = 10 ** (threshold_db / 20.0)

        # Calculate attack and release coefficients
        attack_coeff = np.exp(-1.0 / (attack_ms / 1000.0 * sample_rate))
        release_coeff = np.exp(-1.0 / (release_ms / 1000.0 * sample_rate))

        # Convert knee width to linear
        knee_linear = 10 ** (knee_db / 20.0)

        # Create envelope using absolute value (peak detection)
        envelope = np.zeros(len(audio))
        current_env = 0.0

        for i in range(len(audio)):
            # Peak detection with fast attack and slow release
            peak = abs(audio[i])

            if peak > current_env:
                # Attack phase
                current_env = peak + (current_env - peak) * attack_coeff
            else:
                # Release phase
                current_env = peak + (current_env - peak) * release_coeff

            envelope[i] = current_env

        # Calculate gain reduction
        gain_reduction = np.ones(len(audio))

        for i in range(len(audio)):
            if envelope[i] > threshold_linear:
                # Calculate overshoot in dB
                overshoot_db = 20 * np.log10(envelope[i] / threshold_linear)

                # Apply soft knee
                if knee_db > 0 and overshoot_db < knee_db / 2:
                    # Within soft knee region
                    knee_ratio = overshoot_db / (knee_db / 2)
                    effective_ratio = 1 + knee_ratio * (ratio - 1)
                    reduction_db = (
                        overshoot_db * (effective_ratio - 1) / effective_ratio
                    )
                else:
                    # Above threshold (hard compression region)
                    reduction_db = overshoot_db * (1 - 1 / ratio)

                # Convert reduction to linear gain
                gain_reduction[i] = 10 ** (-reduction_db / 20.0)
            else:
                gain_reduction[i] = 1.0

        # Smooth gain changes to prevent clicking
        smoothed_gain = np.zeros(len(audio))
        current_gain = 1.0

        for i in range(len(gain_reduction)):
            if gain_reduction[i] < current_gain:
                # Attack on gain reduction (fast)
                current_gain = (
                    gain_reduction[i]
                    + (current_gain - gain_reduction[i]) * attack_coeff
                )
            else:
                # Release on gain reduction (slow)
                current_gain = (
                    gain_reduction[i]
                    + (current_gain - gain_reduction[i]) * release_coeff
                )

            smoothed_gain[i] = current_gain

        # Apply compression
        compressed_audio = audio * smoothed_gain

        # Apply wet/dry mix
        mix_ratio = wet_dry_mix / 100.0
        output = audio * (1.0 - mix_ratio) + compressed_audio * mix_ratio

        return output
