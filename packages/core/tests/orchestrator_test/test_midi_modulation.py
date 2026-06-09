import pytest
from openmusic.orchestrator.midi_modulation import (
    generate_modulation_pattern,
    midi_to_modulation_values,
    get_modulation_for_segment,
    ModulationPattern,
)


class TestModulationPattern:

    def test_generates_16_step_pattern(self):
        pattern = generate_modulation_pattern(bpm=125, steps=16)
        assert len(pattern.velocities) <= 16
        assert len(pattern.timings) == len(pattern.velocities)
        assert all(v >= 0 and v <= 127 for v in pattern.velocities)
        assert all(t >= 0 for t in pattern.timings)

    def test_midi_to_modulation_returns_values_in_range(self):
        pattern = ModulationPattern(
            velocities=[64, 100, 32, 80],
            timings=[0.0, 0.5, 1.0, 1.5],
        )
        mod = midi_to_modulation_values(pattern, target_range=(0.0, 1.0))
        assert len(mod) == 4
        assert all(v >= 0.0 and v <= 1.0 for v in mod)

    def test_modulation_differs_per_segment(self):
        mod_a = get_modulation_for_segment(0, 40, bpm=125)
        mod_b = get_modulation_for_segment(5, 40, bpm=125)
        assert mod_a["delay_feedback_mod"] != mod_b["delay_feedback_mod"]

    def test_modulation_contains_expected_keys(self):
        mod = get_modulation_for_segment(10, 40, bpm=125)
        assert "delay_feedback_mod" in mod
        assert "reverb_mix_mod" in mod
        assert "filter_cutoff_mod" in mod

    def test_values_within_expected_ranges(self):
        mod = get_modulation_for_segment(3, 40, bpm=125)
        assert 0.2 <= mod["delay_feedback_mod"] <= 0.8
        assert 0.3 <= mod["reverb_mix_mod"] <= 0.8
        assert 200 <= mod["filter_cutoff_mod"] <= 2000
