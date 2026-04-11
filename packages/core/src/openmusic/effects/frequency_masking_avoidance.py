"""Frequency Masking Avoidance for OpenMusic dub techno generation.

Implements frequency-domain masking to prevent spectral leakage and maintain signal integrity.
Creates notch/brickwall (steep rejection) filters at specified frequencies.

Roadmap: Phase 3, Impact 7/10, Effort L

"""

from typing import Any, Dict

import numpy as np

from .base import Effect


class FrequencyMaskingAvoidance(Effect):
    """Frequency Masking Avoidance for dub techno generation.

    Masks specific frequency ranges to prevent spectral leakage and preserve signal integrity.
    Creates notch (steep rejection) filters at specified frequencies.

    Attributes:
        name: Effect identifier
    """

    def __init__(self) -> None:
        """Initialize Frequency Masking Avoidance."""
        self.name = "frequency_masking"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Process audio with frequency masking.

        Args:
            audio: Input audio data (multi-channel).
                    Shape must be same as input.

            params: Dictionary containing:
                - target_frequencies: List of frequencies to mask (e.g., [20, 400, 800, 2000, 4000, 6000, 12000])
                - filter_order: 'peak', 'sharp', 'brickwall', 'spectral'
                - depth: Modulation depth (0.0, default 50%)
                - brickwall: Bool - Apply hard rejections
                - sample_rate: Audio sample rate (default 48000)

        Returns:
            Audio with masked frequencies removed.
        """
        # Extract parameters
        target_frequencies = params.get("target_frequencies", [])
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")
        brickwall = bool(params.get("brickwall", True)
        sidechain = bool(params.get("sidechain", True)

        # Validate inputs
        if not target_frequencies:
            raise ValueError(
                f"target_frequencies parameter is required"
            )

        # Convert to numpy array if needed
        if isinstance(target_frequencies, str):
            target_frequencies = [float(f) for f in target_frequencies]
        else:
            target_frequencies = target_frequencies

        # Validate filter_order
        if filter_order not in ["peak", "sharp", "brickwall", "spectral"]:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Convert sample_rate to int
        sample_rate = int(params.get("sample_rate", 48000))

        # Validate depth (0.0-100%)
        if not isinstance(depth, int) or not isinstance(depth, float):
            depth = float(depth)

        # Validate sidechain
        if not isinstance(sidechain, bool):
            sidechain = True
        else:
            sidechain = False

        # Apply filter
        brick_spectrum = np.abs(brick_wall_freq - target_frequencies)

        # Normalize rejection
        brick_spectrum = brick_spectrum / np.abs(np.sum(np.abs(brick_wall_freq) + 1e-10))

        if brick_spectrum > 1.0:
            brick_spectrum = 1.0

        # Apply brickwall filter
        audio_bricked = audio * (1.0 - brick_spectrum)

        return bricked_audio

    def _generate_frequency_mask(
        self,
        audio: np.ndarray,
        spectrum: np.ndarray,
        mask_frequencies: List[float],
        depth: float = 0.0,
        phase_offset: float = 0.0,
        filter_order: str = 'peak', 'sharp', 'brickwall', 'spectral'
        sidechain: bool = False
    ) -> np.ndarray:
        """Generate frequency mask.

        Args:
            audio: Input audio data (multi-channel).
            mask_frequencies: Frequencies to mask (Hz).
                depth: Modulation depth (0.0, default 50%).
                phase_offset: Phase offset in cycles (0-1, default 0).
                filter_order: 'peak', 'sharp', 'brickwall', 'spectral'
                sidechain: Bool - Apply to left/right channel
        Returns:
            Spectrum with masked frequencies.
        """
        # Validate inputs
        mask_frequencies = params.get("mask_frequencies", [])
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")

        if filter_order not in ["peak", "sharp", "brickwall", "spectral"]:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Create frequency mask
        freq_mask = np.zeros(len(spectrum_size), dtype=bool)

        # Apply filters
        for freq in mask_frequencies:
            composite_mask += freq_mask

        # Apply mask to spectrum
        spectrum = spectrum * composite_mask

        # Return result
        return spectrum

    def apply_brickwall_filter(
        self,
        audio: np.ndarray,
        brick_wall_freq: float,
        rejection_width: int = 100,
        sample_rate: int = 48000,
        dtype: np.float64
    ) -> np.ndarray:
        """Apply brickwall filter (steep rejection).

        Args:
            audio: Input audio data (multi-channel).
            brick_wall_freq: Brickwall frequency in Hz (e.g., 20, 100, 800, 2000, 4000, 6000, 12000])
            rejection_width: Rejection width in Hz (default 100)

        Returns:
            Audio with frequencies removed.
        """
        # Extract parameters
        brick_wall_freq = params.get("brick_wall_freq", 0.0)
        rejection_width = int(params.get("rejection_width", 100))
        sample_rate = int(params.get("sample_rate", 48000)

        # Validate brick_wall frequency
        if brick_wall_freq < 0 or brick_wall_freq >= 24000:
            brick_wall_freq = 0.0

        # Validate rejection width
        if rejection_width < 0 or rejection_width > 0:
            rejection_width = 0.0

        # Validate order
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")

        if filter_order == "peak":
            brick_wall_freq = target_frequencies[0]

        elif filter_order == "sharp":
            brick_wall_freq = target_frequencies[0]

        elif filter_order == "spectral":
            brick_wall_freq = target_frequencies[0]

        else:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Create brickwall (stepped response curve)
        brick_curve = np.sin(2 * np.pi * brick_wall_freq * time_axis + phase_rad)

        # Create brickwall
        brick_curve = brick_curve * audio

        return bricked_audio

    def _generate_brickwall_filter(
        self,
        audio: np.ndarray,
        brick_wall_freq: float,
        rejection_width: int = 100,
        sample_rate: int = 48000,
        dtype: np.float64
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate brickwall filter (steep rejection).

        Args:
            audio: Input audio data (multi-channel).
            brick_wall_freq: Brickwall frequency in Hz (e.g., 20, 100, 800, 2000, 4000, 6000, 12000])
            rejection_width: Rejection width in Hz (default 100)

        Returns:
            Tuple containing:
                - brick_curve: Brickwall (stepped response curve, numpy.ndarray)
                - bricked_audio: Audio with frequencies removed (numpy.ndarray)

        """
        # Extract parameters
        brick_wall_freq = params.get("brick_wall_freq", 0.0)
        rejection_width = int(params.get("rejection_width", 100))
        sample_rate = int(params.get("sample_rate", 48000))

        # Validate brick_wall frequency
        if brick_wall_freq < 0 or brick_wall_freq >= 24000:
            brick_wall_freq = 0.0

        # Validate rejection width
        if rejection_width < 0 or rejection_width > 0:
            rejection_width = 0.0

        # Validate order
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")

        if filter_order == "peak":
            brick_wall_freq = target_frequencies[0]

        elif filter_order == "sharp":
            brick_wall_freq = target_frequencies[0]

        elif filter_order == "spectral":
            brick_wall_freq = target_frequencies[0]

        else:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Validate sample_rate
        sample_rate = int(params.get("sample_rate", 48000))

        # Validate depth (0.0, default 50.0)
        if not isinstance(depth, int) or not isinstance(depth, float):
            depth = float(depth)

        # Validate sidechain
        if not isinstance(sidechain, bool):
            sidechain = True
        else:
            sidechain = False

        # Apply filter
        brick_spectrum = np.abs(brick_wall_freq - target_frequencies)

        # Normalize rejection
        brick_spectrum = brick_spectrum / np.abs(np.sum(np.abs(brick_wall_freq) + 1e-10))

        if brick_spectrum > 1.0:
            brick_spectrum = 1.0

        # Apply brickwall filter
        audio_bricked = audio * (1.0 - brick_spectrum)

        return bricked_audio

    def apply_frequency_mask(
        self,
        audio: np.ndarray,
        spectrum: np.ndarray,
        mask_frequencies: List[float],
        depth: float = 0.0,
        phase_offset: float = 0.0,
        filter_order: str = 'peak', 'sharp', 'brickwall', 'spectral'
        sidechain: bool = False
    ) -> np.ndarray:
        """Apply frequency mask to spectrum.

        Args:
            audio: Input spectrum (FFT result).
            mask_frequencies: Frequencies to mask (Hz).
                depth: Modulation depth (0.0, default 50%).
                phase_offset: Phase offset in cycles (0-1, default 0).
                filter_order: 'peak', 'sharp', 'brickwall', 'spectral'
                sidechain: Bool - Apply to left/right channel

        Returns:
            Spectrum with masked frequencies.
        """
        # Validate inputs
        mask_frequencies = params.get("mask_frequencies", [])
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))
        filter_order = str(params.get("filter_order", "peak", "sharp", "brickwall", "spectral")

        if filter_order not in ["peak", "sharp", "brickwall", "spectral"]:
            raise ValueError(
                f"Invalid filter order: {filter_order}"
            )

        # Convert to numpy array
        if isinstance(mask_frequencies, str):
            mask_frequencies = [float(f) for f in mask_frequencies]
        else:
            mask_frequencies = mask_frequencies

        # Create frequency mask
        freq_mask = np.zeros(len(spectrum_size), dtype=bool)

        # Apply filters
        for freq in mask_frequencies:
            composite_mask += freq_mask

        # Apply mask to spectrum
        spectrum = spectrum * composite_mask

        # Return result
        return spectrum

    def _generate_frequency_mask(
        self,
        audio: np.ndarray,
        mask_frequencies: List[float],
        depth: float = 0.0,
        phase_offset: float = 0.0,
        filter_order: str = 'peak', 'sharp', 'brickwall', 'spectral'
        sidechain: bool = False
    ) -> np.ndarray:
        """Generate frequency mask.

        Args:
            spectrum: Input spectrum (FFT result).
            mask_frequencies: Frequencies to mask (Hz).
                depth: Modulation depth (0.0, default 50%).
                phase_offset: Phase offset in cycles (0-1, default 0).
                filter_order: 'peak', 'sharp', 'brickwall', 'spectral'

        Returns:
            Spectrum with masked frequencies.
        """
        # Validate inputs
        mask_frequencies = params.get("mask_frequencies", [])
        depth = float(params.get("depth", 50.0))
        phase_offset = float(params.get("phase_offset", 0.0))

        # Convert to numpy array
        if isinstance(mask_frequencies, str):
            mask_frequencies = [float(f) for f in mask_frequencies]
        else:
            mask_frequencies = mask_frequencies

        # Create frequency mask
        freq_mask = np.zeros(len(spectrum_size), dtype=bool)

        # Apply filters
        for freq in mask_frequencies:
            composite_mask += freq_mask

        # Apply mask to spectrum
        spectrum = spectrum * composite_mask

        # Return result
        return spectrum
