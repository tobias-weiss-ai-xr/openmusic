"""Spectral gating effect for OpenMusic dub techno generation."""

from typing import Any, Dict, List

import numpy as np

from .base import Effect


class SpectralGate(Effect):
    """Adaptive spectral gate for noise reduction and rhythmic gating.

    Performs FFT-based spectral analysis to detect signal content across
    frequency bands. Bins below threshold are attenuated, creating a
    clean noise floor removal effect. Can also create rhythmic gating
    by syncing to tempo.
    """

    def __init__(self) -> None:
        self.name = "spectral_gate"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        threshold_db = float(params.get("threshold_db", -40))
        attack_ms = float(params.get("attack_ms", 10))
        release_ms = float(params.get("release_ms", 100))
        hold_ms = float(params.get("hold_ms", 20))
        frequency_bands = params.get("frequency_bands", None)
        sync_to_tempo = float(params.get("sync_to_tempo", 0))
        sync_phase = float(params.get("sync_phase", 0.5))
        sample_rate = int(params.get("sample_rate", 48000))

        threshold_db = np.clip(threshold_db, -100, 0)
        attack_ms = np.clip(attack_ms, 1, 200)
        release_ms = np.clip(release_ms, 10, 2000)
        hold_ms = np.clip(hold_ms, 0, 500)
        sync_to_tempo = max(sync_to_tempo, 0.0)
        sync_phase = np.clip(sync_phase, 0.1, 0.9)

        is_stereo = len(audio.shape) > 1 and audio.shape[1] == 2

        if is_stereo:
            left_out = self._process_mono(
                audio[:, 0], threshold_db, attack_ms, release_ms, hold_ms,
                frequency_bands, sync_to_tempo, sync_phase, sample_rate,
            )
            right_out = self._process_mono(
                audio[:, 1], threshold_db, attack_ms, release_ms, hold_ms,
                frequency_bands, sync_to_tempo, sync_phase, sample_rate,
            )
            return np.column_stack([left_out, right_out])

        return self._process_mono(
            audio, threshold_db, attack_ms, release_ms, hold_ms,
            frequency_bands, sync_to_tempo, sync_phase, sample_rate,
        )

    def _process_mono(
        self,
        audio: np.ndarray,
        threshold_db: float,
        attack_ms: float,
        release_ms: float,
        hold_ms: float,
        frequency_bands: List[float] | None,
        sync_to_tempo: float,
        sync_phase: float,
        sample_rate: int,
    ) -> np.ndarray:
        if len(audio) == 0:
            return audio.copy()

        if frequency_bands is not None and len(frequency_bands) >= 2:
            return self._process_per_band(
                audio, threshold_db, attack_ms, release_ms, hold_ms,
                frequency_bands, sync_to_tempo, sync_phase, sample_rate,
            )

        return self._process_full_spectrum(
            audio, threshold_db, attack_ms, release_ms, hold_ms,
            sync_to_tempo, sync_phase, sample_rate,
        )

    def _process_full_spectrum(
        self,
        audio: np.ndarray,
        threshold_db: float,
        attack_ms: float,
        release_ms: float,
        hold_ms: float,
        sync_to_tempo: float,
        sync_phase: float,
        sample_rate: int,
    ) -> np.ndarray:
        fft_size = 2048
        hop_size = fft_size // 4
        window = np.hanning(fft_size)

        threshold_linear = 10 ** (threshold_db / 20.0)

        attack_samples = int(attack_ms / 1000.0 * sample_rate)
        release_samples = int(release_ms / 1000.0 * sample_rate)
        hold_samples = int(hold_ms / 1000.0 * sample_rate)

        accumulation = np.zeros(len(audio) + fft_size)

        current_gain = 1.0
        hold_counter = 0

        num_frames = (len(audio) - fft_size) // hop_size + 1

        for frame_idx in range(num_frames):
            start = frame_idx * hop_size
            end = start + fft_size

            frame = audio[start:end].copy()
            frame_windowed = frame * window

            spectrum = np.fft.rfft(frame_windowed)
            magnitudes = np.abs(spectrum)

            frame_energy = np.mean(magnitudes)
            is_above = frame_energy > threshold_linear

            if sync_to_tempo > 0:
                beat_period_samples = int(60.0 / sync_to_tempo * sample_rate)
                beat_phase = (start % beat_period_samples) / beat_period_samples
                tempo_gate = 1.0 if beat_phase < sync_phase else 0.0
                is_above = is_above and (tempo_gate > 0.5)

            target_gain = 1.0 if is_above else 0.0

            if target_gain >= current_gain:
                hold_counter = 0
                current_gain = min(
                    current_gain + (1.0 / max(attack_samples, 1)),
                    1.0,
                )
            else:
                if hold_counter < hold_samples:
                    hold_counter += 1
                else:
                    current_gain = max(
                        current_gain - (1.0 / max(release_samples, 1)),
                        0.0,
                    )

            spectrum_gated = spectrum * current_gain
            frame_out = np.fft.irfft(spectrum_gated, n=fft_size)
            frame_out *= window

            accumulation[start : start + fft_size] += frame_out

        return accumulation[: len(audio)]

    def _process_per_band(
        self,
        audio: np.ndarray,
        threshold_db: float,
        attack_ms: float,
        release_ms: float,
        hold_ms: float,
        frequency_bands: List[float],
        sync_to_tempo: float,
        sync_phase: float,
        sample_rate: int,
    ) -> np.ndarray:
        fft_size = 2048
        hop_size = fft_size // 4
        window = np.hanning(fft_size)

        threshold_linear = 10 ** (threshold_db / 20.0)
        attack_samples = int(attack_ms / 1000.0 * sample_rate)
        release_samples = int(release_ms / 1000.0 * sample_rate)
        hold_samples = int(hold_ms / 1000.0 * sample_rate)

        accumulation = np.zeros(len(audio) + fft_size)
        freq_bins = np.fft.rfftfreq(fft_size, d=1.0 / sample_rate)

        band_bin_edges: List[int] = []
        for freq in frequency_bands:
            bin_idx = int(freq / sample_rate * fft_size)
            band_bin_edges.append(
                min(bin_idx, len(freq_bins) - 1),
            )
        if not band_bin_edges or band_bin_edges[0] > 0:
            band_bin_edges.insert(0, 0)
        if band_bin_edges[-1] < len(freq_bins) - 1:
            band_bin_edges.append(len(freq_bins) - 1)

        num_bands = len(band_bin_edges) - 1
        band_gains = np.ones(num_bands)
        band_hold_counters = np.zeros(num_bands, dtype=int)

        num_frames = (len(audio) - fft_size) // hop_size + 1

        for frame_idx in range(num_frames):
            start = frame_idx * hop_size
            end = start + fft_size

            frame = audio[start:end].copy()
            frame_windowed = frame * window

            spectrum = np.fft.rfft(frame_windowed)
            magnitudes = np.abs(spectrum)

            tempo_gate = 1.0
            if sync_to_tempo > 0:
                beat_period_samples = int(60.0 / sync_to_tempo * sample_rate)
                beat_phase = (start % beat_period_samples) / beat_period_samples
                tempo_gate = 1.0 if beat_phase < sync_phase else 0.0

            for band_idx in range(num_bands):
                band_start = band_bin_edges[band_idx]
                band_end = band_bin_edges[band_idx + 1]

                band_energy = np.mean(magnitudes[band_start:band_end])
                is_above = (band_energy > threshold_linear) and (tempo_gate > 0.5)

                target_gain = 1.0 if is_above else 0.0

                if target_gain >= band_gains[band_idx]:
                    band_hold_counters[band_idx] = 0
                    band_gains[band_idx] = min(
                        band_gains[band_idx] + (1.0 / max(attack_samples, 1)),
                        1.0,
                    )
                else:
                    if band_hold_counters[band_idx] < hold_samples:
                        band_hold_counters[band_idx] += 1
                    else:
                        band_gains[band_idx] = max(
                            band_gains[band_idx] - (1.0 / max(release_samples, 1)),
                            0.0,
                        )

                spectrum[band_start:band_end] *= band_gains[band_idx]

            frame_out = np.fft.irfft(spectrum, n=fft_size)
            frame_out *= window

            accumulation[start : start + fft_size] += frame_out

        return accumulation[: len(audio)]
