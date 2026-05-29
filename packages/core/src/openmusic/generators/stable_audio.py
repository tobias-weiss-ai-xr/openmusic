import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from openmusic.generators.base import AudioGenerator

try:
    import torch
except ImportError:
    torch = None

logger = logging.getLogger(__name__)

_MAX_CONTIGUOUS_SECONDS = 44
_CROSSFADE_SECONDS = 1.0
_SAMPLE_RATE = 44100


def _is_stable_audio_available() -> bool:
    try:
        import stable_audio_tools  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class StableAudioConfig:
    device: str = "auto"
    inference_steps: int = 100
    cfg_scale: float = 7.0
    model_id: str = "stabilityai/stable-audio-open-1.0"
    model_path: str | None = None


class StableAudioGenerator:
    def __init__(self, config: StableAudioConfig | None = None):
        self.config = config or StableAudioConfig()
        self.device = self._resolve_device()
        self._model = None
        self._model_config = None

    def generate_texture(
        self,
        prompt: str,
        duration: int = 60,
        bpm: int = 125,
        key: str = "Am",
    ) -> Path:
        if not _is_stable_audio_available():
            raise RuntimeError(
                "stable-audio-tools is not installed. "
                "Install with: uv pip install stable-audio-tools"
            )

        model, model_config = self._get_model()

        condition_prompt = self._build_prompt(prompt, bpm, key)

        if duration <= _MAX_CONTIGUOUS_SECONDS:
            audio = self._generate_chunk(
                model, model_config, condition_prompt, duration
            )
        else:
            audio = self._generate_chunked(
                model, model_config, condition_prompt, duration
            )

        out = tempfile.NamedTemporaryFile(
            prefix="openmusic-sao-",
            suffix=".wav",
            delete=False,
        )
        out_path = Path(out.name)
        out.close()

        import soundfile as sf

        sf.write(str(out_path), audio, _SAMPLE_RATE)
        logger.info(
            "StableAudio generated %s (%.1fs, %d channels @ %dHz)",
            out_path,
            len(audio) / _SAMPLE_RATE,
            audio.ndim,
            _SAMPLE_RATE,
        )
        return out_path

    @classmethod
    def is_available(cls) -> bool:
        return _is_stable_audio_available()

    @classmethod
    def get_gpu_info(cls) -> dict:
        if torch is None or not torch.cuda.is_available():
            return {"name": "CPU", "vram_gb": 0, "available": False, "tier": 0}
        props = torch.cuda.get_device_properties(0)
        vram_gb = props.total_memory / (1024**3)
        return {
            "name": torch.cuda.get_device_name(0),
            "vram_gb": round(vram_gb, 1),
            "available": True,
            "tier": cls._classify_gpu_tier(vram_gb),
        }

    @staticmethod
    def _classify_gpu_tier(vram_gb: float) -> int:
        if vram_gb <= 4:
            return 1
        if vram_gb <= 6:
            return 2
        if vram_gb <= 8:
            return 3
        if vram_gb <= 12:
            return 4
        if vram_gb <= 16:
            return 5
        if vram_gb <= 20:
            return 6
        if vram_gb <= 24:
            return 7
        return 8

    def _resolve_device(self) -> str:
        if self.config.device != "auto":
            return self.config.device
        if torch is not None and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _get_model(self) -> tuple[object, dict]:
        if self._model is not None and self._model_config is not None:
            return self._model, self._model_config

        from stable_audio_tools import get_pretrained_model

        model_id = self.config.model_path or self.config.model_id
        logger.info("Loading Stable Audio Open model: %s", model_id)
        model, model_config = get_pretrained_model(model_id)
        model = model.to(self.device)
        model.eval()

        self._model = model
        self._model_config = model_config
        return model, model_config

    def _build_prompt(self, prompt: str, bpm: int, key: str) -> str:
        augmented = f"{prompt}, {bpm} BPM, key of {key}, dub techno"
        return augmented

    def _generate_chunk(
        self,
        model,
        model_config: dict,
        prompt: str,
        duration: int,
    ) -> np.ndarray:
        import torch
        from stable_audio_tools.inference.generation import generate_diffusion_cond
        from einops import rearrange

        sample_rate = model_config.get("sample_rate", _SAMPLE_RATE)
        sample_size = model_config.get("sample_size", 204800)

        conditioning = [
            {
                "prompt": prompt,
                "seconds_start": 0,
                "seconds_total": duration,
            }
        ]

        output = generate_diffusion_cond(
            model,
            steps=self.config.inference_steps,
            cfg_scale=self.config.cfg_scale,
            conditioning=conditioning,
            sample_size=sample_size,
            sample_rate=sample_rate,
            device=self.device,
        )

        audio = rearrange(output, "b d n -> d (b n)")
        audio = audio.to(torch.float32)
        peak = audio.abs().max()
        if peak > 0:
            audio = audio / peak
        return audio.cpu().numpy()

    def _generate_chunked(
        self,
        model,
        model_config: dict,
        prompt: str,
        total_duration: int,
    ) -> np.ndarray:
        sample_rate = _SAMPLE_RATE
        cf_samples = int(_CROSSFADE_SECONDS * sample_rate)
        chunk_dur = _MAX_CONTIGUOUS_SECONDS

        chunks: list[np.ndarray] = []

        pos = 0.0
        while pos < total_duration:
            remaining = total_duration - pos
            cur_dur = min(chunk_dur, remaining)

            logger.debug(
                "SAO chunk at pos=%.1f, dur=%.1f (total=%d)",
                pos,
                cur_dur,
                total_duration,
            )

            audio = self._generate_chunk(model, model_config, prompt, int(cur_dur))
            chunks.append(audio)
            pos += cur_dur - _CROSSFADE_SECONDS

        if len(chunks) == 1:
            return chunks[0]

        total_len = sum(c.shape[1] for c in chunks)
        total_len -= (len(chunks) - 1) * cf_samples

        channels = chunks[0].shape[0]
        combined = np.zeros((channels, total_len), dtype=np.float32)

        write_pos = 0
        for i, chunk in enumerate(chunks):
            chunk_len = chunk.shape[1]
            if i == 0:
                end = chunk_len - cf_samples
                combined[:, write_pos : write_pos + end] = chunk[:, :end]
                write_pos += end
            elif i == len(chunks) - 1:
                for j in range(cf_samples):
                    alpha = j / cf_samples
                    combined[:, write_pos - cf_samples + j] = (
                        (1 - alpha) * combined[:, write_pos - cf_samples + j]
                        + alpha * chunk[:, j]
                    )
                remaining = chunk_len - cf_samples
                combined[:, write_pos : write_pos + remaining] = chunk[:, cf_samples:]
            else:
                for j in range(cf_samples):
                    alpha = j / cf_samples
                    combined[:, write_pos - cf_samples + j] = (
                        (1 - alpha) * combined[:, write_pos - cf_samples + j]
                        + alpha * chunk[:, j]
                    )
                middle_len = chunk_len - 2 * cf_samples
                combined[:, write_pos : write_pos + middle_len] = chunk[
                    :, cf_samples : cf_samples + middle_len
                ]
                write_pos += middle_len

        return combined
