"""Tests for MixArranger class."""

import io
import math
import struct
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from openmusic.arrangement.mixer import MixArranger, load_audio, save_audio


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


class TestLoadAudio:
    def _make_wav_bytes(
        self, samples_16bit_stereo: np.ndarray, sample_rate: int = 48000
    ) -> bytes:
        """Create WAV bytes from int16 stereo array (n_samples, 2)."""
        buf = io.BytesIO()
        n_frames, n_channels = samples_16bit_stereo.shape
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples_16bit_stereo.astype(np.int16).tobytes())
        return buf.getvalue()

    def test_load_16bit_stereo(self, tmp_path):
        """16-bit stereo WAV → float64 array in [-1, 1]."""
        samples = np.array([[1000, -1000], [32767, -32768]], dtype=np.int16)
        wav_path = tmp_path / "test.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(samples.tobytes())
        wav_path.write_bytes(buf.getvalue())

        audio = load_audio(wav_path)
        assert audio.shape == (2, 2)
        assert audio.dtype == np.float64
        assert audio[0, 0] == pytest.approx(1000 / 32768.0)
        assert audio[0, 1] == pytest.approx(-1000 / 32768.0)
        assert audio[1, 0] == pytest.approx(32767 / 32768.0)
        assert audio[1, 1] == pytest.approx(-1.0)

    def test_load_8bit_mono(self, tmp_path):
        """8-bit unsigned WAV → float64 centered at 0."""
        samples = np.array([128, 0, 255], dtype=np.uint8)
        wav_path = tmp_path / "test8.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(1)
            wf.setframerate(48000)
            wf.writeframes(samples.tobytes())
        wav_path.write_bytes(buf.getvalue())

        audio = load_audio(wav_path)
        assert audio.shape == (3, 1)
        assert audio[0, 0] == pytest.approx(0.0)  # 128 centered
        assert audio[1, 0] == pytest.approx(-1.0)  # (0-128)/128
        assert audio[2, 0] == pytest.approx((255 - 128) / 128.0)

    def test_load_32bit_stereo(self, tmp_path):
        """32-bit WAV → float64 array."""
        samples = np.array([[0, 0], [2147483647, -2147483648]], dtype=np.int32)
        wav_path = tmp_path / "test32.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(4)
            wf.setframerate(48000)
            wf.writeframes(samples.tobytes())
        wav_path.write_bytes(buf.getvalue())

        audio = load_audio(wav_path)
        assert audio.shape == (2, 2)
        assert audio[1, 0] == pytest.approx(2147483647 / 2147483648.0)
        assert audio[1, 1] == pytest.approx(-1.0)

    def test_load_24bit_mono(self, tmp_path):
        """24-bit WAV → float64 array via manual unpacking."""
        # Create 24-bit samples: 0 and max positive
        raw = b"\x00\x00\x00"  # 0
        raw += b"\xff\xff\x7f"  # max positive 24-bit
        raw += b"\x00\x00\x80"  # -8388608 (most negative)
        wav_path = tmp_path / "test24.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(3)
            wf.setframerate(48000)
            wf.writeframes(raw)
        wav_path.write_bytes(buf.getvalue())

        audio = load_audio(wav_path)
        assert audio.shape == (3, 1)
        assert audio[0, 0] == pytest.approx(0.0)
        assert audio[1, 0] == pytest.approx(8388607 / 8388608.0)
        assert audio[2, 0] == pytest.approx(-1.0)

    def test_load_unsupported_width_raises(self, tmp_path):
        """Unsupported sample width raises ValueError."""
        mock_wf = MagicMock()
        mock_wf.getnchannels.return_value = 1
        mock_wf.getsampwidth.return_value = 5  # unsupported
        mock_wf.getframerate.return_value = 48000
        mock_wf.getnframes.return_value = 1
        mock_wf.readframes.return_value = b"\x00"
        mock_wf.__enter__ = lambda self: self
        mock_wf.__exit__ = MagicMock(return_value=False)

        with patch("wave.open", return_value=mock_wf):
            with pytest.raises(ValueError, match="Unsupported sample width"):
                load_audio("dummy.wav")


class TestSaveAudio:
    def test_save_stereo(self, tmp_path):
        """Stereo float64 array → 16-bit WAV file."""
        audio = np.array([[0.5, -0.5], [1.0, -1.0]], dtype=np.float64)
        out_path = tmp_path / "out.wav"
        save_audio(audio, out_path)

        assert out_path.exists()
        with wave.open(str(out_path), "rb") as wf:
            assert wf.getnchannels() == 2
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 48000
            frames = wf.readframes(2)
            samples = np.frombuffer(frames, dtype=np.int16).reshape(2, 2)
            assert samples[0, 0] == pytest.approx(16384, abs=1)
            assert samples[1, 0] == pytest.approx(32767, abs=1)

    def test_save_mono_1d(self, tmp_path):
        """Mono 1D array gets reshaped to (n, 1)."""
        audio = np.array([0.0, 0.5, -0.5, 1.0], dtype=np.float64)
        out_path = tmp_path / "mono.wav"
        save_audio(audio, out_path)

        with wave.open(str(out_path), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2

    def test_save_clips_values(self, tmp_path):
        """Values outside [-1, 1] are clipped."""
        audio = np.array([[2.0, -3.0]], dtype=np.float64)
        out_path = tmp_path / "clipped.wav"
        save_audio(audio, out_path)

        with wave.open(str(out_path), "rb") as wf:
            frames = wf.readframes(1)
            samples = np.frombuffer(frames, dtype=np.int16)
            assert samples[0] == 32767  # clipped to max
            assert samples[1] == -32767  # clipped: -3.0 * 32767
