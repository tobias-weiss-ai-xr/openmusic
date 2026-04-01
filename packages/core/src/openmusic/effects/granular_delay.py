"""Granular delay effect for OpenMusic dub techno generation.

Implements a granular-based delay that produces textured, evolving repeats
through grain-based processing with randomization and feedback.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class GranularDelay(Effect):
    """Granular delay effect for dub techno echoes.

    Creates textured, evolving delay repeats by dividing audio into grains,
    applying random time/pitch variations, and reassembling with feedback.
    Produces the signature dub techno sound of broken, atmospheric echoes.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the GranularDelay effect."""
        self.name = "granular_delay"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with granular delay.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - grain_size_ms: Duration of each grain in milliseconds
                                   (10-200, default 50)
                   - grain_density: Number of grains per second (1-20, default 5)
                   - randomization_amount: Random pitch/time variation (0-100%, default 30%)
                   - feedback: Feedback amount for repeats (0-100%, default 40%)
                   - wet_dry_mix: Wet/dry balance (0-100%, default 60%)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters with defaults
        grain_size_ms = float(params.get("grain_size_ms", 50))
        grain_density = float(params.get("grain_density", 5))
        randomization_amount = float(params.get("randomization_amount", 30))
        feedback = float(params.get("feedback", 40))
        wet_dry_mix = float(params.get("wet_dry_mix", 60))
        sample_rate = int(params.get("sample_rate", 48000))

        # Clamp parameters to valid ranges
        grain_size_ms = np.clip(grain_size_ms, 10, 200)
        grain_density = np.clip(grain_density, 1, 20)
        randomization_amount = np.clip(randomization_amount, 0, 100)
        feedback = np.clip(feedback, 0, 100)
        wet_dry_mix = np.clip(wet_dry_mix, 0, 100)

        # Determine audio format
        is_stereo = len(audio.shape) > 1 and audio.shape[0] == 2

        if is_stereo:
            # Process each channel independently
            left_output = self._process_mono(
                audio[0],
                grain_size_ms,
                grain_density,
                randomization_amount,
                feedback,
                wet_dry_mix,
                sample_rate,
            )
            right_output = self._process_mono(
                audio[1],
                grain_size_ms,
                grain_density,
                randomization_amount,
                feedback,
                wet_dry_mix,
                sample_rate,
            )
            return np.stack([left_output, right_output])
        else:
            return self._process_mono(
                audio,
                grain_size_ms,
                grain_density,
                randomization_amount,
                feedback,
                wet_dry_mix,
                sample_rate,
            )

    def _process_mono(
        self,
        audio: np.ndarray,
        grain_size_ms: float,
        grain_density: float,
        randomization_amount: float,
        feedback: float,
        wet_dry_mix: float,
        sample_rate: int,
    ) -> np.ndarray:
        """Process mono audio with granular delay.

        Args:
            audio: Mono audio input
            grain_size_ms: Grain duration in milliseconds
            grain_density: Grains per second
            randomization_amount: Random variation percentage (0-100)
            feedback: Feedback amount (0-100)
            wet_dry_mix: Wet/dry mix ratio (0-100)
            sample_rate: Audio sample rate

        Returns:
            Processed mono audio
        """
        # Handle empty input
        if len(audio) == 0:
            return audio.copy()

        # Convert grain size to samples
        grain_size_samples = int(grain_size_ms / 1000.0 * sample_rate)
        grain_size_samples = max(grain_size_samples, 1)  # At least 1 sample

        # Calculate hop size based on density
        # Higher density = smaller hop size = more overlap
        hop_size_samples = int(sample_rate / grain_density)
        hop_size_samples = max(hop_size_samples, 1)  # At least 1 sample

        # Ensure hop size doesn't exceed grain size
        hop_size_samples = min(hop_size_samples, grain_size_samples)

        # Create grain envelope (raised cosine for smooth fade in/out)
        envelope = self._create_grain_envelope(grain_size_samples)

        # Randomization factor (normalized -1 to 1 range for variation)
        random_factor = randomization_amount / 100.0

        # Feedback amount as a multiplier
        feedback_amount = feedback / 100.0

        # Create output buffer
        output = np.zeros(len(audio))

        # Feedback buffer for accumulating delayed signal
        feedback_buffer = np.zeros(len(audio) + grain_size_samples * 2)

        # Process grains
        position = 0
        while position < len(audio):
            # Calculate random variation for this grain
            if random_factor > 0:
                time_variation = np.random.uniform(-random_factor, random_factor)
                pitch_variation = np.random.uniform(-random_factor, random_factor)
            else:
                time_variation = 0
                pitch_variation = 0

            # Extract grain from input
            grain_start = position
            grain_end = min(position + grain_size_samples, len(audio))
            grain = audio[grain_start:grain_end].copy()

            # Pad grain if needed
            if len(grain) < grain_size_samples:
                grain = np.pad(grain, (0, grain_size_samples - len(grain)))

            # Apply envelope to grain
            grain = grain * envelope

            # Apply pitch variation via resampling
            if pitch_variation != 0:
                grain = self._apply_pitch_variation(grain, pitch_variation * 0.5)

            # Apply time variation (stretch/shrink)
            if time_variation != 0:
                grain = self._apply_time_variation(grain, time_variation)

            # Add grain to output at current position
            output_pos = position
            for i in range(len(grain)):
                out_idx = output_pos + i
                if out_idx < len(output):
                    output[out_idx] += grain[i]

            # Write to feedback buffer for delay
            fb_pos = position + grain_size_samples
            for i in range(len(grain)):
                buf_idx = fb_pos + i
                if buf_idx < len(feedback_buffer):
                    feedback_buffer[buf_idx] += grain[i]

            # Apply feedback: read from earlier position in buffer
            if feedback_amount > 0:
                read_pos = position
                for i in range(len(grain)):
                    fb_idx = read_pos + i
                    if fb_idx < len(feedback_buffer):
                        # Add feedback to current grain position
                        write_idx = position + i
                        if write_idx < len(output):
                            output[write_idx] += (
                                feedback_buffer[fb_idx] * feedback_amount
                            )

            # Move to next grain position
            position += hop_size_samples

        # Apply wet/dry mix
        mix_ratio = wet_dry_mix / 100.0
        output = audio * (1.0 - mix_ratio) + output * mix_ratio

        return output

    def _create_grain_envelope(self, size: int) -> np.ndarray:
        """Create a smooth grain envelope.

        Args:
            size: Envelope size in samples

        Returns:
            Envelope array with raised cosine shape
        """
        if size <= 0:
            return np.array([1.0])

        # Raised cosine envelope (Hann window)
        # Provides smooth fade in and out to avoid clicks
        envelope = 0.5 * (
            1.0 - np.cos(2.0 * np.pi * np.arange(size) / max(size - 1, 1))
        )

        return envelope

    def _apply_pitch_variation(self, grain: np.ndarray, variation: float) -> np.ndarray:
        """Apply pitch variation via resampling.

        Args:
            grain: Input grain
            variation: Pitch variation factor (-0.5 to 0.5)

        Returns:
            Resampled grain with pitch shift
        """
        if variation == 0:
            return grain

        # Calculate new length based on pitch variation
        # Positive variation = higher pitch = shorter duration
        new_length = int(len(grain) / (1 + variation))
        new_length = max(new_length, 1)

        # Resample using linear interpolation
        if new_length == len(grain):
            return grain

        # Create interpolation indices
        original_indices = np.linspace(
            0, len(grain) - 1, num=new_length, dtype=np.float64
        )

        # Linear interpolation
        output = np.interp(original_indices, np.arange(len(grain)), grain)

        return output

    def _apply_time_variation(self, grain: np.ndarray, variation: float) -> np.ndarray:
        """Apply time variation (stretching/shrinking).

        Args:
            grain: Input grain
            variation: Time variation factor (-0.5 to 0.5)

        Returns:
            Stretched/shrunk grain
        """
        if variation == 0:
            return grain

        # Calculate new length based on time variation
        # Positive variation = slower = longer duration
        new_length = int(len(grain) * (1 + variation))
        new_length = max(new_length, 1)

        # Resample using linear interpolation
        if new_length == len(grain):
            return grain

        # Create interpolation indices
        original_indices = np.linspace(
            0, len(grain) - 1, num=new_length, dtype=np.float64
        )

        # Linear interpolation
        output = np.interp(original_indices, np.arange(len(grain)), grain)

        return output
