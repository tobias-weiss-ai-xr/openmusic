"""Parameter automation primitives for evolving effects."""

from __future__ import annotations

import numpy as np


class Envelope:
    """Generate a parameter envelope over time."""

    def __init__(
        self,
        start: float,
        end: float,
        duration: int,
        curve: str = "linear",
    ):
        self.start = start
        self.end = end
        self.duration = duration
        self.curve = curve

    def generate(self) -> np.ndarray:
        """Return an array of `duration` values from start to end."""
        t = np.linspace(0.0, 1.0, self.duration)
        if self.curve == "linear":
            return self.start + (self.end - self.start) * t
        elif self.curve == "exponential":
            # Exponential interpolation (avoid log(0))
            s = max(self.start, 1e-10)
            e = max(self.end, 1e-10)
            log_vals = np.log(s) + (np.log(e) - np.log(s)) * t
            return np.exp(log_vals)
        elif self.curve == "sine":
            half_pi = np.linspace(0, np.pi / 2, self.duration)
            return self.start + (self.end - self.start) * np.sin(half_pi)
        else:
            raise ValueError(f"Unknown curve type: {self.curve}")


class LFO:
    """Low-frequency oscillator for parameter modulation."""

    def __init__(
        self,
        rate_hz: float = 0.1,
        depth: float = 0.1,
        center: float = 1.0,
        sample_rate: int = 48000,
    ):
        self.rate_hz = rate_hz
        self.depth = depth
        self.center = center
        self.sample_rate = sample_rate

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate LFO values for num_samples at sample_rate."""
        t = np.arange(num_samples) / self.sample_rate
        # Sine wave LFO
        wave = np.sin(2 * np.pi * self.rate_hz * t)
        return self.center + self.depth * wave


class RandomWalk:
    """Random walk parameter modulation within bounds."""

    def __init__(
        self,
        center: float = 1.0,
        max_deviation: float = 0.1,
        step_size: float = 0.01,
        seed: int | None = None,
    ):
        self.center = center
        self.max_deviation = max_deviation
        self.step_size = step_size
        self.rng = np.random.default_rng(seed)

    def generate(self, num_samples: int) -> np.ndarray:
        """Generate random walk values bounded by center +/- max_deviation."""
        values = np.empty(num_samples)
        values[0] = self.center
        lower = self.center - self.max_deviation
        upper = self.center + self.max_deviation

        for i in range(1, num_samples):
            step = self.rng.normal(0, self.step_size)
            new_val = values[i - 1] + step
            # Clamp to bounds
            values[i] = np.clip(new_val, lower, upper)

        return values
