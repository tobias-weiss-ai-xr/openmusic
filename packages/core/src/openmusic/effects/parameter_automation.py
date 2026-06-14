"""Parameter automation effect - applies envelopes and LFOs to audio parameters."""
from typing import Any, Dict
import numpy as np
from .base import Effect
from .automation import Envelope, LFO, RandomWalk

class ParameterAutomation(Effect):
    """Modulates audio using parameter automation primitives.

    Applies gain/pan/filter envelopes to create evolving sound over time.
    """

    def __init__(self):
        self.name = "parameter_automation"

    def process(self, audio: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        auto_type = str(params.get("auto_type", "gain_envelope"))
        sample_rate = int(params.get("sample_rate", 48000))
        num_samples = len(audio) if audio.ndim == 1 else audio.shape[-1]

        if auto_type == "gain_envelope":
            start = float(params.get("start", 0.0))
            end = float(params.get("end", 1.0))
            curve = str(params.get("curve", "linear"))
            env = Envelope(start, end, num_samples, curve)
            curve_vals = env.generate()
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals

        elif auto_type == "tremolo":
            rate_hz = float(params.get("rate_hz", 2.0))
            depth = float(params.get("depth", 0.5))
            lfo = LFO(rate_hz=rate_hz, depth=depth, center=1.0, sample_rate=sample_rate)
            curve_vals = lfo.generate(num_samples)
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals

        elif auto_type == "random_walk_gain":
            center = float(params.get("center", 1.0))
            max_dev = float(params.get("max_deviation", 0.2))
            step = float(params.get("step_size", 0.01))
            rw = RandomWalk(center=center, max_deviation=max_dev, step_size=step)
            curve_vals = rw.generate(num_samples)
            if audio.ndim > 1:
                return audio * curve_vals[np.newaxis, :]
            return audio * curve_vals

        return audio.copy()
