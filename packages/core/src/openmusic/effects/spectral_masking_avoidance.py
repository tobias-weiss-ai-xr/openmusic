"""Spectral masking avoidance effect for OpenMusic.

Implements automated frequency carving that detects overlapping frequency
content and applies subtle EQ cuts to reduce spectral masking and improve
clarity between audio layers. Uses FFT-based spectral analysis with
overlapping windows to find spectral peaks and apply gentle notch filters
at conflict frequencies.
"""

from typing import Any, Dict, List

import numpy as np

from .base import Effect


class SpectralMaskingAvoidance(Effect):
    """Spectral masking avoidance effect for frequency carving.

    Uses FFT-based spectral analysis with overlapping windows to detect
    spectral peaks and apply gentle notch filters at conflict frequencies.
    This reduces spectral crowding and creates cleaner separation between
    frequency components.

    The effect operates by:
    1. Splitting audio into overlapping frames with a Hann window
    2. Computing the FFT magnitude spectrum for each frame
    3. Detecting spectral peaks (local maxima above a sensitivity-dependent threshold)
    4. Applying narrow gaussian notch filters at each peak frequency
    5. Reconstructing the audio via overlap-add

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize the SpectralMaskingAvoidance effect."""
        self.name = "spectral_masking_avoidance"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with spectral masking avoidance.

        Args:
            audio: Input audio data. Shape can be:
                   - (N,) for mono audio
                   - (2, N) for stereo audio
            params: Dictionary containing:
                   - sensitivity: Detection sensitivity (0-100, default 50).
                     Higher values detect more peaks and apply more carving.
                   - max_cut_db: Maximum gain reduction in dB (0-24, default 6).
                   - frequency_range: Frequency range to process as [min, max]
                     in Hz (default [20, 20000]).
                   - auto_detect: Auto-detect conflict frequencies vs targeting
                     specific bands (default True).
                   - notch_width_factor: Width of notch relative to peak bandwidth
                     (0.1-1.0, default 0.5). Lower = narrower notches.
                   - window_size: FFT window size in samples (default 2048).
                   - hop_size: Hop size in samples (default 512).
                   - sample_rate: Audio sample rate (default 48000).

        Returns:
            Processed audio with same shape as input.
        """
        # Extract parameters with defaults
        sensitivity = float(params.get("sensitivity", 50))
        max_cut_db = float(params.get("max_cut_db", 6))
        frequency_range: List[float] = params.get("frequency_range", [20.0, 20000.0])
        auto_detect = bool(params.get("auto_detect", True))
        notch_width_factor = float(params.get("notch_width_factor", 0.5))
        window_size = int(params.get("window_size", 2048))
        hop_size = int(params.get("hop_size", 512))
        sample_rate = int(params.get("sample_rate", 48000))

        # Clamp parameters to valid ranges
        sensitivity = float(np.clip(sensitivity, 0, 100))
        max_cut_db = float(np.clip(max_cut_db, 0, 24))
        notch_width_factor = float(np.clip(notch_width_factor, 0.1, 1.0))
        window_size = max(64, int(np.clip(window_size, 64, 16384)))
        hop_size = max(1, int(np.clip(hop_size, 1, window_size)))

        # Handle empty audio
        if audio.size == 0:
            return audio.copy()

        # Determine if stereo: shape (2, N) vs (N,)
        is_stereo = len(audio.shape) > 1 and audio.shape[0] == 2

        if is_stereo:
            left = self._process_channel(
                audio[0, :],
                sensitivity,
                max_cut_db,
                frequency_range,
                auto_detect,
                notch_width_factor,
                window_size,
                hop_size,
                sample_rate,
            )
            right = self._process_channel(
                audio[1, :],
                sensitivity,
                max_cut_db,
                frequency_range,
                auto_detect,
                notch_width_factor,
                window_size,
                hop_size,
                sample_rate,
            )
            return np.stack([left, right], axis=0)
        else:
            return self._process_channel(
                audio,
                sensitivity,
                max_cut_db,
                frequency_range,
                auto_detect,
                notch_width_factor,
                window_size,
                hop_size,
                sample_rate,
            )

    def _process_channel(
        self,
        audio: np.ndarray,
        sensitivity: float,
        max_cut_db: float,
        frequency_range: List[float],
        auto_detect: bool,
        notch_width_factor: float,
        window_size: int,
        hop_size: int,
        sample_rate: int,
    ) -> np.ndarray:
        """Process a single channel of audio.

        Args:
            audio: Mono audio as 1D array.
            sensitivity: Detection sensitivity (0-100).
            max_cut_db: Maximum gain reduction in dB.
            frequency_range: [min_freq, max_freq] in Hz.
            auto_detect: Auto-detect peaks vs gentle shaping.
            notch_width_factor: Width of notches (0.1-1.0).
            window_size: FFT window size in samples.
            hop_size: Hop size in samples.
            sample_rate: Audio sample rate.

        Returns:
            Processed mono audio with same length as input.
        """
        n_samples = len(audio)

        if n_samples == 0:
            return audio.copy()

        # Create Hann analysis/synthesis window
        window = np.hanning(window_size)

        # Compute number of overlapping frames and padded length
        n_frames = max(1, (n_samples - window_size + hop_size - 1) // hop_size + 1)
        padded_length = (n_frames - 1) * hop_size + window_size
        pad_amount = padded_length - n_samples

        if pad_amount > 0:
            audio_padded = np.pad(audio, (0, pad_amount), mode="reflect")
        else:
            audio_padded = audio.copy()

        # Frequency bin centers for the FFT
        freqs = np.fft.rfftfreq(window_size, d=1.0 / sample_rate)
        n_bins = len(freqs)

        # Convert max cut in dB to linear gain factor
        max_cut_linear = float(10.0 ** (-max_cut_db / 20.0))

        # Build frequency range mask
        freq_min = float(frequency_range[0]) if len(frequency_range) > 0 else 20.0
        freq_max = float(frequency_range[1]) if len(frequency_range) > 1 else 20000.0
        freq_mask = (freqs >= freq_min) & (freqs <= freq_max)

        # Output buffer
        output = np.zeros(padded_length, dtype=np.float64)

        for frame_idx in range(n_frames):
            start = frame_idx * hop_size
            frame = audio_padded[start : start + window_size] * window

            # Forward FFT
            spectrum = np.fft.rfft(frame)
            magnitude = np.abs(spectrum)

            # Build gain reduction mask (1.0 = no reduction)
            gain_mask = np.ones(n_bins, dtype=np.float64)

            if auto_detect:
                # Detect spectral peaks and apply notch filters
                peaks = self._find_peaks(magnitude, freqs, freq_mask, sensitivity)

                for peak_bin in peaks:
                    peak_freq = freqs[peak_bin]
                    peak_mag = magnitude[peak_bin]

                    # Bandwidth proportional to frequency (constant-Q approximation)
                    bandwidth = max(10.0, peak_freq * 0.1)
                    notch_sigma = bandwidth * notch_width_factor * 0.5

                    # Gaussian distance from peak in Hz
                    freq_dist = np.abs(freqs - peak_freq)
                    notch_profile = np.exp(
                        -0.5 * ((freq_dist / max(notch_sigma, 1.0)) ** 2)
                    )

                    # Relative strength: how dominant this peak is in the spectrum
                    if np.any(freq_mask):
                        avg_mag = float(np.mean(magnitude[freq_mask]))
                    else:
                        avg_mag = float(np.mean(magnitude))
                    rel_strength = np.clip(
                        peak_mag / max(avg_mag * 2.0, 1e-10), 0.0, 1.0
                    )

                    # Apply notch: deeper cut for stronger, more dominant peaks
                    cut_amount = 1.0 - (1.0 - max_cut_linear) * notch_profile * rel_strength
                    gain_mask = np.minimum(gain_mask, cut_amount)
            else:
                # Non-auto-detect: gentle spectral shaping across the range
                range_indices = np.where(freq_mask)[0]
                if len(range_indices) > 1:
                    shaping = np.ones(n_bins, dtype=np.float64)
                    center = float(len(range_indices)) / 2.0
                    for i, idx in enumerate(range_indices):
                        dist_from_center = abs(float(i) - center) / max(center, 1.0)
                        reduction = 1.0 - (1.0 - max_cut_linear) * 0.3 * (
                            1.0 - dist_from_center
                        )
                        shaping[idx] = reduction
                    gain_mask = np.minimum(gain_mask, shaping)

            # Apply gain mask (preserves phase, only modifies magnitude)
            processed_spec = spectrum * gain_mask

            # Inverse FFT and re-window
            processed_frame = np.fft.irfft(processed_spec, n=window_size)
            processed_frame = processed_frame * window

            # Overlap-add into output buffer
            output[start : start + window_size] += processed_frame

        # Normalize using the same scalar approach as existing effects (spectral.py)
        overlap_factor = float(np.sum(window**2)) / float(hop_size)
        if overlap_factor > 1e-10:
            output /= overlap_factor

        # Guard against any non-finite values from edge conditions
        output = np.nan_to_num(output, nan=0.0, posinf=0.0, neginf=0.0)

        # Trim to original length and ensure same dtype as input
        result = output[:n_samples].astype(audio.dtype)

        return result

    @staticmethod
    def _find_peaks(
        magnitude: np.ndarray,
        freqs: np.ndarray,
        freq_mask: np.ndarray,
        sensitivity: float,
    ) -> List[int]:
        """Find spectral peaks for notch carving.

        A peak is defined as a frequency bin whose magnitude exceeds both of
        its immediate neighbors and is above an adaptive threshold derived
        from the noise floor and sensitivity setting.

        Args:
            magnitude: Magnitude spectrum (from rFFT).
            freqs: Frequency bin centers in Hz (for masking).
            freq_mask: Boolean mask selecting the frequency range of interest.
            sensitivity: Detection sensitivity (0-100). Higher = more peaks.

        Returns:
            Sorted list of peak bin indices.
        """
        if np.all(magnitude == 0):
            return []

        # Estimate noise floor as mean magnitude in the target range
        if np.any(freq_mask):
            noise_floor = float(np.mean(magnitude[freq_mask]))
        else:
            noise_floor = float(np.mean(magnitude))

        # Map sensitivity (0-100) to a peak threshold multiplier
        # sensitivity=0: threshold=4.0*noise_floor (very selective)
        # sensitivity=100: threshold=1.1*noise_floor (very inclusive)
        threshold_mult = 4.0 - (sensitivity / 100.0) * 2.9
        peak_threshold = noise_floor * max(threshold_mult, 1.1)

        n_bins = len(magnitude)
        peak_candidates: List[int] = []

        for i in range(1, n_bins - 1):
            if not freq_mask[i]:
                continue
            if (
                magnitude[i] > magnitude[i - 1]
                and magnitude[i] > magnitude[i + 1]
                and magnitude[i] > peak_threshold
            ):
                peak_candidates.append(i)

        # Limit total peaks to avoid excessive carving
        max_peaks = max(5, n_bins // 16)
        if len(peak_candidates) > max_peaks:
            # Keep only the strongest peaks
            candidates_with_mag = [(p, magnitude[p]) for p in peak_candidates]
            candidates_with_mag.sort(key=lambda x: x[1], reverse=True)
            peak_candidates = [p[0] for p in candidates_with_mag[:max_peaks]]

        return sorted(peak_candidates)
