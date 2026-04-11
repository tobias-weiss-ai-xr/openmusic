"""LFO Modulation Engine for OpenMusic dub techno generation.

Implements Low Frequency Oscillator (LFO) modulation for effects automation,
supporting multiple waveform types to create dynamic, evolving effects over time.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class LFOModulationEngine(Effect):
    """LFO Modulation Engine for dub techno effects automation.

    Generates modulation curves using various waveform types (sine, triangle, square, random) that can be used to
    automate effect parameters over time.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize LFO Modulation Engine."""
        self.name = "lfo_modulation"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with LFO modulation.

        Args:
            audio: Input audio data (currently returned unchanged for compatibility).
                   Shape must be same as input.
            params: Dictionary containing:
                   - waveform: Waveform type ('sine', 'triangle', 'square', 'random')
                   - rate_hz: LFO frequency in Hz (0.1-20, default 1)
                   - depth: Modulation depth percentage (0-100%, default 50%)
                   - target_parameter: Which effect parameter to modulate (string identifier)
                   - phase_offset: Phase offset in cycles (0-1, default 0)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Original audio unchanged (LFO would be used for internal parameter
        """
        # Extract parameters with defaults
        waveform = str(params.get("waveform", "sine"))
        rate_hz = float(params.get("rate_hz", 1.0))
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))
        sample_rate = int(params.get("sample_rate", 48000))

        # Clamp parameters to valid ranges
        rate_hz = np.clip(rate_hz, 0.1, 20.0)
        depth = np.clip(depth, 0.0, 100.0)
        phase_offset = np.clip(phase_offset, 0.0, 1.0)

        # Validate waveform type
        valid_waveforms = {"sine", "triangle", "square", "random"}
        if waveform not in valid_waveforms:
            raise ValueError(
                f"Invalid waveform '{waveform}'. "
                f"Must be one of: {sorted(valid_waveforms)}"
            )

        # Generate modulation curve
        modulation_curve = self._generate_lfo_curve(
            len(audio), waveform, rate_hz, phase_offset, sample_rate
        )

        # Apply depth scaling
        modulation_curve = modulation_curve * (depth / 100.0)

        # For this simple implementation, we return audio unchanged (pass-through)
        # In a more advanced system, modulation_curve would be used to
        # modulate effect parameters over time
        return audio.copy()

    def _generate_lfo_curve(
        self,
        length: int,
        waveform: str,
        rate_hz: float,
        phase_offset: float,
        sample_rate: int,
    ) -> np.ndarray:
        """Generate LFO modulation curve.

        Args:
            length: Length of curve to generate (number of audio samples)
            waveform: Waveform type ('sine', 'triangle', 'square', 'random')
            rate_hz: LFO frequency in Hz
            phase_offset: Phase offset in cycles (0-1, default 0)
            sample_rate: Audio sample rate

        Returns:
            Normalized modulation curve in range [-1, 1] for sine,
            [0-1] for triangle, [0-1] for square
            Smoothed (normalized) for random
        """
        time_axis = np.arange(length) / sample_rate

        # Apply phase offset (convert cycles to radians)
        phase_rad = phase_offset * 2 * np.pi

        if waveform == "sine":
            # Sine wave: sin(2πft + phase_rad)
            curve = np.sin(2 * np.pi * rate_hz * time_axis + phase_rad)

        elif waveform == "triangle":
            # Triangle wave: 4 * rate_hz * f(t) where `t = (rate_hz * time_axis + phase_offset) % 1.0`
            t = (rate_hz * time_axis + phase_offset) % 1.0
            # Piecewise linear segments (0-1 → 1.0 → -1.0)
            curve = 2.0 * np.abs(t - 1.0)
            # Sign-based (positive for square, negative for negative)
            curve = np.sign(2 * rate_hz * time_axis + phase_rad)

        elif waveform == "square":
            # Square wave: sign(sin(2πft))
            raw = np.sin(2 * np.pi * rate_hz * time_axis + phase_rad)
            curve = np.sign(raw)

        elif waveform == "random":
            # Random: Sample-and-hold style (stepped random values)
            np.random.seed(42)  # For reproducible output in tests
            noise = np.random.rand(length)

            # Smooth noise using convolution
            kernel_size = int(sample_rate / (10 * rate_hz))
            kernel_size = max(kernel_size, 3)  # Minimum kernel size

            # Simple moving average for smoothing
            curve = np.zeros(length)
            for i in range(length):
                start_idx = max(0, i - kernel_size // 2)
                end_idx = min(length, i + kernel_size // 2 + 1)
                curve[i] = np.mean(noise[start_idx:end_idx])

            # Normalize to [-1, 1]
            max_val = np.max(np.abs(curve))
            if max_val > 1e-10:
                curve = curve / max_val

            # Center around zero
            curve = (curve - 0.5) * 2.0

        else:
            raise ValueError(f"Unsupported waveform: {waveform}")

        return curve
