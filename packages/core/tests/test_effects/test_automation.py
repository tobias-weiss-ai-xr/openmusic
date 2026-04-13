"""Tests for parameter automation primitives."""

import numpy as np
import pytest


class TestEnvelope:
    def test_linear_envelope_shape(self):
        from openmusic.effects.automation import Envelope

        env = Envelope(start=0.0, end=1.0, duration=100, curve="linear")
        values = env.generate()
        assert len(values) == 100
        assert values[0] == pytest.approx(0.0, abs=1e-6)
        assert values[-1] == pytest.approx(1.0, abs=1e-6)
        assert values[50] == pytest.approx(0.5, abs=0.1)

    def test_exponential_envelope_shape(self):
        from openmusic.effects.automation import Envelope

        env = Envelope(start=100.0, end=2000.0, duration=100, curve="exponential")
        values = env.generate()
        assert values[0] == pytest.approx(100.0, abs=1e-6)
        assert values[-1] == pytest.approx(2000.0, abs=1e-6)
        # Exponential: early values should be lower than linear midpoint
        assert values[25] < values[75]


class TestLFO:
    def test_lfo_periodicity(self):
        from openmusic.effects.automation import LFO

        lfo = LFO(rate_hz=1.0, depth=0.1, center=1.0, sample_rate=100)
        values = lfo.generate(num_samples=200)
        assert len(values) == 200
        # At 1Hz with 100 samples/sec, period = 100 samples
        # Values at 0 and 100 should be similar (one full cycle)
        assert values[0] == pytest.approx(values[100], abs=0.01)


class TestRandomWalk:
    def test_random_walk_bounds(self):
        from openmusic.effects.automation import RandomWalk

        rw = RandomWalk(center=500.0, max_deviation=100.0, step_size=10.0)
        values = rw.generate(num_samples=1000)
        assert len(values) == 1000
        assert all(v >= 400.0 for v in values)
        assert all(v <= 600.0 for v in values)

    def test_random_walk_starts_at_center(self):
        from openmusic.effects.automation import RandomWalk

        rw = RandomWalk(center=100.0, max_deviation=50.0, step_size=5.0)
        values = rw.generate(num_samples=1)
        assert values[0] == pytest.approx(100.0, abs=1e-6)
