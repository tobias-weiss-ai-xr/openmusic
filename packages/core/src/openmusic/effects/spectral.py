"""Spectral gate effect for OpenMusic.

Implements an adaptive spectral gate that removes noise floor and creates
rhythmic gating effects using FFT-based analysis with per-bin thresholding,
attack/release smoothing, and optional tempo-synced modulation.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import Effect


class SpectralGate(Effect):
    """Spectral gate for noise reduction and rhythmic gating.

    Processes audio in overlapping FFT frames, applying gain reduction
    to frequency bins whose magnitude falls below a configurable threshold.
    Supports independent frequency bands with per-band thresholds,
    attack/release/hold smoothing, and optional tempo-synced gating.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the SpectralGate effect."""
        self.name = "spectral_gate"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with spectral gating.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - threshold: Gate threshold in dB (-60 to 0, default -40)
                   - attack_ms: Attack time in ms (default 10)
                   - release_ms: Release time in ms (default 100)
                   - hold_ms: Hold time in ms after signal drops below threshold
                               (default 20)
                   - sync_to_tempo: If True, modulate gate with rhythmic pattern
                                    based on bpm (default False)
                   - bpm: Beats per minute for tempo sync (default 125)
                   - gate_pattern: List of 0-1 values for tempo-synced gate
                                   (default [1, 0, 1, 0] for quarter-note pattern)
                   - frequency_bands: List of dicts with 'min_freq', 'max_freq',
                                      'threshold_db' for per-band gating
                   - window_size: FFT window size in samples (default 2048)
                   - hop_size: Hop size in samples (default 512)
                   - sample_rate: Audio sample rate (default 48000)

        Returns:
            Processed audio with same shape as input.
        """
        threshold_db = float(params.get("threshold", -40))
        attack_ms = float(params.get("attack_ms", 10))
        release_ms = float(params.get("release_ms", 100))
        hold_ms = float(params.get("hold_ms", 20))
        sync_to_tempo = bool(params.get("sync_to_tempo", False))
        bpm = float(params.get("bpm", 125))
        gate_pattern = params.get("gate_pattern", [1, 0, 1, 0])
        frequency_bands: List[Dict[str, Any]] = params.get("frequency_bands", [])
        window_size = int(params.get("window_size", 2048))
        hop_size = int(params.get("hop_size", 512))
        sample_rate = int(params.get("sample_rate", 48000))

        threshold_db = np.clip(threshold_db, -60, 0)

        is_stereo = len(audio.shape) > 1 and audio.shape[1] == 2

        if is_stereo:
            left = self._process_channel(
                audio[:, 0],
                threshold_db,
                attack_ms,
                release_ms,
                hold_ms,
                sync_to_tempo,
                bpm,
                gate_pattern,
                frequency_bands,
                window_size,
                hop_size,
                sample_rate,
            )
            right = self._process_channel(
                audio[:, 1],
                threshold_db,
                attack_ms,
                release_ms,
                hold_ms,
                sync_to_tempo,
                bpm,
                gate_pattern,
                frequency_bands,
                window_size,
                hop_size,
                sample_rate,
            )
            return np.column_stack([left, right])
        else:
            return self._process_channel(
                audio,
                threshold_db,
                attack_ms,
                release_ms,
                hold_ms,
                sync_to_tempo,
                bpm,
                gate_pattern,
                frequency_bands,
                window_size,
                hop_size,
                sample_rate,
            )

    def _process_channel(
        self,
        audio: np.ndarray,
        threshold_db: float,
        attack_ms: float,
        release_ms: float,
        hold_ms: float,
        sync_to_tempo: bool,
        bpm: float,
        gate_pattern: List[float],
        frequency_bands: List[Dict[str, Any]],
        window_size: int,
        hop_size: int,
        sample_rate: int,
    ) -> np.ndarray:
        n_samples = len(audio)

        if n_samples == 0:
            return audio.copy()

        window = np.hanning(window_size)

        n_frames = max(1, (n_samples - window_size + hop_size - 1) // hop_size + 1)
        padded_length = (n_frames - 1) * hop_size + window_size
        pad_amount = padded_length - n_samples
        if pad_amount > 0:
            audio_padded = np.pad(audio, (0, pad_amount), mode="reflect")
        else:
            audio_padded = audio.copy()

        freqs = np.fft.rfftfreq(window_size, d=1.0 / sample_rate)
        n_bins = len(freqs)

        use_bands = len(frequency_bands) > 0
        if use_bands:
            band_masks: List[Tuple[np.ndarray, float]] = []
            for band in frequency_bands:
                min_f = float(band.get("min_freq", 20))
                max_f = float(band.get("max_freq", 20000))
                band_thresh = float(band.get("threshold_db", threshold_db))
                mask = (freqs >= min_f) & (freqs <= max_f)
                if np.any(mask):
                    band_masks.append((mask, band_thresh))

        hold_samples = int(hold_ms / 1000.0 * sample_rate / hop_size)
        current_gate = np.ones(n_bins)
        hold_counter = 0

        if sync_to_tempo and len(gate_pattern) > 0:
            beats_per_second = bpm / 60.0
            beat_samples = int(sample_rate / beats_per_second)
            pattern_frames = len(gate_pattern)
            pattern_len_frames = int(beat_samples * pattern_frames / hop_size)
            tempo_envelope = np.zeros(pattern_len_frames)
            for i in range(pattern_len_frames):
                beat_pos = (i * hop_size) / beat_samples
                pattern_idx = int(beat_pos) % pattern_frames
                tempo_envelope[i] = gate_pattern[pattern_idx]
        else:
            tempo_envelope = None

        attack_coeff = np.exp(-1.0 / (attack_ms / 1000.0 * sample_rate / hop_size))
        release_coeff = np.exp(-1.0 / (release_ms / 1000.0 * sample_rate / hop_size))

        output = np.zeros(padded_length)

        for frame_idx in range(n_frames):
            start = frame_idx * hop_size
            frame = audio_padded[start : start + window_size] * window

            spectrum = np.fft.rfft(frame)
            magnitude = np.abs(spectrum)

            if use_bands:
                gate_values = np.ones(n_bins)
                for mask, band_thresh in band_masks:
                    band_thresh_linear = 10 ** (band_thresh / 20.0)
                    gate_values[mask] = np.where(
                        magnitude[mask] < band_thresh_linear, 0.0, 1.0
                    )
                covered = np.zeros(n_bins, dtype=bool)
                for mask, _ in band_masks:
                    covered |= mask
                global_thresh_linear = 10 ** (threshold_db / 20.0)
                gate_values[~covered] = np.where(
                    magnitude[~covered] < global_thresh_linear, 0.0, 1.0
                )
            else:
                threshold_linear = 10 ** (threshold_db / 20.0)
                gate_values = np.where(magnitude < threshold_linear, 0.0, 1.0)

            if hold_counter > 0:
                gate_values = np.ones(n_bins) * np.min(gate_values)
                hold_counter -= 1
            elif np.all(gate_values < 0.5):
                hold_counter = hold_samples

            for b in range(n_bins):
                if gate_values[b] < current_gate[b]:
                    current_gate[b] = current_gate[b] + (
                        gate_values[b] - current_gate[b]
                    ) * (1 - attack_coeff)
                else:
                    current_gate[b] = current_gate[b] + (
                        gate_values[b] - current_gate[b]
                    ) * (1 - release_coeff)

            if tempo_envelope is not None:
                t_idx = frame_idx % len(tempo_envelope)
                current_gate *= tempo_envelope[t_idx]

            gated_spectrum = spectrum * current_gate
            gated_frame = np.fft.irfft(gated_spectrum, n=window_size)
            gated_frame *= window

            output[start : start + window_size] += gated_frame

        overlap_factor = np.sum(window ** 2) / hop_size
        if overlap_factor > 0:
            output /= overlap_factor

        return output[:n_samples]
