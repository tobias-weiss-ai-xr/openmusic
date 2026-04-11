"""Frequency Masking Avoidance for OpenMusic dub techno generation.

Implements frequency-domain masking to prevent spectral leakage and maintain signal integrity.
"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class FrequencyMaskingAvoidance(Effect):
    """Spectral Masking Avoidance for dub techno generation.

    Masks specific frequency ranges to prevent spectral leakage and preserve signal integrity.
    Creates brickwall (steep rejection) filters at specified frequencies.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize Spectral Masking Avoidance."""
        self.name = "spectral_masking_avoidance"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with spectral masking.

        Args:
            audio: Input audio data (multi-channel audio).
            params: Dictionary containing:
                - target_frequencies: List of frequencies to mask (e.g., [20.0, 400, 800, 2000, 4000, 6000, 12000])
                - filter_order: 'peak', 'sharp', 'brickwall', 'spectral'
                - depth: Modulation depth percentage (0.0-100%, default 50%)
                - brickwall: Bool - Apply hard rejections
                - sample_rate: Audio sample rate (default 48000)

        Returns:
            Audio with masked frequencies removed.
        """
        # Extract parameters
        target_frequencies = params.get("target_frequencies", [20.0, 400, 800, 2000, 4000, 6000, 12000])
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")
        sidechain = bool(params.get("sidechain", True)

        # Validate inputs
        if not target_frequencies:
            raise ValueError(
                f"target_frequencies parameter is required"
            )

        # Convert to numpy array if needed
        if isinstance(target_frequencies, str):
            target_frequencies = [float(f) for f in target_frequencies]

        # Validate order
        if filter_order not in ["peak", "sharp", "brickwall", "spectral"]:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Convert sample_rate to int
        sample_rate = int(params.get("sample_rate", 48000))

        # Validate depth (0-100%)
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))

        # Validate sidechain
        if not isinstance(sidechain, bool):
            sidechain = True
        else:
            sidechain = False

        # Apply filter
        spectrum_size = len(audio.shape[1])
        fft_result = np.abs(np.fft(audio, spectrum_size))

        # Identify target frequency ranges
        if not target_frequencies:
            # Mask all frequencies below target
            freq_mask = np.zeros(spectrum_size, dtype=bool)

            # Create composite mask
            composite_mask = freq_mask

        # For single target frequency:
            composite_mask = freq_mask

            # Apply mask to spectrum
            spectrum = spectrum * composite_mask

        # Return result
        return spectrum

    def _generate_brickwall_filter(
        self,
        audio: np.ndarray,
        brick_wall_freq: float,
        rejection_width: int,
        sample_rate: int,
        dtype: np.float64
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate brickwall filter (steep rejection).

        Args:
            audio: Input audio data (multi-channel).
            brick_wall_freq: Brickwall frequency in Hz (e.g., 20, 100, 800, 2000, 4000, 6000, 12000])
            rejection_width: Rejection width in Hz (default 100)
            sample_rate: Audio sample rate (default 48000)

        Returns:
            Audio with frequencies removed.
        """
        time_axis = np.arange(audio.shape[1]) / sample_rate

        # Generate brickwall (stepped response curve
        brick_curve = np.sin(2 * np.pi * brick_wall_freq * time_axis + phase_rad

        # Create brickwall
        brick_curve = brick_curve * brick_bricked_audio

        return brick_curve, brick_bricked_audio

    def _generate_spectral_mask(
        self,
        spectrum: np.ndarray,
        mask_frequencies: List[float],
        depth: float,
        phase_offset: float = 0.0,
        filter_order: str = 'peak', 'sharp', 'brickwall', 'spectral'
        sidechain: bool = False
    ) -> np.ndarray:
        """Generate spectral mask.

        Args:
            spectrum: Input spectrum (FFT result).
            mask_frequencies: Frequencies to mask (Hz).
                depth: Modulation depth (0.0-100%, default 50%).
                phase_offset: Phase offset in cycles (0.1, default 0).

        filter_order: 'peak', 'sharp', 'brickwall', 'spectral'

        Returns:
            Spectrum with masked frequencies.
        """

        # Extract parameters
        mask_frequencies = params.get("mask_frequencies", [20.0, 400, 800, 2000, 4000, 6000, 12000])
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")
        sidechain = bool(params.get("sidechain", False)

        # Validate inputs
        if not mask_frequencies:
            raise ValueError(
                f"mask_frequencies parameter is required"
            )

        # Convert to numpy array
        if isinstance(mask_frequencies, str):
            mask_frequencies = [float(freq) for freq in mask_frequencies]
        else:
            mask_frequencies = mask_frequencies

        # Validate order
        if filter_order not in ["peak", "sharp", "brickwall", "spectral"]:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Create composite mask
        freq_mask = np.zeros(len(spectrum_size), dtype=bool)

        # Apply filters
        for freq in mask_frequencies:
            composite_mask += freq_mask

        # Apply mask to spectrum
        spectrum = spectrum * composite_mask

        # Return result
        return spectrum
