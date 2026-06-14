"""Tests for the shorts pipeline module — auto-positioning, category rotation, batch."""

import math

from openmusic.shorts.pipeline import (
    SHORT_CATEGORIES,
    ShortConfig,
    category_generator,
    auto_staggered_positions,
)
from openmusic.shorts.quotes import StoicQuote


class TestAutoStaggeredPositions:
    def test_single_position(self):
        """With count=1, returns midpoint."""
        result = auto_staggered_positions(3600.0, 1)
        assert len(result) == 1
        assert math.isclose(result[0], 1800.0)

    def test_even_spacing(self):
        """Positions are evenly spaced within margins."""
        result = auto_staggered_positions(3600.0, 6)
        assert len(result) == 6
        # First position should be ~ margin + step/2
        step = (3600.0 - 120.0) / 6
        assert math.isclose(result[0], 60.0 + step * 0.5, rel_tol=1e-6)
        # Last position should be near the end margin
        assert math.isclose(result[-1], 3600.0 - 60.0 - step * 0.5, rel_tol=1e-6)
        # All positions should be within [margin, mix_length - margin]
        for pos in result:
            assert 60.0 <= pos <= 3540.0

    def test_count_zero_returns_empty(self):
        assert auto_staggered_positions(3600.0, 0) == []

    def test_min_gap_respected(self):
        """Positions respect min_gap even for tight spacing."""
        result = auto_staggered_positions(600.0, 20, min_gap=30.0, margin=10.0)
        for i in range(1, len(result)):
            assert result[i] - result[i - 1] >= 29.9  # be tolerant of fp

    def test_short_mix(self):
        """Very short mix still produces requested count."""
        result = auto_staggered_positions(120.0, 3, margin=5.0, min_gap=10.0)
        assert len(result) == 3

    def test_custom_margin(self):
        result = auto_staggered_positions(3600.0, 4, margin=300.0)
        assert all(300.0 <= p <= 3300.0 for p in result)


class TestCategoryGenerator:
    def test_default_categories(self):
        gen = category_generator()
        first_round = [next(gen) for _ in range(len(SHORT_CATEGORIES))]
        assert first_round == SHORT_CATEGORIES

    def test_rotation_cycles(self):
        gen = category_generator(["stoic", "meditation"])
        results = [next(gen) for _ in range(6)]
        assert results == ["stoic", "meditation", "stoic", "meditation", "stoic", "meditation"]

    def test_single_category(self):
        gen = category_generator(["devops"])
        results = [next(gen) for _ in range(3)]
        assert results == ["devops", "devops", "devops"]

    def test_none_fallback_to_default(self):
        gen = category_generator(None)
        first = next(gen)
        assert first in SHORT_CATEGORIES


class TestShortConfig:
    def test_default_category(self):
        cfg = ShortConfig()
        assert cfg.category == "stoic"
        assert cfg.clip_duration == 30
        assert cfg.portrait is True

    def test_explicit_category(self):
        cfg = ShortConfig(category="meditation")
        assert cfg.category == "meditation"

    def test_devops_config(self):
        cfg = ShortConfig(category="devops", devops_seed=42)
        assert cfg.category == "devops"
        assert cfg.devops_seed == 42
