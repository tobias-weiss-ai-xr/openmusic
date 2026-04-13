"""Stable Audio Open generator wrapper for alternative audio generation."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StableAudioConfig:
    """Configuration for Stable Audio Open generation."""

    model_name: str = "stabilityai/stable-audio-open-1.0"
    sample_rate: int = 32000
    max_duration: int = 30  # seconds (max for Stable Audio Open)
    inference_steps: int = 50
    guidance_scale: float = 7.0
    device: str = "auto"


class StableAudioGenerator:
    """Generate audio textures using Stable Audio Open."""

    def __init__(self, config: StableAudioConfig | None = None):
        self.config = config or StableAudioConfig()
        self._model = None
        self._pipeline = None

    def _load_model(self):
        """Lazy-load the model on first use."""
        if self._model is not None:
            return

        try:
            import torch
            from diffusers import StableAudioPipeline

            device = self.config.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"

            self._pipeline = StableAudioPipeline.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            ).to(device)
            self._model = True
            logger.info(f"Loaded Stable Audio Open on {device}")
        except ImportError:
            raise ImportError(
                "diffusers and torch are required for Stable Audio Open. "
                "Install with: pip install diffusers torch"
            )

    def generate_texture(
        self,
        prompt: str,
        duration: int = 30,
        bpm: int = 125,
        key: str = "Dm",
    ) -> Path:
        """Generate an audio texture.

        Returns:
            Path to the generated WAV file.
        """
        self._load_model()

        import soundfile as sf
        import tempfile

        full_prompt = f"{prompt}, {key}, {bpm} BPM"
        logger.info(f"Generating with Stable Audio Open: {full_prompt[:80]}...")

        audio = self._pipeline(
            prompt=full_prompt,
            num_inference_steps=self.config.inference_steps,
            audio_length_in_s=min(duration, self.config.max_duration),
            guidance_scale=self.config.guidance_scale,
        )

        # audio is a tuple of (waveform, sample_rate)
        waveform = audio[0][0]  # first batch, first channel
        sr = self.config.sample_rate

        # Write to temp file
        path = tempfile.mktemp(suffix=".wav")
        sf.write(path, waveform, sr)
        logger.info(f"Generated: {path} ({len(waveform) / sr:.1f}s)")
        return Path(path)

    def is_available(self) -> bool:
        """Check if the generator can be loaded."""
        try:
            self._load_model()
            return True
        except (ImportError, Exception):
            return False
