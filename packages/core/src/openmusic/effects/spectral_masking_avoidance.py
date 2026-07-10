"""Frequency masking avoidance effect for OpenMusic.

Implements an automated frequency carving system that detects overlapping
frequency content between layers of audio and applies subtle EQ cuts to
reduce masking. Uses FFT analysis to identify spectral conflicts and
applies narrow-band gain reduction at conflict frequencies.

The effect processes audio by:
1. Analyzing the spectrum to identify dominant frequency regions
2. Detecting conflicts where multiple layers occupy the same spectral space
3. Applying narrow notch/peak EQ cuts at conflict frequencies to carve space
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base import Effect


class FrequencyMaskingAvoidance(Effect):
    """Frequency masking avoidance for automated spectral carving.

    Detects overlapping frequency content and applies subtle EQ cuts
    to reduce masking between audio layers. Uses FFT analysis per frame
    to identify dominant peaks and apply targeted notch filtering.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the FrequencyMaskingAvoidance effect."""
        self.name = "frequency_masking_avoidance"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply frequency masking avoidance to audio.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - sensitivity: Detection sensitivity (0-100, default 50).
                                 Higher values detect more conflicts.
                   - max_cut_db: Maximum gain reduction in dB (0-24, default 6).
                   - frequency_range: Tuple of (min_hz, max_hz) for detection
                     range (default (20, 20000)).
                   - auto_detect: If True, automatically detect conflict
                     frequencies (default True).
                   - conflict_frequencies: Manual list of center frequencies
                     to cut when auto_detect is False (default []).
                   - bandwidth: Bandwidth of each EQ cut in Hz (default 50).
                   - window_size: FFT window size in samples (default 2048).
                   - hop_size: Hop size in samples (default 512).
                   - sample_rate: Audio sample rate (default 48000).
                   - num_peaks: Number of dominant peaks to detect per frame
                     (default 3).

        Returns:
            Processed audio with same shape as input.
        """
        sensitivity = float(params.get("sensitivity", 50))
        max_cut_db = float(params.get("max_cut_db", 6))
        frequency_range = params.get("frequency_range", (20, 20000))
        auto_detect = bool(params.get("auto_detect", True))
        conflict_frequencies: List[float] = params.get("conflict_frequencies", [])
        bandwidth = float(params.get("bandwidth", 50))
        window_size = int(params.get("window_size", 2048))
        hop_size = int(params.get("hop_size", 512))
        sample_rate = int(params.get("sample_rate", 48000))
        num_peaks = int(params.get("num_peaks", 3))

        # Clamp parameters
        sensitivity = np.clip(sensitivity, 0, 100)
        max_cut_db = np.clip(max_cut_db, 0, 24)
        bandwidth = max(bandwidth, 10)
        num_peaks = max(1, min(num_peaks, 20))
        conflict_frequencies = [f for f in conflict_frequencies if 0 < f < sample_rate / 2]

        # Determine audio shape
        is_stereo = audio.ndim == 2 and audio.shape[1] == 2
        if audio.ndim > 1 and not is_stereo:
            audio = audio.T if audio.shape[0] == 2 else audio
            is_stereo = audio.ndim == 2 and audio.shape[1] == 2

        if is_stereo:
            left = self._process_channel(
                np.ascontiguousarray(audio[:, 0]),
                sensitivity, max_cut_db, frequency_range,
                auto_detect, conflict_frequencies, bandwidth,
                window_size, hop_size, sample_rate, num_peaks,
            )
            right = self._process_channel(
                np.ascontiguousarray(audio[:, 1]),
                sensitivity, max_cut_db, frequency_range,
                auto_detect, conflict_frequencies, bandwidth,
                window_size, hop_size, sample_rate, num_peaks,
            )
            return np.column_stack([left, right])
        else:
            return self._process_channel(
                audio, sensitivity, max_cut_db, frequency_range,
                auto_detect, conflict_frequencies, bandwidth,
                window_size, hop_size, sample_rate, num_peaks,
            )

    def _process_channel(
        self,
        audio: np.ndarray,
        sensitivity: float,
        max_cut_db: float,
        frequency_range: Any,
        auto_detect: bool,
        conflict_frequencies: List[float],
        bandwidth: float,
        window_size: int,
        hop_size: int,
        sample_rate: int,
        num_peaks: int,
    ) -> np.ndarray:
        n_samples = len(audio)

        if n_samples == 0:
            return audio.copy()

        freq_min, freq_max = frequency_range
        freq_min = max(float(freq_min), 20)
        freq_max = min(float(freq_max), sample_rate / 2 - 1)

        # Build frequency axis once
        window = np.hanning(window_size)
        freqs = np.fft.rfftfreq(window_size, d=1.0 / sample_rate)
        n_bins = len(freqs)

        # Build filter bank: for each conflict frequency, create a notch filter
        filter_freqs: List[float]
        if auto_detect:
            # We'll detect per frame using the conflict frequencies as initial seeds
            # and look for dominant peaks near them
            if not conflict_frequencies:
                filter_freqs = []
            else:
                filter_freqs = list(conflict_frequencies)
        else:
            filter_freqs = list(conflict_frequencies)

        # If no frequencies specified, use default octave-band centers
        if not filter_freqs and not auto_detect:
            filter_freqs = self._default_center_frequencies(freq_min, freq_max)

        # Pre-compute filter masks for static notch frequencies
        static_filter_masks: List[Tuple[np.ndarray, float]] = []
        for f_center in filter_freqs:
            if f_center < sample_rate / 2:
                mask = self._notch_filter_mask(freqs, f_center, bandwidth)
                if np.any(mask > 0):
                    static_filter_masks.append((mask, f_center))

        n_frames = max(1, (n_samples - window_size + hop_size - 1) // hop_size + 1)
        padded_length = (n_frames - 1) * hop_size + window_size
        pad_amount = padded_length - n_samples
        if pad_amount > 0:
            audio_padded = np.pad(audio, (0, pad_amount), mode="reflect")
        else:
            audio_padded = audio.copy()

        output = np.zeros(padded_length)

        # Sensitivity factor: maps 0-100 to 0.0-1.0 cut intensity
        sensitivity_factor = sensitivity / 100.0
        max_cut_linear = 10 ** (-max_cut_db / 20.0)  # Convert cut to linear gain
        # Scale between full cut (at 100% sensitivity) and no cut (at 0%)
        cut_gain = 1.0 - sensitivity_factor * (1.0 - max_cut_linear)

        # Early return when no cut is applied
        if abs(cut_gain - 1.0) < 1e-9:
            return audio.copy()

        for frame_idx in range(n_frames):
            start = frame_idx * hop_size
            frame = audio_padded[start : start + window_size]
            frame_windowed = frame * window

            spectrum = np.fft.rfft(frame_windowed)
            magnitude_db = 20 * np.log10(np.abs(spectrum) + 1e-10)

            # Start with unity gain mask
            gain_mask = np.ones(n_bins)

            if auto_detect:
                # Detect dominant peaks in the spectrum
                peak_freqs = self._detect_peaks(
                    magnitude_db, freqs, num_peaks, freq_min, freq_max
                )
                # Apply notch at each detected peak (if it's strong enough)
                for pk_freq in peak_freqs:
                    notch = self._build_notch_filter(
                        freqs, np.abs(spectrum), pk_freq, bandwidth, cut_gain
                    )
                    gain_mask *= notch
            else:
                # Apply static notch filters
                for mask, _ in static_filter_masks:
                    gain_mask[mask > 0] = np.minimum(gain_mask[mask > 0], cut_gain)

            # Apply gain mask to spectrum
            filtered_spectrum = spectrum * gain_mask
            filtered_frame = np.fft.irfft(filtered_spectrum, n=window_size)
            filtered_frame *= window

            output[start : start + window_size] += filtered_frame

        # Normalize overlap-add
        overlap_factor = np.sum(window ** 2) / hop_size
        if overlap_factor > 0:
            output /= overlap_factor

        # Clip to prevent extreme values
        output = np.clip(output, -1.0, 1.0)

        return output[:n_samples]

    def _detect_peaks(
        self,
        magnitude_db: np.ndarray,
        freqs: np.ndarray,
        num_peaks: int,
        freq_min: float,
        freq_max: float,
    ) -> List[float]:
        """Detect dominant spectral peaks within the frequency range.

        Args:
            magnitude_db: Magnitude spectrum in dB.
            freqs: Frequency axis array.
            num_peaks: Maximum number of peaks to detect.
            freq_min: Minimum frequency to consider.
            freq_max: Maximum frequency to consider.

        Returns:
            List of peak frequencies sorted by prominence.
        """
        # Only consider frequencies in range
        range_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(range_mask):
            return []

        # Find local maxima within the range
        in_range_indices = np.where(range_mask)[0]
        bin_mags = magnitude_db[in_range_indices]
        bin_freqs = freqs[in_range_indices]

        if len(bin_freqs) < 3:
            return []

        peaks: List[Tuple[float, float]] = []

        for i in range(1, len(bin_freqs) - 1):
            if bin_mags[i] > bin_mags[i - 1] and bin_mags[i] > bin_mags[i + 1]:
                prominence = bin_mags[i] - np.median(bin_mags)
                if prominence > 1.0:  # Minimum 1dB prominence to count
                    peaks.append((bin_freqs[i], bin_mags[i]))

        # Sort by magnitude (descending) and return top N frequencies
        peaks.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in peaks[:num_peaks]]

    def _build_notch_filter(
        self,
        freqs: np.ndarray,
        magnitude: np.ndarray,
        center_freq: float,
        bandwidth: float,
        cut_gain: float,
    ) -> np.ndarray:
        """Build a notch filter mask centered at a frequency.

        Creates a smooth notch (inverse bell curve) at the center frequency
        with the given bandwidth, scaled by cut_gain.

        Args:
            freqs: Frequency array from rfft.
            magnitude: Magnitude spectrum (unused, kept for future weighting).
            center_freq: Center frequency of the notch.
            bandwidth: Bandwidth of the notch in Hz.
            cut_gain: Gain multiplier at notch center (0-1).

        Returns:
            Gain mask array with notch applied.
        """
        mask = np.ones_like(freqs)
        sigma = bandwidth / 2.355  # Convert bandwidth to Gaussian sigma

        if sigma > 0:
            # Apply Gaussian notch centered at center_freq
            notch = 1.0 - (1.0 - cut_gain) * np.exp(
                -((freqs - center_freq) ** 2) / (2 * sigma ** 2)
            )
            mask = notch

        return mask

    def _notch_filter_mask(
        self, freqs: np.ndarray, center_freq: float, bandwidth: float
    ) -> np.ndarray:
        """Build a notch filter mask for a static frequency.

        Returns the notch gain values (0-1) across the frequency axis.
        Used for pre-computed static filters.

        Args:
            freqs: Frequency array from rfft.
            center_freq: Center frequency of the notch.
            bandwidth: Bandwidth of the notch in Hz.

        Returns:
            Notch gain mask array.
        """
        return self._build_notch_filter(freqs, np.ones_like(freqs), center_freq, bandwidth, 0.5)

    @staticmethod
    def _default_center_frequencies(freq_min: float, freq_max: float) -> List[float]:
        """Get default octave-band center frequencies in the given range.

        Uses standard ISO octave band center frequencies starting at 31.25 Hz.

        Args:
            freq_min: Minimum frequency.
            freq_max: Maximum frequency.

        Returns:
            List of center frequencies within the range.
        """
        # ISO octave band center frequencies
        all_centers = [
            31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000
        ]
        return [f for f in all_centers if freq_min <= f <= freq_max]
