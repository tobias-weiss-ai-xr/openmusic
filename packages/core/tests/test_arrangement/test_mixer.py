"""Tests for MixArranger class."""

import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from openmusic.arrangement.mixer import MixArranger


class TestMixArrangerInit:
    def test_default_sample_rate(self):
        arranger = MixArranger(bpm=125)
        assert arranger.bpm == 125
        assert arranger.sample_rate == 48000

    def test_custom_sample_rate(self):
        arranger = MixArranger(bpm=130, sample_rate=44100)
        assert arranger.bpm == 130
        assert arranger.sample_rate == 44100


class TestMixArrangerCrossfadeDuration:
    def test_crossfade_duration_at_125_bpm(self):
        """4 beats at 125 BPM = 4 * (60/125) = 1.92s."""
        arranger = MixArranger(bpm=125)
        assert arranger.get_crossfade_duration() == pytest.approx(1.92)

    def test_crossfade_duration_at_120_bpm(self):
        """4 beats at 120 BPM = 4 * (60/120) = 2.0s."""
        arranger = MixArranger(bpm=120)
        assert arranger.get_crossfade_duration() == pytest.approx(2.0)

    def test_crossfade_duration_at_130_bpm(self):
        """4 beats at 130 BPM = 4 * (60/130) ≈ 1.846s."""
        arranger = MixArranger(bpm=130)
        expected = 4 * 60 / 130
        assert arranger.get_crossfade_duration() == pytest.approx(expected)


class TestMixArrangerArrangementLength:
    def test_single_segment_no_crossfade(self):
        """1 segment = just its duration, no crossfade needed."""
        arranger = MixArranger(bpm=125)
        assert arranger.get_arrangement_length(1) == 180.0

    def test_two_segments_one_crossfade(self):
        """2 segments = 2 * 180 - 1 * crossfade_duration."""
        arranger = MixArranger(bpm=125)
        cf = arranger.get_crossfade_duration()
        expected = 2 * 180.0 - cf
        assert arranger.get_arrangement_length(2) == pytest.approx(expected)

    def test_three_segments_two_crossfades(self):
        """3 segments = 3 * 180 - 2 * crossfade_duration."""
        arranger = MixArranger(bpm=125)
        cf = arranger.get_crossfade_duration()
        expected = 3 * 180.0 - 2 * cf
        assert arranger.get_arrangement_length(3) == pytest.approx(expected)

    def test_40_segments(self):
        """40 segments for a 2-hour mix."""
        arranger = MixArranger(bpm=125)
        cf = arranger.get_crossfade_duration()
        expected = 40 * 180.0 - 39 * cf
        assert arranger.get_arrangement_length(40) == pytest.approx(expected)


class TestMixArrangerArrangeSegments:
    @patch("openmusic.arrangement.mixer.Path")
    @patch("openmusic.arrangement.mixer.load_audio")
    @patch("openmusic.arrangement.mixer.save_audio")
    def test_arrange_single_segment(self, mock_save, mock_load, mock_path):
        """Single segment should be saved as-is without crossfade."""
        audio = np.ones(48000 * 10, dtype=np.float32)  # 10s
        mock_load.return_value = audio
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        arranger = MixArranger(bpm=125)
        arranger.arrange_segments(["/tmp/seg1.wav"])

        mock_save.assert_called_once()

    @patch("openmusic.arrangement.mixer.Path")
    @patch("openmusic.arrangement.mixer.load_audio")
    @patch("openmusic.arrangement.mixer.save_audio")
    def test_arrange_two_segments_crossfades(self, mock_save, mock_load, mock_path):
        """Two segments should be crossfaded."""
        audio = np.ones(48000 * 10, dtype=np.float32)  # 10s
        mock_load.return_value = audio
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        arranger = MixArranger(bpm=125)
        arranger.arrange_segments(["/tmp/seg1.wav", "/tmp/seg2.wav"])

        mock_save.assert_called_once()
        # Verify the saved audio is shorter than sum (crossfade overlap)
        saved_audio = mock_save.call_args[0][0]
        total_samples = 2 * 48000 * 10
        cf_samples = int(arranger.get_crossfade_duration() * 48000)
        expected_samples = total_samples - cf_samples
        assert len(saved_audio) == expected_samples

    @patch("openmusic.arrangement.mixer.load_audio")
    @patch("openmusic.arrangement.mixer.save_audio")
    def test_arrange_returns_path(self, mock_save, mock_load):
        audio = np.ones(48000 * 5, dtype=np.float32)
        mock_load.return_value = audio

        arranger = MixArranger(bpm=125)
        result = arranger.arrange_segments(["/tmp/seg1.wav"])

        assert isinstance(result, Path)

    @patch("openmusic.arrangement.mixer.load_audio")
    def test_arrange_empty_list_raises(self, mock_load):
        arranger = MixArranger(bpm=125)
        with pytest.raises(ValueError, match="at least one"):
            arranger.arrange_segments([])
