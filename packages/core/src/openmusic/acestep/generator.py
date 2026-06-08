from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from openmusic.acestep.config import ACEStepConfig, GenerationParams
from openmusic.acestep.cache import CacheManager

try:
    import torch
except ImportError:
    torch = None


class ACEStepNotAvailableError(Exception):
    pass


class GPUOutOfMemoryError(Exception):
    pass


@dataclass
class GPUInfo:
    name: str
    vram_gb: float
    available: bool
    tier: int


class ACEStepGenerator:
    """Generates audio textures using the ACE-Step AI model."""

    def __init__(self, config: ACEStepConfig | None = None):
        self.config = config or ACEStepConfig()
        self.cache = CacheManager()
        self.device = self._detect_device()
        self._dit_handler = None
        self._llm_handler = None

    def _detect_device(self) -> str:
        if self.config.device != "auto":
            return self.config.device
        if torch is not None and torch.cuda.is_available():
            return "cuda"
        return "cpu"

    @classmethod
    def is_available(cls) -> bool:
        try:
            import acestep  # noqa: F401

            return True
        except ImportError:
            return False

    @classmethod
    def get_gpu_info(cls) -> dict:
        if torch is None or not torch.cuda.is_available():
            return {"name": "CPU", "vram_gb": 0, "available": False, "tier": 0}

        props = torch.cuda.get_device_properties(0)
        name = torch.cuda.get_device_name(0)
        vram_gb = props.total_memory / (1024**3)
        tier = cls._classify_gpu_tier(vram_gb)

        return {
            "name": name,
            "vram_gb": round(vram_gb, 1),
            "available": True,
            "tier": tier,
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

    def generate_texture(
        self,
        prompt: str,
        duration: int = 60,
        bpm: int = 125,
        key: str = "Am",
    ) -> Path:
        params_dict = {
            "bpm": bpm,
            "key": key,
            "duration": duration,
            "instrumental": True,
        }
        prompt_hash = self.cache.compute_hash(prompt, params_dict)

        cached = self.cache.get_cached(prompt_hash)
        if cached is not None:
            return cached

        return self._generate(prompt, params_dict, prompt_hash)

    def generate_chord_stab(self, key: str = "Am", quality: str = "warm") -> Path:
        prompt = f"dub techno chord stabs in {key}, {quality} tone with heavy reverb and delay"
        return self.generate_texture(prompt=prompt, duration=8, bpm=125, key=key)

    def _generate(self, prompt: str, params_dict: dict, prompt_hash: str) -> Path:
        if not self.is_available():
            raise ACEStepNotAvailableError(
                "ACE-Step is not installed. Install it from https://github.com/ace-step/ACE-Step-1.5"
            )

        import os
        import gc

        if self.device == "cuda":
            os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,max_split_size_mb:256")
            torch.cuda.empty_cache()
            gc.collect()

        from acestep.handler import AceStepHandler
        from acestep.llm_inference import LLMHandler
        from acestep.inference import (
            generate_music,
            GenerationParams as AceParams,
            GenerationConfig,
        )

        generation_device = self.device
        offload_to_cpu = self.device == "cuda"
        offload_dit_to_cpu = True

        dit_handler = AceStepHandler()
        llm_handler = LLMHandler()

        # Monkey-patch: force bfloat16 even on pre-Ampere GPUs (RTX 2060 = 7.5).
        # bf16 has the same exponent range as fp32 so SFT models don't NaN on VAE decode.
        from acestep import gpu_config as _acestep_gpu_config
        _orig_bfloat16_check = _acestep_gpu_config.cuda_supports_bfloat16
        _acestep_gpu_config.cuda_supports_bfloat16 = lambda device_index=None: True

        try:
            dit_handler.initialize_service(
                project_root="ACE-Step-1.5",
                config_path=self.config.model_path,
                device=generation_device,
                offload_to_cpu=offload_to_cpu,
                offload_dit_to_cpu=offload_dit_to_cpu,
            )
        finally:
            _acestep_gpu_config.cuda_supports_bfloat16 = _orig_bfloat16_check

        ace_params = AceParams(
            caption=prompt,
            bpm=params_dict.get("bpm"),
            duration=params_dict.get("duration", 30),
            instrumental=params_dict.get("instrumental", True),
            inference_steps=self.config.inference_steps,
            keyscale=params_dict.get("key", ""),
        )

        ace_config = GenerationConfig(
            batch_size=1,
            audio_format=self.config.audio_format,
        )

        save_dir = Path(self.cache.cache_dir) / "output"
        save_dir.mkdir(parents=True, exist_ok=True)

        def _run_generation(device: str, offload: bool) -> tuple:
            nonlocal dit_handler, llm_handler
            del dit_handler, llm_handler
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
            dit_handler = AceStepHandler()
            llm_handler = LLMHandler()
            from acestep import gpu_config as _agc
            _orig = _agc.cuda_supports_bfloat16
            _agc.cuda_supports_bfloat16 = lambda device_index=None: True
            try:
                dit_handler.initialize_service(
                    project_root="ACE-Step-1.5",
                    config_path=self.config.model_path,
                    device=device,
                    offload_to_cpu=offload,
                    offload_dit_to_cpu=offload,
                )
            finally:
                _agc.cuda_supports_bfloat16 = _orig
            return generate_music(
                dit_handler, llm_handler, ace_params, ace_config, save_dir=str(save_dir)
            )

        result = generate_music(
            dit_handler, llm_handler, ace_params, ace_config, save_dir=str(save_dir)
        )

        if not result.success and self.device == "cuda":
            fallback_reason = None
            if "CUDA out of memory" in (result.error or ""):
                fallback_reason = "CUDA out of memory"
            elif "NaN or Inf latents" in (result.error or ""):
                fallback_reason = "NaN/Inf latents (bf16 compatibility)"

            if fallback_reason:
                logger.warning(
                    f"{fallback_reason} during generation on CUDA. "
                    "Falling back to CPU generation (this will be slower but should succeed)."
                )
                result = _run_generation("cpu", False)
            else:
                raise RuntimeError(f"Generation failed: {result}")

        elif not result.success:
            if self.device == "cpu" or generation_device == "cpu":
                raise RuntimeError(
                    "Generation timed out on CPU. The ACE-Step model requires a GPU with at least 8GB VRAM.\n"
                    "Suggestions:\n"
                    "  - Use a machine with a compatible NVIDIA GPU\n"
                    "  - Reduce segment duration (e.g. --config with segment_duration: 30)\n"
                    "  - Use '--no-effects' to skip the effects processing pipeline"
                )
            raise RuntimeError(f"Generation failed: {result}")

        if result.success and result.audios:
            output_path = Path(result.audios[0]["path"])
            self.cache.set_cached(prompt_hash, output_path)
            return output_path

        raise RuntimeError(f"Generation failed: {result}")
