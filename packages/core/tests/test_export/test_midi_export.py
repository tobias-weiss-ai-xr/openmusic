"""Tests for export.midi_export module."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from openmusic.export.midi_export import (
    export_pattern_to_midi,
    export_markov_chain_to_midi,
    pattern_to_isobar_sequence,
    DEFAULT_MIDI_TEMPO,
)


class TestExportPatternToMidi:
    def test_returns_path(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64, 67, 72],
                output_path=out_path,
                bpm=125,
            )
            assert result == out_path
            assert out_path.exists()
            assert out_path.stat().st_size > 20
        finally:
            out_path.unlink(missing_ok=True)

    def test_custom_velocity(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64],
                output_path=out_path,
                velocities=[100, 80],
            )
            assert result.exists()
        finally:
            out_path.unlink(missing_ok=True)

    def test_empty_pattern_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="empty"):
                export_pattern_to_midi([], output_path=out_path)
        finally:
            out_path.unlink(missing_ok=True)

    def test_velocity_count_mismatch_raises(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="same length"):
                export_pattern_to_midi(
                    [60, 64, 67], output_path=out_path, velocities=[100]
                )
        finally:
            out_path.unlink(missing_ok=True)

    def test_generates_valid_midi_header(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            export_pattern_to_midi([60, 64, 67], output_path=out_path)
            raw = out_path.read_bytes()
            assert raw[:4] == b"MThd"  # Standard MIDI header
        finally:
            out_path.unlink(missing_ok=True)

    def test_with_durations(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=[60, 64, 67],
                output_path=out_path,
                durations=[1.0, 0.5, 2.0],
            )
            assert result.exists()
        finally:
            out_path.unlink(missing_ok=True)

    def test_note_names_accepted(self):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_pattern_to_midi(
                note_values=["C4", "Eb4", "G4"],
                output_path=out_path,
            )
            assert result.exists()
            raw = out_path.read_bytes()
            assert raw[:4] == b"MThd"
        finally:
            out_path.unlink(missing_ok=True)


class TestPatternToIsobarSequence:
    def test_returns_line(self):
        try:
            from isobar import Line  # noqa: F401
        except ImportError:
            pytest.skip("isobar not installed")
        seq = pattern_to_isobar_sequence([60, 62, 64])
        assert seq is not None

    def test_empty_returns_none(self):
        result = pattern_to_isobar_sequence([])
        assert result is None


class TestExportMarkovChainToMidi:
    @pytest.fixture
    def markov_states(self):
        return {
            "C3": {"Eb3": 0.5, "G3": 0.5},
            "Eb3": {"F3": 0.7, "G3": 0.3},
            "F3": {"G3": 0.4, "Eb3": 0.6},
            "G3": {"C3": 0.8, "F3": 0.2},
        }

    def test_returns_path(self, markov_states):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            result = export_markov_chain_to_midi(
                transitions=markov_states,
                output_path=out_path,
                steps=16,
            )
            assert result == out_path
            assert out_path.exists()
        finally:
            out_path.unlink(missing_ok=True)

    def test_respects_step_count(self, markov_states):
        with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
            out_path = Path(f.name)
        try:
            export_markov_chain_to_midi(
                transitions=markov_states,
                output_path=out_path,
                steps=8,
            )
            assert out_path.exists()
        finally:
            out_path.unlink(missing_ok=True)
