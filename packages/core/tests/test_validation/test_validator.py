import json
import os
import sys
import math
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "scripts")
)

import validate_mix as vm

GOOD_FFPROBE_JSON = json.dumps(
    {
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "flac",
                "sample_rate": "48000",
                "channels": 2,
                "bits_per_sample": 24,
            }
        ],
        "format": {
            "format_name": "flac",
            "duration": "7200.000000",
            "size": "86400000",
        },
    }
)

GOOD_SOX_STAT = """\
Samples read:           691200000
Length (seconds):     7200.000000
Scaled by:         2147483647.0
Maximum amplitude:     0.891251
Minimum amplitude:    -0.891251
Midline amplitude:    -0.000000
Mean    norm:          0.158489
Mean    amplitude:     0.158489
RMS     amplitude:     0.158489
RMS     dB:            -16.0000
Maximum delta:         0.000000
Minimum delta:         0.000000
Mean    delta:         0.000000
RMS     delta:         0.000000
Rough   frequency:          0
Volume adjustment:        1.124
"""

CLIPPED_SOX_STAT = GOOD_SOX_STAT.replace(
    "Maximum amplitude:     0.891251",
    "Maximum amplitude:     0.999000",
)

LOUD_SOX_STAT = GOOD_SOX_STAT.replace(
    "RMS     dB:            -16.0000",
    "RMS     dB:            -12.0000",
)

QUIET_SOX_STAT = GOOD_SOX_STAT.replace(
    "RMS     dB:            -16.0000",
    "RMS     dB:            -22.0000",
)

WRONG_RATE_FFPROBE = json.dumps(
    {
        "streams": [
            {
                "codec_type": "audio",
                "sample_rate": "44100",
                "channels": 2,
            }
        ],
        "format": {
            "format_name": "flac",
            "duration": "7200.000000",
            "size": "86400000",
        },
    }
)

WRONG_CHANNELS_FFPROBE = json.dumps(
    {
        "streams": [
            {
                "codec_type": "audio",
                "sample_rate": "48000",
                "channels": 1,
            }
        ],
        "format": {
            "format_name": "flac",
            "duration": "7200.000000",
            "size": "86400000",
        },
    }
)

SHORT_DURATION_FFPROBE = json.dumps(
    {
        "streams": [
            {
                "codec_type": "audio",
                "sample_rate": "48000",
                "channels": 2,
            }
        ],
        "format": {
            "format_name": "flac",
            "duration": "3600.000000",
            "size": "43200000",
        },
    }
)

WAV_FFPROBE = json.dumps(
    {
        "streams": [
            {
                "codec_type": "audio",
                "sample_rate": "48000",
                "channels": 2,
            }
        ],
        "format": {
            "format_name": "wav",
            "duration": "7200.000000",
            "size": "2073600000",
        },
    }
)


def _mock_subprocess(ffprobe_json, sox_stat="", file_exists=True, file_size=None):
    def side_effect(cmd, **kwargs):
        proc = MagicMock()
        proc.returncode = 0
        if cmd[0] == "ffprobe":
            proc.stdout = ffprobe_json
            proc.stderr = ""
        elif cmd[0] == "sox":
            proc.stdout = ""
            proc.stderr = sox_stat
        else:
            proc.returncode = 1
            proc.stderr = f"Unknown command: {cmd[0]}"
        return proc

    return side_effect


class TestDurationCheck:
    def test_duration_within_tolerance_passes(self):
        result = vm.check_duration(7200.0, 7200.0, 5.0)
        assert result.passed is True

    def test_duration_at_exact_upper_bound_passes(self):
        result = vm.check_duration(7560.0, 7200.0, 5.0)
        assert result.passed is True

    def test_duration_at_exact_lower_bound_passes(self):
        result = vm.check_duration(6840.0, 7200.0, 5.0)
        assert result.passed is True

    def test_duration_just_over_tolerance_fails(self):
        result = vm.check_duration(7561.0, 7200.0, 5.0)
        assert result.passed is False

    def test_duration_just_under_tolerance_fails(self):
        result = vm.check_duration(6839.0, 7200.0, 5.0)
        assert result.passed is False

    def test_duration_zero_actual_fails(self):
        result = vm.check_duration(0.0, 7200.0, 5.0)
        assert result.passed is False

    def test_custom_duration_override(self):
        result = vm.check_duration(3600.0, 3600.0, 5.0)
        assert result.passed is True
        result = vm.check_duration(3600.0, 7200.0, 5.0)
        assert result.passed is False

    def test_short_duration_against_long_target(self):
        result = vm.check_duration(60.0, 7200.0, 5.0)
        assert result.passed is False


class TestSampleRateCheck:
    def test_correct_sample_rate_passes(self):
        result = vm.check_sample_rate(48000)
        assert result.passed is True

    def test_wrong_sample_rate_fails(self):
        result = vm.check_sample_rate(44100)
        assert result.passed is False

    def test_high_sample_rate_fails(self):
        result = vm.check_sample_rate(96000)
        assert result.passed is False


class TestChannelsCheck:
    def test_stereo_passes(self):
        result = vm.check_channels(2)
        assert result.passed is True

    def test_mono_fails(self):
        result = vm.check_channels(1)
        assert result.passed is False

    def test_surround_fails(self):
        result = vm.check_channels(6)
        assert result.passed is False


class TestFormatCheck:
    def test_flac_passes(self):
        result = vm.check_format("flac", "mix.flac")
        assert result.passed is True
        assert result.value == "FLAC"

    def test_wav_passes(self):
        result = vm.check_format("wav", "mix.wav")
        assert result.passed is True

    def test_wave_passes(self):
        result = vm.check_format("wave", "mix.wave")
        assert result.passed is True

    def test_mp3_fails(self):
        result = vm.check_format("mp3", "mix.mp3")
        assert result.passed is False

    def test_compound_format_name_passes(self):
        result = vm.check_format("matroska,flac", "mix.flac")
        assert result.passed is True

    def test_unknown_format_falls_back_to_extension(self):
        result = vm.check_format("unknown", "mix.flac")
        assert result.passed is True


class TestRmsLevelCheck:
    def test_rms_at_target_passes(self):
        result = vm.check_rms_level(-16.0)
        assert result.passed is True

    def test_rms_at_lower_bound_passes(self):
        result = vm.check_rms_level(-18.0)
        assert result.passed is True

    def test_rms_at_upper_bound_passes(self):
        result = vm.check_rms_level(-14.0)
        assert result.passed is True

    def test_rms_below_range_fails(self):
        result = vm.check_rms_level(-20.0)
        assert result.passed is False

    def test_rms_above_range_fails(self):
        result = vm.check_rms_level(-10.0)
        assert result.passed is False

    def test_rms_none_fails(self):
        result = vm.check_rms_level(None)
        assert result.passed is False


class TestPeakLevelCheck:
    def test_clean_peak_passes(self):
        result = vm.check_peak_level(0.891251)
        assert result.passed is True

    def test_very_low_peak_passes(self):
        result = vm.check_peak_level(0.5)
        assert result.passed is True

    def test_clipping_peak_fails(self):
        result = vm.check_peak_level(0.999)
        assert result.passed is False

    def test_exactly_at_threshold_fails(self):
        threshold = vm.PEAK_MAX_AMPLITUDE
        result = vm.check_peak_level(threshold)
        assert result.passed is False

    def test_just_below_threshold_passes(self):
        threshold = vm.PEAK_MAX_AMPLITUDE
        result = vm.check_peak_level(threshold - 0.0001)
        assert result.passed is True

    def test_peak_none_fails(self):
        result = vm.check_peak_level(None)
        assert result.passed is False


class TestAmplitudeToDb:
    def test_unity_is_zero_db(self):
        assert vm.amplitude_to_db(1.0) == 0.0

    def test_half_is_about_minus_6db(self):
        assert abs(vm.amplitude_to_db(0.5) - (-6.0206)) < 0.01

    def test_zero_is_negative_infinity(self):
        assert vm.amplitude_to_db(0.0) == float("-inf")

    def test_negative_amplitude_is_inf(self):
        assert vm.amplitude_to_db(-1.0) == float("-inf")


class TestFileSizeCheck:
    def test_reasonable_size_passes(self, tmp_path):
        f = tmp_path / "test.flac"
        f.write_bytes(b"\x00" * 86_400_000)
        result = vm.check_file_size(str(f), 7200.0)
        assert result.passed is True

    def test_too_small_fails(self, tmp_path):
        f = tmp_path / "test.flac"
        f.write_bytes(b"\x00" * 100)
        result = vm.check_file_size(str(f), 7200.0)
        assert result.passed is False


class TestParseSoxStat:
    def test_parse_rms_db(self):
        rms = vm.parse_sox_rms_db(GOOD_SOX_STAT)
        assert rms == pytest.approx(-16.0)

    def test_parse_peak_amplitude(self):
        peak = vm.parse_sox_peak_amplitude(GOOD_SOX_STAT)
        assert peak == pytest.approx(0.891251)

    def test_parse_rms_from_empty(self):
        assert vm.parse_sox_rms_db("") is None

    def test_parse_peak_from_empty(self):
        assert vm.parse_sox_peak_amplitude("") is None


class TestParseFfprobe:
    def test_parse_duration(self):
        probe = json.loads(GOOD_FFPROBE_JSON)
        assert vm.parse_ffprobe_duration(probe) == 7200.0

    def test_parse_sample_rate(self):
        probe = json.loads(GOOD_FFPROBE_JSON)
        assert vm.parse_ffprobe_sample_rate(probe) == 48000

    def test_parse_channels(self):
        probe = json.loads(GOOD_FFPROBE_JSON)
        assert vm.parse_ffprobe_channels(probe) == 2

    def test_parse_format_name(self):
        probe = json.loads(GOOD_FFPROBE_JSON)
        assert vm.parse_ffprobe_format_name(probe) == "flac"

    def test_no_audio_stream_raises(self):
        probe = {"streams": [{"codec_type": "video"}], "format": {}}
        with pytest.raises(ValueError, match="No audio stream"):
            vm.parse_ffprobe_sample_rate(probe)


class TestFormatDuration:
    def test_hours(self):
        assert vm.format_duration(7200) == "2h 0m 0s"

    def test_minutes(self):
        assert vm.format_duration(150) == "2m 30s"

    def test_seconds_only(self):
        assert vm.format_duration(45) == "45s"

    def test_float_truncates(self):
        assert vm.format_duration(90.7) == "1m 30s"


class TestValidationResult:
    def test_all_pass(self):
        vr = vm.ValidationResult()
        vr.add(vm.CheckResult("test", True, "ok"))
        assert vr.passed is True

    def test_one_fail(self):
        vr = vm.ValidationResult()
        vr.add(vm.CheckResult("a", True, "ok"))
        vr.add(vm.CheckResult("b", False, "bad"))
        assert vr.passed is False

    def test_count(self):
        vr = vm.ValidationResult()
        vr.add(vm.CheckResult("a", True, ""))
        vr.add(vm.CheckResult("b", False, ""))
        assert len(vr.checks) == 2


class TestFullValidation:
    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(GOOD_FFPROBE_JSON, GOOD_SOX_STAT),
    )
    def test_all_checks_pass(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is True
        assert len(result.checks) == 7

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(WRONG_RATE_FFPROBE, GOOD_SOX_STAT),
    )
    def test_wrong_sample_rate_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        sample_check = next(c for c in result.checks if c.name == "Sample Rate")
        assert not sample_check.passed

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(GOOD_FFPROBE_JSON, LOUD_SOX_STAT),
    )
    def test_loud_rms_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        rms_check = next(c for c in result.checks if c.name == "RMS Level")
        assert not rms_check.passed

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(GOOD_FFPROBE_JSON, CLIPPED_SOX_STAT),
    )
    def test_clipping_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        peak_check = next(
            c for c in result.checks if c.name == "Peak Level (no clipping)"
        )
        assert not peak_check.passed

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(WRONG_CHANNELS_FFPROBE, GOOD_SOX_STAT),
    )
    def test_mono_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        ch_check = next(c for c in result.checks if c.name == "Channels")
        assert not ch_check.passed

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(SHORT_DURATION_FFPROBE, GOOD_SOX_STAT),
    )
    def test_short_duration_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        dur_check = next(c for c in result.checks if c.name == "Duration")
        assert not dur_check.passed

    @patch("validate_mix.os.path.isfile", return_value=False)
    def test_missing_file_raises(self, mock_exists):
        with pytest.raises(FileNotFoundError):
            vm.validate("nonexistent.flac")

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(GOOD_FFPROBE_JSON, GOOD_SOX_STAT),
    )
    def test_custom_target_duration(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac", target_duration=3600.0)
        assert result.passed is False
        dur_check = next(c for c in result.checks if c.name == "Duration")
        assert not dur_check.passed

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(WAV_FFPROBE, GOOD_SOX_STAT),
    )
    def test_wav_format_passes(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.wav")
        fmt_check = next(c for c in result.checks if c.name == "Format")
        assert fmt_check.passed is True

    @patch("validate_mix.os.path.isfile", return_value=True)
    @patch("validate_mix.os.path.getsize", return_value=86_400_000)
    @patch(
        "validate_mix.subprocess.run",
        side_effect=_mock_subprocess(GOOD_FFPROBE_JSON, QUIET_SOX_STAT),
    )
    def test_quiet_rms_fails(self, mock_run, mock_size, mock_exists):
        result = vm.validate("mix.flac")
        assert result.passed is False
        rms_check = next(c for c in result.checks if c.name == "RMS Level")
        assert not rms_check.passed


class TestBuildParser:
    def test_parser_accepts_input(self):
        parser = vm.build_parser()
        args = parser.parse_args(["--input", "test.flac"])
        assert args.input == "test.flac"

    def test_parser_accepts_duration(self):
        parser = vm.build_parser()
        args = parser.parse_args(["--input", "test.flac", "--duration", "3600"])
        assert args.duration == 3600.0

    def test_parser_accepts_verbose(self):
        parser = vm.build_parser()
        args = parser.parse_args(["--input", "test.flac", "--verbose"])
        assert args.verbose is True

    def test_parser_duration_default_none(self):
        parser = vm.build_parser()
        args = parser.parse_args(["--input", "test.flac"])
        assert args.duration is None

    def test_parser_requires_input(self):
        parser = vm.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])
