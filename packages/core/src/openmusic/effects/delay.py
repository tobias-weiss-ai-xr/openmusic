"""Multi-tap delay effect for OpenMusic.

Implements multiple delay taps with independent timing, feedback, and panning.
"""

from typing import Any, Dict, List

import numpy as np

from .base import Effect


class MultiTapDelay(Effect):
    """Multi-tap delay effect with independent tap controls.

    Creates multiple delayed copies of the input signal, each with its own
    delay time, feedback amount, and panning. Master feedback controls
    overall regeneration.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the MultiTapDelay effect."""
        self.name = "multi_tap_delay"
        self._buffers: Dict[int, np.ndarray] = {}

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with multi-tap delay.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - num_taps: Number of delay taps (default 4)
                   - tap_times_ms: List of delay times in milliseconds
                   - tap_feedback: List of feedback amounts per tap (0-1)
                   - tap_pan: List of pan values per tap (-1 to 1)
                   - master_feedback: Overall feedback amount (0-1, default 0.3)
                   - wet_dry: Wet/dry mix (0-100, default 50)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters
        num_taps = int(params.get("num_taps", 4))
        tap_times_ms = params.get("tap_times_ms", [250, 375, 500, 625])
        tap_feedback = params.get("tap_feedback", [0.3, 0.25, 0.2, 0.15])
        tap_pan = params.get("tap_pan", [0.0, -0.5, 0.5, 0.0])
        master_feedback = float(params.get("master_feedback", 0.3))
        wet_dry = float(params.get("wet_dry", 50))
        sample_rate = int(params.get("sample_rate", 48000))
        feedback_filter_enabled = bool(params.get("feedback_filter_enabled", False))
        feedback_filter_freq = float(params.get("feedback_filter_freq", 450.0))
        feedback_filter_q = float(params.get("feedback_filter_q", 2.0))

        # Ensure lists are correct length
        while len(tap_times_ms) < num_taps:
            tap_times_ms.append(tap_times_ms[-1] if tap_times_ms else 250)
        while len(tap_feedback) < num_taps:
            tap_feedback.append(tap_feedback[-1] if tap_feedback else 0.3)
        while len(tap_pan) < num_taps:
            tap_pan.append(tap_pan[-1] if tap_pan else 0.0)

        # Convert delay times to samples
        tap_times_samples = [int(t / 1000.0 * sample_rate) for t in tap_times_ms]

        # Determine audio format
        is_stereo = len(audio.shape) > 1 and audio.shape[1] == 2

        if is_stereo:
            output = np.zeros_like(audio)
            left = audio[:, 0].copy()
            right = audio[:, 1].copy()
        else:
            output = np.zeros_like(audio)
            left = audio.copy()
            right = audio.copy()

        # Process each tap
        for tap_idx in range(num_taps):
            delay_samples = tap_times_samples[tap_idx]
            feedback = float(tap_feedback[tap_idx]) * master_feedback
            pan = float(tap_pan[tap_idx])

            # Create delayed signal with feedback
            # For offline processing with feedback:
            # delayed[i] = input[i - delay] + feedback * delayed[i - delay]
            # This creates a recursive delay line (echo repeats)
            delayed = np.zeros_like(left)

            if delay_samples == 0:
                # No delay - just pass through with feedback
                delayed = left * (1 / (1 - feedback)) if feedback < 1 else left.copy()
            else:
                # Copy input with delay
                if delay_samples < len(left):
                    delayed[delay_samples:] = left[:-delay_samples]

                # Add recursive feedback: each sample adds feedback from (delay_samples) earlier
                # This creates the echo repeats: impulse -> delay -> feedback -> delay -> feedback...
                if feedback > 0:
                    for i in range(delay_samples, len(left)):
                        delayed[i] += delayed[i - delay_samples] * feedback

                    # Apply bandpass filter to feedback signal (Basic Channel "filtered echo")
                    if feedback_filter_enabled:
                        w0 = 2 * np.pi * feedback_filter_freq / sample_rate
                        alpha = np.sin(w0) / (2 * feedback_filter_q)
                        b0 = alpha
                        b1 = 0.0
                        b2 = -alpha
                        a0 = 1.0 + alpha
                        a1 = -2.0 * np.cos(w0)
                        a2 = 1.0 - alpha
                        b0 /= a0
                        b1 /= a0
                        b2 /= a0
                        a1 /= a0
                        a2 /= a0
                        filtered = np.zeros_like(delayed)
                        for i in range(2, len(delayed)):
                            filtered[i] = (
                                b0 * delayed[i]
                                + b1 * delayed[i - 1]
                                + b2 * delayed[i - 2]
                                - a1 * filtered[i - 1]
                                - a2 * filtered[i - 2]
                            )
                        delayed = filtered

            # Apply pan
            pan_factor_left = np.sqrt(0.5 * (1 - pan))
            pan_factor_right = np.sqrt(0.5 * (1 + pan))

            left += delayed * pan_factor_left
            right += delayed * pan_factor_right

        # Combine dry and wet
        wet_ratio = wet_dry / 100.0

        if is_stereo:
            output[:, 0] = audio[:, 0] * (1 - wet_ratio) + left * wet_ratio
            output[:, 1] = audio[:, 1] * (1 - wet_ratio) + right * wet_ratio
        else:
            output = audio * (1 - wet_ratio) + left * wet_ratio

        return output
