"""Tests for analysis.beat_tracker module."""

import numpy as np
import pytest

pytest.importorskip("aubio", reason="aubio is not installed (optional dep for beat tracking)")

from openmusic.analysis.beat_tracker import (
    detect_tempo,
    detect_beats,
    validate_tempo_match,
    BEAT_TRACKING_METHODS,
)


# Fixture: 10 seconds of 125 BPM click track (quarter notes)
@pytest.fixture(scope="module")
def click_track_125bpm():
    """Generate a click track at 125 BPM for tempo detection testing."""
    sr = 48000
    duration = 10.0
    bpm = 125.0
    beat_interval = 60.0 / bpm  # ~0.48 seconds
    audio = np.zeros(int(sr * duration))
    for beat_idx in range(int(duration / beat_interval)):
        sample = int(beat_idx * beat_interval * sr)
        if sample < len(audio):
            click_len = int(0.01 * sr)
            end = min(sample + click_len, len(audio))
            click_env = np.hanning(end - sample) * 0.5
            audio[sample:end] = click_env
    return audio, sr, bpm


class TestDetectTempo:
    def test_detects_125bpm_from_click_track(self, click_track_125bpm):
        audio, sr, expected_bpm = click_track_125bpm
        detected = detect_tempo(audio, sr)
        assert detected is not None
        assert abs(detected - expected_bpm) < 5.0

    def test_returns_float(self, click_track_125bpm):
        audio, sr, _ = click_track_125bpm
        result = detect_tempo(audio, sr)
        assert isinstance(result, float) or result is None

    def test_silence_returns_none(self):
        audio = np.zeros(48000 * 3)
        result = detect_tempo(audio, 48000)
        assert result is None

    def test_supports_stereo(self, click_track_125bpm):
        audio, sr, expected_bpm = click_track_125bpm
        stereo = np.column_stack([audio, audio])
        detected = detect_tempo(stereo, sr)
        assert detected is not None
        assert abs(detected - expected_bpm) < 5.0

    def test_short_audio_returns_none(self):
        audio = np.random.randn(7999)
        result = detect_tempo(audio, 8000)
        assert result is None

    def test_unknown_method_raises(self):
        audio = np.random.randn(48000 * 3)
        with pytest.raises(ValueError, match="Unknown method"):
            detect_tempo(audio, 48000, method="invalid")

    def test_beat_methods_list_not_empty(self):
        assert len(BEAT_TRACKING_METHODS) > 0
        assert "default" in BEAT_TRACKING_METHODS

    def test_3d_audio_raises_value_error(self):
        audio = np.random.randn(48000, 2, 2)
        with pytest.raises(ValueError, match="Expected 1D or 2D"):
            detect_tempo(audio, 48000)


class TestDetectBeats:
    def test_returns_beat_times(self, click_track_125bpm):
        audio, sr, _ = click_track_125bpm
        beats = detect_beats(audio, sr)
        assert isinstance(beats, list)
        assert len(beats) > 0
        for t in beats:
            assert isinstance(t, float)
            assert 0 <= t <= (len(audio) / sr)

    def test_beat_count_matches_bpm(self, click_track_125bpm):
        audio, sr, bpm = click_track_125bpm
        duration = len(audio) / sr
        expected_beats = int(duration * bpm / 60)
        beats = detect_beats(audio, sr)
        assert len(beats) > 0
        assert len(beats) > expected_beats * 0.2

    def test_empty_for_silence(self):
        audio = np.zeros(48000 * 3)
        beats = detect_beats(audio, 48000)
        assert beats == []

    def test_short_audio_returns_empty_list(self):
        audio = np.random.randn(7999)
        beats = detect_beats(audio, 8000)
        assert beats == []


class TestValidateTempoMatch:
    def test_exact_match(self):
        assert validate_tempo_match(125.0, 125.0, tolerance=2.0) is True

    def test_within_tolerance(self):
        assert validate_tempo_match(124.0, 125.0, tolerance=2.0) is True

    def test_outside_tolerance(self):
        assert validate_tempo_match(120.0, 125.0, tolerance=2.0) is False

    def test_none_detected(self):
        assert validate_tempo_match(None, 125.0) is False
