"""Mastering chain for final output processing."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    from pedalboard import Pedalboard, Compressor, Gain, LowShelfFilter, HighShelfFilter

    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False


class MasteringChain:
    """Final mastering processing: multiband-style comp, EQ, loudness."""

    def __init__(
        self,
        target_lufs: float = -16.0,
        compressor_threshold_db: float = -20.0,
        compressor_ratio: float = 3.0,
        bass_gain_db: float = 2.0,
        treble_gain_db: float = -1.0,
    ):
        if not HAS_PEDALBOARD:
            raise ImportError("pedalboard is required for mastering")
        self.target_lufs = target_lufs
        self.compressor_threshold_db = compressor_threshold_db
        self.compressor_ratio = compressor_ratio
        self.bass_gain_db = bass_gain_db
        self.treble_gain_db = treble_gain_db
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

        # Simple LUFS-style normalization (RMS-based approximation)
        rms = np.sqrt(np.mean(processed**2))
        if rms > 0:
            # -16 LUFS ≈ -16 dBFS for tonal content
            target_rms = 10 ** (self.target_lufs / 20.0)
            gain = target_rms / rms
            # Limit gain to avoid extreme boosting of quiet content
            gain = min(gain, 6.0)
            processed = processed * gain

        return processed
