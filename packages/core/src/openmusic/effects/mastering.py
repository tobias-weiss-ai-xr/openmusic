"""Mastering chain for final output processing."""

from __future__ import annotations

import logging

import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)

try:
    from pedalboard import Pedalboard, Compressor, Gain, LowShelfFilter, HighShelfFilter

    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class Limiter:
    """Simple brickwall limiter with envelope follower."""

    def __init__(
        self,
        threshold_db: float = -1.0,
        release_ms: float = 100.0,
        sample_rate: int = 48000,
    ):
        self.threshold_linear = 10 ** (threshold_db / 20.0)
        self.release_coeff = np.exp(-1.0 / (release_ms / 1000.0 * sample_rate))
        self.envelope = 0.0

    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply brickwall limiting to audio array."""
        was_1d = audio.ndim == 1
        needs_transpose = audio.ndim == 2 and audio.shape[1] == 2
        if was_1d:
            audio = audio[np.newaxis, :]  # (N,) → (1, N)
        elif needs_transpose:
            audio = audio.T  # (N, 2) → (2, N)
        output = np.zeros_like(audio)
        for ch in range(audio.shape[0]):
            self.envelope = 0.0
            for i in range(audio.shape[1]):
                abs_val = abs(audio[ch, i])
                if abs_val > self.envelope:
                    self.envelope = abs_val
                else:
                    self.envelope += (abs_val - self.envelope) * self.release_coeff
                if self.envelope > self.threshold_linear:
                    gain = self.threshold_linear / self.envelope
                    output[ch, i] = audio[ch, i] * gain
                else:
                    output[ch, i] = audio[ch, i]
        if was_1d:
            return output[0]
        if needs_transpose:
            return output.T  # (2, N) → (N, 2)
        return output


class MasteringChain:
    """Final mastering processing: multiband-style comp, EQ, loudness."""

    def __init__(
        self,
        target_lufs: float = -16.0,
        compressor_threshold_db: float = -20.0,
        compressor_ratio: float = 3.0,
        bass_gain_db: float = 2.0,
        treble_gain_db: float = -1.0,
        limiter_threshold_db: float = -1.0,
        limiter_enabled: bool = True,
    ):
        if not HAS_PEDALBOARD:
            raise ImportError("pedalboard is required for mastering")
        self.target_lufs = target_lufs
        self.compressor_threshold_db = compressor_threshold_db
        self.compressor_ratio = compressor_ratio
        self.bass_gain_db = bass_gain_db
        self.treble_gain_db = treble_gain_db
        self.limiter_threshold_db = limiter_threshold_db
        self.limiter_enabled = limiter_enabled
        self.board = self._build()

    def _build(self) -> "Pedalboard":
        return Pedalboard(
            [
                LowShelfFilter(cutoff_frequency_hz=120.0, gain_db=self.bass_gain_db),
                Compressor(
                    threshold_db=self.compressor_threshold_db,
                    ratio=self.compressor_ratio,
                ),
                HighShelfFilter(
                    cutoff_frequency_hz=8000.0, gain_db=self.treble_gain_db
                ),
            ]
        )

    def process(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply mastering chain to audio array."""
        processed = self.board(audio, sample_rate)

        # Improved LUFS approximation (ITU-R BS.1770-4 style)
        # Pre-filter: apply Leq(RLB) highpass at ~38Hz
        sos = signal.butter(4, 38, "highpass", fs=sample_rate, output="sos")
        if processed.ndim == 1:
            filtered = signal.sosfilt(sos, processed)
        else:
            filtered = np.zeros_like(processed)
            for ch in range(
                processed.shape[-1] if processed.ndim > 1 else 1
            ):
                filtered[..., ch] = signal.sosfilt(sos, processed[..., ch])

        # Mean square per channel with gating at -70dB
        if filtered.ndim == 1:
            mean_sq = np.mean(filtered**2)
            gate_threshold = 10 ** (-70 / 20.0)
            above_gate = np.abs(filtered) > gate_threshold
            if np.any(above_gate):
                mean_sq = np.mean(filtered[above_gate] ** 2)
        else:
            ch_powers = []
            for ch in range(filtered.shape[-1]):
                ch_data = filtered[..., ch]
                gate_threshold = 10 ** (-70 / 20.0)
                above_gate = np.abs(ch_data) > gate_threshold
                if np.any(above_gate):
                    ch_powers.append(np.mean(ch_data[above_gate] ** 2))
                else:
                    ch_powers.append(np.mean(ch_data**2))
            if len(ch_powers) >= 2:
                mean_sq = ch_powers[0] + 10 ** (-1.5 / 10) * ch_powers[1]
            else:
                mean_sq = ch_powers[0]

        # LUFS = -0.691 + 10*log10(mean_sq)
        lufs = -0.691 + 10 * np.log10(max(mean_sq, 1e-20))

        # Apply gain to reach target LUFS
        gain_db = self.target_lufs - lufs
        gain_db = min(gain_db, 6.0)
        processed = processed * (10 ** (gain_db / 20.0))

        # Apply brickwall limiter
        if self.limiter_enabled:
            limiter = Limiter(
                threshold_db=self.limiter_threshold_db, sample_rate=sample_rate
            )
            processed = limiter.process(processed)

        return processed
