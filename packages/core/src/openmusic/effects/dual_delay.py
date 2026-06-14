"""Dual delay with pitch detune for dub techno width."""
from typing import Any, Dict

import numpy as np

from .base import Effect


class DualDelay(Effect):
    """Parallel dual delay with pitch detune.

    Two delays: one at dotted-8th (75% of quarter), one at quarter note.
    Each is hard-panned opposite and slightly pitch-detuned (±X cents).
    Creates the wide, spatial echo signature of dub techno.
    """

    def __init__(self):
        self.name = "dual_delay"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        delay1_ms = float(params.get("delay1_ms", 375))  # Dotted 8th at 125 BPM
        delay2_ms = float(params.get("delay2_ms", 500))  # Quarter note
        feedback1 = float(params.get("feedback1", 0.4))
        feedback2 = float(params.get("feedback2", 0.3))
        mix = float(params.get("mix", 0.5))
        detune_cents = float(params.get("detune_cents", 3.0))
        sample_rate = int(params.get("sample_rate", 48000))

        is_stereo = len(audio.shape) > 1 and audio.shape[1] == 2

        if is_stereo:
            left = audio[:, 0].copy()
            right = audio[:, 1].copy()
        else:
            left = audio.copy()
            right = audio.copy()

        def _delay_line(
            signal: np.ndarray, delay_ms: float, fb: float, detune: float
        ) -> np.ndarray:
            delay_samples = int(delay_ms / 1000.0 * sample_rate)
            out = np.zeros_like(signal)
            if delay_samples >= len(signal):
                return out
            out[delay_samples:] = signal[:-delay_samples]
            if fb > 0:
                for i in range(delay_samples, len(signal)):
                    out[i] += out[i - delay_samples] * fb
            # Simple pitch detune via linear interpolation (resampling)
            if abs(detune) > 0.01:
                ratio = 2 ** (detune / 1200.0)
                orig_indices = np.arange(len(out))
                new_indices = orig_indices * ratio
                new_indices = np.clip(new_indices, 0, len(out) - 1)
                idx_floor = np.floor(new_indices).astype(int)
                idx_ceil = np.minimum(idx_floor + 1, len(out) - 1)
                frac = new_indices - idx_floor
                out = out[idx_floor] * (1 - frac) + out[idx_ceil] * frac
            return out

        # Tap 1: panned left, -detune
        tap1_left = _delay_line(left, delay1_ms, feedback1, -detune_cents)
        tap1_right = _delay_line(right, delay1_ms, feedback1, -detune_cents) * 0.3

        # Tap 2: panned right, +detune
        tap2_left = _delay_line(left, delay2_ms, feedback2, detune_cents) * 0.3
        tap2_right = _delay_line(right, delay2_ms, feedback2, detune_cents)

        # Mix
        wet = np.zeros_like(audio)
        if is_stereo:
            wet[:, 0] = tap1_left * 0.707 + tap2_left * 0.707
            wet[:, 1] = tap1_right * 0.707 + tap2_right * 0.707
        else:
            wet = tap1_left * 0.5 + tap2_right * 0.5

        return audio * (1 - mix) + wet * mix
