"""Spectral gate and frequency masking avoidance effects for OpenMusic.

Provides:
- SpectralGate: Adaptive spectral gate for noise reduction and rhythmic gating.
- SpectralMaskingAvoidance: Automated frequency carving that detects overlapping
  frequency content and applies subtle EQ cuts to reduce muddy buildup.
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


class SpectralMaskingAvoidance(Effect):
    """Frequency masking avoidance using spectral analysis.

    Detects frequency regions with excessive energy that could mask other
    content and applies subtle, narrow EQ cuts to reduce muddy buildup.
    Uses FFT-based spectral overlap analysis with per-band energy comparison
    to identify masking candidates and attenuate them gracefully.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the SpectralMaskingAvoidance effect."""
        self.name = "spectral_masking_avoidance"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with frequency masking avoidance.

        Analyzes the spectrum in overlapping frames, identifies frequency
        regions with disproportionately high energy (potential maskers),
        and applies gentle attenuation to create a cleaner spectral balance.

        Args:
            audio: Input audio data, mono (N,) or stereo (N, 2).
            params: Dictionary containing:
                   - sensitivity: Detection sensitivity 0-100 (default 50).
                      Higher = more aggressive carving.
                   - max_cut_db: Maximum attenuation in dB 0-24 (default 6).
                   - frequency_range: Dict with 'min_hz' and 'max_hz'
                     defining analysis range (default {min: 20, max: 20000}).
                   - auto_detect: If True, automatically find masking
                     regions based on spectral imbalance (default True).
                   - window_size: FFT window in samples (default 4096).
                   - hop_size: Hop size in samples (default 1024).
                   - sample_rate: Audio sample rate (default 48000).

        Returns:
            Processed audio with same shape as input.
        """
        sensitivity = float(params.get("sensitivity", 50))
        max_cut_db = float(params.get("max_cut_db", 6))
        frequency_range: Dict[str, Any] = params.get(
            "frequency_range", {"min_hz": 20, "max_hz": 20000}
        )
        auto_detect = bool(params.get("auto_detect", True))
        sample_rate = int(params.get("sample_rate", 48000))
        window_size = int(params.get("window_size", 4096))
        hop_size = int(params.get("hop_size", 1024))

        min_hz = float(frequency_range.get("min_hz", 20))
        max_hz = float(frequency_range.get("max_hz", 20000))

        sensitivity = float(np.clip(sensitivity, 0, 100))
        max_cut_db = float(np.clip(max_cut_db, 0, 24))

        is_stereo = len(audio.shape) > 1 and audio.shape[1] == 2

        if is_stereo:
            left = self._process_channel(
                audio[:, 0], sensitivity, max_cut_db,
                min_hz, max_hz, auto_detect,
                window_size, hop_size, sample_rate,
            )
            right = self._process_channel(
                audio[:, 1], sensitivity, max_cut_db,
                min_hz, max_hz, auto_detect,
                window_size, hop_size, sample_rate,
            )
            return np.column_stack([left, right])
        else:
            return self._process_channel(
                audio, sensitivity, max_cut_db,
                min_hz, max_hz, auto_detect,
                window_size, hop_size, sample_rate,
            )

    def _process_channel(
        self,
        audio: np.ndarray,
        sensitivity: float,
        max_cut_db: float,
        min_hz: float,
        max_hz: float,
        auto_detect: bool,
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

        # Build frequency band mask for the analysis range
        band_mask = (freqs >= min_hz) & (freqs <= max_hz)
        band_indices = np.where(band_mask)[0]

        if len(band_indices) == 0:
            return audio.copy()

        # Convert sensitivity to a threshold ratio:
        # sensitivity=0  -> ratio=4.0 (very conservative, only extreme peaks)
        # sensitivity=50 -> ratio=2.0 (moderate)
        # sensitivity=100 -> ratio=1.2 (very aggressive, subtle imbalances trigger cuts)
        threshold_ratio = 4.0 - (sensitivity / 100.0) * 2.8

        # Convert max_cut_db to linear gain reduction
        max_cut_linear = 10 ** (-max_cut_db / 20.0)

        # Smoothing coefficient for frame-to-frame gain changes
        smooth_coeff = 0.3

        output = np.zeros(padded_length)
        current_gains = np.ones(n_bins)

        for frame_idx in range(n_frames):
            start = frame_idx * hop_size
            frame = audio_padded[start: start + window_size] * window

            spectrum = np.fft.rfft(frame)
            magnitude = np.abs(spectrum) + 1e-10

            # Compute per-bin gain reductions
            if auto_detect and len(band_indices) > 5:
                # Divide the spectrum into analysis bands (~1/3 octave)
                # and compute the local masking potential.
                gains = self._compute_masking_gains(
                    magnitude, freqs, band_indices,
                    threshold_ratio, max_cut_linear,
                    n_bins, sample_rate,
                )
            else:
                gains = np.ones(n_bins)

            # Smooth gain changes across frames
            current_gains = (
                smooth_coeff * gains + (1.0 - smooth_coeff) * current_gains
            )
            current_gains = np.clip(current_gains, max_cut_linear, 1.0)

            # Apply attenuation in frequency domain
            processed_spec = spectrum * current_gains
            processed_frame = np.fft.irfft(processed_spec, n=window_size)
            processed_frame *= window

            output[start: start + window_size] += processed_frame

        overlap_factor = np.sum(window ** 2) / hop_size
        if overlap_factor > 0:
            output /= overlap_factor

        return output[:n_samples]

    def _compute_masking_gains(
        self,
        magnitude: np.ndarray,
        freqs: np.ndarray,
        band_indices: np.ndarray,
        threshold_ratio: float,
        max_cut_linear: float,
        n_bins: int,
        sample_rate: int,
    ) -> np.ndarray:
        gains = np.ones(n_bins)

        if len(band_indices) < 6:
            return gains

        # Group bins into ~1/6-octave bands for perceptual relevance.
        # Use logarithmic spacing: ~1/6 octave = 2^(1/6) factor boundaries.
        octave_factor = 2.0 ** (1.0 / 6.0)
        band_edges = [band_indices[0]]
        i = 0
        while i < len(band_indices):
            current_freq = freqs[band_indices[i]]
            target_freq = current_freq * octave_factor
            while i < len(band_indices) and freqs[band_indices[i]] < target_freq:
                i += 1
            if i < len(band_indices):
                band_edges.append(band_indices[i])

        if len(band_edges) < 3:
            return gains

        # Compute energy per band
        band_energies = []
        for j in range(len(band_edges) - 1):
            lo = int(band_edges[j])
            hi = int(band_edges[j + 1])
            energy = float(np.mean(magnitude[lo:hi] ** 2))
            band_energies.append(energy)

        # For each band, compute the masking ratio against neighboring bands.
        # A band is flagged as a masker if its energy exceeds the average
        # of its neighbors by the threshold_ratio.
        for j in range(len(band_energies)):
            lo_bin = int(band_edges[j])
            hi_bin = int(band_edges[j + 1])

            neighbor_energies = []
            if j > 0:
                neighbor_energies.append(band_energies[j - 1])
            if j > 1:
                neighbor_energies.append(band_energies[j - 2])
            if j < len(band_energies) - 1:
                neighbor_energies.append(band_energies[j + 1])
            if j < len(band_energies) - 2:
                neighbor_energies.append(band_energies[j + 2])

            if not neighbor_energies:
                continue

            avg_neighbor = float(np.mean(neighbor_energies))
            band_energy = band_energies[j]

            if avg_neighbor > 0 and band_energy > avg_neighbor * threshold_ratio:
                # Compute attenuation: stronger for higher excess ratios
                excess_ratio = band_energy / avg_neighbor
                # Map excess ratio to gain reduction: more excess = more cut
                attenuation = min(
                    max_cut_linear,
                    max_cut_linear
                    + (1.0 - max_cut_linear)
                    * (1.0 - (threshold_ratio / max(excess_ratio, 1e-6))),
                )
                gains[lo_bin:hi_bin] = attenuation

        return gains
