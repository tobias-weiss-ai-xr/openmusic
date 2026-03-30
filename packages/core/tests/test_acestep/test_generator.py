"""Tests for ACEStepGenerator with mocked model."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from openmusic.acestep.config import ACEStepConfig, GenerationParams
from openmusic.acestep.generator import ACEStepGenerator
from openmusic.acestep.cache import CacheManager


class TestACEStepGeneratorInit:
    """Tests for ACEStepGenerator initialization."""

    @patch("openmusic.acestep.generator.torch")
    def test_init_auto_detects_gpu(self, mock_torch):
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "RTX 3060"
        mock_torch.cuda.get_device_properties.return_value = MagicMock(
            total_memory=12 * 1024**3
        )

        gen = ACEStepGenerator(ACEStepConfig(device="auto"))
        assert gen.device == "cuda"

    @patch("openmusic.acestep.generator.torch")
    def test_init_falls_back_to_cpu_when_no_gpu(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False

        gen = ACEStepGenerator(ACEStepConfig(device="auto"))
        assert gen.device == "cpu"

    @patch("openmusic.acestep.generator.torch")
    def test_init_uses_explicit_device(self, mock_torch):
        mock_torch.cuda.is_available.return_value = True

        gen = ACEStepGenerator(ACEStepConfig(device="cpu"))
        assert gen.device == "cpu"

    @patch("openmusic.acestep.generator.torch")
    def test_init_stores_config(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False
        config = ACEStepConfig(model_path="custom-model", audio_format="wav")

        gen = ACEStepGenerator(config)
        assert gen.config.model_path == "custom-model"
        assert gen.config.audio_format == "wav"


class TestIsAvailable:
    """Tests for ACEStepGenerator.is_available class method."""

    @patch.dict(sys.modules, {"acestep": MagicMock(), "acestep.inference": MagicMock()})
    def test_available_when_module_importable(self):
        assert ACEStepGenerator.is_available() is True

    @patch.dict(sys.modules, {}, clear=False)
    def test_unavailable_when_module_missing(self):
        # Temporarily remove acestep from importable modules
        import importlib

        saved = sys.modules.get("acestep")
        sys.modules.pop("acestep", None)
        try:
            result = ACEStepGenerator.is_available()
            assert result is False
        finally:
            if saved is not None:
                sys.modules["acestep"] = saved


class TestGetGPUInfo:
    """Tests for GPU info detection."""

    @patch("openmusic.acestep.generator.torch")
    def test_gpu_info_returns_tier_and_details(self, mock_torch):
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "RTX 2060"
        mock_torch.cuda.get_device_properties.return_value = MagicMock(
            total_memory=6 * 1024**3
        )

        info = ACEStepGenerator.get_gpu_info()
        assert info["name"] == "RTX 2060"
        assert info["vram_gb"] == pytest.approx(6.0, abs=0.1)
        assert info["available"] is True
        assert info["tier"] == 2

    @patch("openmusic.acestep.generator.torch")
    def test_gpu_info_tier1_under_4gb(self, mock_torch):
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "GTX 1650"
        mock_torch.cuda.get_device_properties.return_value = MagicMock(
            total_memory=4 * 1024**3
        )

        info = ACEStepGenerator.get_gpu_info()
        assert info["tier"] == 1

    @patch("openmusic.acestep.generator.torch")
    def test_gpu_info_tier4_8_12gb(self, mock_torch):
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_name.return_value = "RTX 3060"
        mock_torch.cuda.get_device_properties.return_value = MagicMock(
            total_memory=10 * 1024**3
        )

        info = ACEStepGenerator.get_gpu_info()
        assert info["tier"] == 4

    @patch("openmusic.acestep.generator.torch")
    def test_gpu_info_no_gpu(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False

        info = ACEStepGenerator.get_gpu_info()
        assert info["available"] is False
        assert info["name"] == "CPU"
        assert info["tier"] == 0


class TestGenerateTexture:
    """Tests for generate_texture method."""

    @patch("openmusic.acestep.generator.torch")
    def test_generate_texture_returns_wav_path(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False

        gen = ACEStepGenerator(ACEStepConfig())

        with patch.object(gen, "_generate") as mock_generate:
            mock_generate.return_value = Path("/output/texture.wav")
            result = gen.generate_texture(
                prompt="dub techno textures",
                duration=60,
                bpm=125,
                key="Am",
            )
            assert result == Path("/output/texture.wav")
            mock_generate.assert_called_once()

    @patch("openmusic.acestep.generator.torch")
    def test_generate_texture_uses_cache(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False

        gen = ACEStepGenerator(ACEStepConfig())

        with (
            patch.object(gen.cache, "compute_hash") as mock_hash,
            patch.object(gen.cache, "get_cached") as mock_get,
        ):
            mock_hash.return_value = "cached_hash"
            mock_get.return_value = Path("/cached/output.wav")

            result = gen.generate_texture(prompt="cached prompt", duration=30)
            assert result == Path("/cached/output.wav")
            mock_hash.assert_called_once()


class TestGenerateChordStab:
    """Tests for generate_chord_stab method."""

    @patch("openmusic.acestep.generator.torch")
    def test_generate_chord_stab_constructs_prompt(self, mock_torch):
        mock_torch.cuda.is_available.return_value = False

        gen = ACEStepGenerator(ACEStepConfig())

        with patch.object(gen, "generate_texture") as mock_texture:
            mock_texture.return_value = Path("/output/stab.wav")
            gen.generate_chord_stab(key="Am", quality="warm")

            mock_texture.assert_called_once()
            call_kwargs = mock_texture.call_args[1]
            assert "Am" in call_kwargs["key"]
            assert call_kwargs["bpm"] == 125


class TestErrors:
    """Tests for custom error classes."""

    def test_ace_step_not_available_error(self):
        from openmusic.acestep import ACEStepNotAvailableError

        with pytest.raises(ACEStepNotAvailableError):
            raise ACEStepNotAvailableError("ACE-Step not installed")

    def test_gpu_out_of_memory_error(self):
        from openmusic.acestep import GPUOutOfMemoryError

        with pytest.raises(GPUOutOfMemoryError):
            raise GPUOutOfMemoryError("VRAM too low: 2GB")
