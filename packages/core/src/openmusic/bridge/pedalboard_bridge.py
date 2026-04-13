"""Native Python DSP bridge using Spotify Pedalboard."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from openmusic.effects.pedalboard_chain import PedalboardEffectsChain, PRESETS

logger = logging.getLogger(__name__)


class PythonDSPBridge:
    """Process audio segments using Pedalboard (native Python, no Node.js)."""

    def __init__(
        self,
        preset: str = "deep_dub",
        apply_mastering: bool = True,
        target_lufs: float = -16.0,
    ):
        self.preset_name = preset
        self.apply_mastering = apply_mastering
        self.target_lufs = target_lufs

    def is_available(self) -> bool:
        try:
            import pedalboard  # noqa: F401

            return True
        except ImportError:
            return False

    def process(self, input_path: str, output_path: str) -> str:
        """Process a WAV file through the Pedalboard effects chain.

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

        # Process through Pedalboard
        logger.info(
            f"Processing {input_path} with preset '{self.preset_name}' "
            f"({len(audio)} samples at {sample_rate}Hz)"
        )
        assert chain.board is not None, "Pedalboard board should be initialized"
        processed = chain.board(audio, sample_rate)

        # Apply mastering if requested
        if self.apply_mastering:
            from openmusic.effects.mastering import MasteringChain

            mastering = MasteringChain(target_lufs=self.target_lufs)
            processed = mastering.process(processed, sample_rate)

        # Write output
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, processed, sample_rate, format="WAV")
        logger.info(f"Processed audio written to {output_path}")

        return output_path
