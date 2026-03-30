"""Tests for barrel exports from acestep module."""

from openmusic.acestep import (
    ACEStepConfig,
    GenerationParams,
    CacheManager,
    ACEStepGenerator,
    ACEStepNotAvailableError,
    GPUOutOfMemoryError,
)


class TestBarrelExports:
    """Verify all public classes are exported."""

    def test_config_exported(self):
        assert ACEStepConfig is not None

    def test_generation_params_exported(self):
        assert GenerationParams is not None

    def test_cache_manager_exported(self):
        assert CacheManager is not None

    def test_generator_exported(self):
        assert ACEStepGenerator is not None

    def test_errors_exported(self):
        assert ACEStepNotAvailableError is not None
        assert GPUOutOfMemoryError is not None
