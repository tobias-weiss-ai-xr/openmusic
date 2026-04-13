"""Build Pedalboard effects chains from preset configs."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from pedalboard import (
        Pedalboard,
        Reverb,
        Delay,
        Chorus,
        Phaser,
        Distortion,
        Compressor,
        Gain,
        HighShelfFilter,
        LowShelfFilter,
        PeakFilter,
        HighpassFilter,
        LowpassFilter,
    )

    HAS_PEDALBOARD = True
except ImportError:
    HAS_PEDALBOARD = False

# Preset definitions mapping to Pedalboard objects
PRESETS: dict[str, dict] = {
    "deep_dub": {
        "filter_cutoff_hz": 600.0,
        "filter_q": 3.0,
        "delay_seconds": 0.375,
        "delay_feedback": 0.5,
        "delay_mix": 0.6,
        "reverb_room_size": 0.8,
        "reverb_damping": 0.3,
        "reverb_wet": 0.5,
        "reverb_dry": 0.7,
        "distortion_drive": 0.2,
        "chorus_rate_hz": 0.1,
        "chorus_depth": 0.3,
        "output_gain_db": -3.0,
    },
    "minimal_dub": {
        "filter_cutoff_hz": 900.0,
        "filter_q": 2.0,
        "delay_seconds": 0.375,
        "delay_feedback": 0.3,
        "delay_mix": 0.35,
        "reverb_room_size": 0.5,
        "reverb_damping": 0.5,
        "reverb_wet": 0.25,
        "reverb_dry": 0.8,
        "distortion_drive": 0.1,
        "chorus_rate_hz": 0.2,
        "chorus_depth": 0.15,
        "output_gain_db": -3.0,
    },
    "club_dub": {
        "filter_cutoff_hz": 1000.0,
        "filter_q": 2.5,
        "delay_seconds": 0.3,
        "delay_feedback": 0.35,
        "delay_mix": 0.4,
        "reverb_room_size": 0.6,
        "reverb_damping": 0.4,
        "reverb_wet": 0.3,
        "reverb_dry": 0.75,
        "distortion_drive": 0.25,
        "chorus_rate_hz": 0.3,
        "chorus_depth": 0.2,
        "output_gain_db": -2.0,
    },
}


@dataclass
class PedalboardEffectsChain:
    """Configured Pedalboard effects chain from a preset."""

    preset_name: str
    board: Pedalboard | None = None

    def __post_init__(self):
        if not HAS_PEDALBOARD:
            raise ImportError(
                "pedalboard is required. Install with: pip install pedalboard"
            )
        if self.preset_name not in PRESETS:
            raise ValueError(
                f"Unknown preset '{self.preset_name}'. Available: {sorted(PRESETS)}"
            )
        self.board = self._build_chain(PRESETS[self.preset_name])

    def _build_chain(self, p: dict) -> Pedalboard:
        """Build a Pedalboard chain from preset parameters."""
        return Pedalboard(
            [
                HighpassFilter(cutoff_frequency_hz=30.0),
                LowpassFilter(
                    cutoff_frequency_hz=p["filter_cutoff_hz"], q=p["filter_q"]
                ),
                Delay(
                    delay_seconds=p["delay_seconds"],
                    feedback=p["delay_feedback"],
                    mix=p["delay_mix"],
                ),
                Reverb(
                    room_size=p["reverb_room_size"],
                    damping=p["reverb_damping"],
                    wet_level=p["reverb_wet"],
                    dry_level=p["reverb_dry"],
                ),
                Chorus(rate_hz=p["chorus_rate_hz"], depth=p["chorus_depth"]),
                Distortion(drive_db=p["distortion_drive"] * 20),
                Gain(gain_db=p["output_gain_db"]),
            ]
        )
