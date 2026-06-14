"""Native Python DSP bridge using Spotify Pedalboard."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from openmusic.effects.pedalboard_chain import PedalboardEffectsChain, PRESETS

# Lazy import scipy.signal (optional dependency for IIR filters)
try:
    import scipy.signal  # noqa: F401

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


class PythonDSPBridge:
    """Process audio segments using Pedalboard (native Python, no Node.js).

    Applies effects in canonical dub techno order:
    Source -> HPF -> TapeSaturation -> Pedalboard chain (Filter/Delay/Reverb/Chorus)
    -> SidechainCompression -> MidSideStereoWidener + MonoSubBass -> Mastering
    """

    def __init__(
        self,
        preset: str = "deep_dub",
        apply_mastering: bool = True,
        target_lufs: float = -16.0,
        sidechain_enabled: bool = True,
        ms_enabled: bool = True,
    ):
        self.preset_name = preset
        self.apply_mastering = apply_mastering
        self.target_lufs = target_lufs
        self.sidechain_enabled = sidechain_enabled
        self.ms_enabled = ms_enabled

    def is_available(self) -> bool:
        try:
            import pedalboard  # noqa: F401

            return True
        except ImportError:
            return False

    def _apply_hpf(self, audio: np.ndarray, sample_rate: float) -> np.ndarray:
        """Highpass at 30Hz using scipy Butterworth or DC-blocking fallback."""
        if HAS_SCIPY:
            from scipy import signal

            sos = signal.butter(4, 30, "highpass", fs=sample_rate, output="sos")
            if audio.ndim == 1:
                audio = signal.sosfilt(sos, audio)
            else:
                for ch in range(audio.shape[1]):
                    audio[:, ch] = signal.sosfilt(sos, audio[:, ch])
        else:
            # Simple DC-blocking filter fallback
            alpha = 0.9997
            if audio.ndim == 1:
                audio = np.column_stack([audio, audio])
            for ch in range(audio.shape[1]):
                x = audio[:, ch]
                y = np.zeros_like(x)
                for i in range(1, len(x)):
                    y[i] = x[i] - x[i - 1] + alpha * y[i - 1]
                audio[:, ch] = y
        return audio

    def _mono_sub_bass(self, audio: np.ndarray, sample_rate: float) -> np.ndarray:
        """Collapse frequencies below 150Hz to mono (club compatibility)."""
        if audio.ndim < 2 or audio.shape[1] < 2:
            return audio
        if HAS_SCIPY:
            from scipy import signal

            sos = signal.butter(4, 150, "lowpass", fs=sample_rate, output="sos")
            sub_l = signal.sosfilt(sos, audio[:, 0])
            sub_r = signal.sosfilt(sos, audio[:, 1])
            sub_mono = (sub_l + sub_r) / 2
            result = audio.copy()
            result[:, 0] = result[:, 0] - sub_l + sub_mono
            result[:, 1] = result[:, 1] - sub_r + sub_mono
        else:
            # Simple moving-average lowpass fallback
            window = max(1, int(sample_rate / 300))
            if window > 1:
                kernel = np.ones(window) / window
                sub_l = np.convolve(audio[:, 0], kernel, mode="same")
                sub_r = np.convolve(audio[:, 1], kernel, mode="same")
                sub_mono = (sub_l + sub_r) / 2
                result = audio.copy()
                result[:, 0] = result[:, 0] - sub_l + sub_mono
                result[:, 1] = result[:, 1] - sub_r + sub_mono
            else:
                result = audio.copy()
        return result

    def process(self, input_path: str, output_path: str) -> str:
        """Process a WAV file through the full DSP pipeline.

        Order: HPF -> TapeSaturation -> Pedalboard chain ->
               SidechainCompression -> MidSide/Stereo -> Mastering

        Args:
            input_path: Path to input WAV file.
            output_path: Path to write processed WAV file.

        Returns:
            The output_path on success.

        Raises:
            ImportError: If pedalboard is not installed.
            ValueError: If preset is unknown.
            FileNotFoundError: If input file doesn't exist.
        """
        if not Path(input_path).exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Build effects chain
        chain = PedalboardEffectsChain(self.preset_name)

        # Read input audio
        audio, sample_rate = sf.read(input_path)

        # Ensure 2D (stereo)
        if audio.ndim == 1:
            audio = np.column_stack([audio, audio])

        logger.info(
            f"Processing {input_path} with preset '{self.preset_name}' "
            f"({len(audio)} samples at {sample_rate}Hz)"
        )

        # --- Stage A: Pre-processing (HPF + tape saturation) ---
        audio = self._apply_hpf(audio, sample_rate)

        from openmusic.effects.saturation import TapeSaturation

        sat = TapeSaturation()
        audio = sat.process(audio, {"drive": 20, "wet_dry_mix": 30})

        # --- Stage B: Pedalboard chain ---
        assert chain.board is not None, "Pedalboard board should be initialized"
        processed = chain.board(audio, sample_rate)

        # --- Stage C: Sidechain compression ---
        if self.sidechain_enabled:
            from openmusic.effects.compression import SidechainCompression

            sc = SidechainCompression()
            processed = sc.process(
                processed,
                {
                    "threshold_db": -24,
                    "ratio": 4.0,
                    "attack_ms": 10,
                    "release_ms": 300,
                    "knee_db": 3,
                    "wet_dry_mix": 80,
                    "sample_rate": sample_rate,
                },
            )

        # --- Stage D: Mid-side processing + mono sub-bass ---
        if self.ms_enabled:
            from openmusic.effects.stereo import MidSideStereoWidener

            ms = MidSideStereoWidener()
            processed = ms.process(
                processed,
                {"stereo_width": 1.0, "sample_rate": sample_rate},
            )

            # Mono sub-bass below 150Hz (club compatibility)
            processed = self._mono_sub_bass(processed, sample_rate)

        # --- Stage E: Mastering ---
        if self.apply_mastering:
            from openmusic.effects.mastering import MasteringChain

            mastering = MasteringChain(target_lufs=self.target_lufs)
            processed = mastering.process(processed, sample_rate)

        # Write output
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, processed, sample_rate, format="WAV")
        logger.info(f"Processed audio written to {output_path}")

        return output_path
