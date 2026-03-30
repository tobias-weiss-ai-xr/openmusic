#!/usr/bin/env python3
"""Validate a generated dub techno mix against acceptance criteria.

Standalone script that checks an existing audio file against all
machine-verifiable criteria from docs/acceptance_criteria.md.

Uses only stdlib + subprocess calls to ffprobe/sox. No external Python deps.

Usage:
    python scripts/validate_mix.py --input mix.flac
    python scripts/validate_mix.py --input mix.flac --duration 3600
    python scripts/validate_mix.py --input mix.flac --verbose
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_TARGET_DURATION = 7200  # 2 hours in seconds
DURATION_TOLERANCE_PCT = 5.0
REQUIRED_SAMPLE_RATE = 48000
REQUIRED_CHANNELS = 2
ACCEPTABLE_FORMATS = {"flac", "wav", "wave"}
RMS_MIN_DB = -18.0
RMS_MAX_DB = -14.0
RMS_TARGET_DB = -16.0
PEAK_MAX_AMPLITUDE = 10 ** (-0.1 / 20)  # -0.1 dBFS in linear amplitude
MIN_BYTES_PER_SECOND = 500
MAX_BYTES_PER_SECOND = 400_000


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    value: Optional[str] = None


@dataclass
class ValidationResult:
    checks: list[CheckResult] = field(default_factory=list)
    passed: bool = True

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)
        if not check.passed:
            self.passed = False


def run_ffprobe(filepath: str) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", filepath,
        ],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def run_sox_stat(filepath: str) -> str:
    result = subprocess.run(
        ["sox", filepath, "-n", "stat"],
        capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"sox stat failed: {result.stderr.strip()}")
    return result.stderr


def parse_ffprobe_duration(probe: dict) -> float:
    return float(probe["format"]["duration"])


def parse_ffprobe_sample_rate(probe: dict) -> int:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return int(stream["sample_rate"])
    raise ValueError("No audio stream found")


def parse_ffprobe_channels(probe: dict) -> int:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "audio":
            return int(stream["channels"])
    raise ValueError("No audio stream found")


def parse_ffprobe_format_name(probe: dict) -> str:
    return probe["format"]["format_name"].lower()


# sox stat line format: 'RMS     dB:            -24.0824'
def parse_sox_rms_db(stat_output: str) -> Optional[float]:
    match = re.search(r"RMS\s+dB:\s+(-?[0-9]+\.?[0-9]*)", stat_output)
    return float(match.group(1)) if match else None


# sox stat line format: 'Maximum amplitude:     0.707946'
def parse_sox_peak_amplitude(stat_output: str) -> Optional[float]:
    match = re.search(r"Maximum amplitude:\s+(-?[0-9]+\.?[0-9]*)", stat_output)
    return float(match.group(1)) if match else None


def amplitude_to_db(amplitude: float) -> float:
    if amplitude <= 0:
        return float("-inf")
    return 20.0 * math.log10(amplitude)


def check_duration(
    actual_duration: float,
    target_duration: float = DEFAULT_TARGET_DURATION,
    tolerance_pct: float = DURATION_TOLERANCE_PCT,
) -> CheckResult:
    tolerance_seconds = target_duration * (tolerance_pct / 100.0)
    diff = abs(actual_duration - target_duration)
    passed = diff <= tolerance_seconds

    actual_str = format_duration(actual_duration)
    target_str = format_duration(target_duration)
    tol_str = format_duration(tolerance_seconds)

    if passed:
        msg = f"Duration {actual_str} is within ±{tol_str} of target {target_str}"
    else:
        msg = (
            f"Duration {actual_str} is NOT within ±{tol_str} of target {target_str} "
            f"(off by {format_duration(diff)})"
        )

    return CheckResult(
        name="Duration", passed=passed, message=msg,
        value=f"{actual_duration:.3f}s",
    )


def check_sample_rate(actual_rate: int) -> CheckResult:
    passed = actual_rate == REQUIRED_SAMPLE_RATE
    if passed:
        msg = f"Sample rate is {actual_rate} Hz (required: {REQUIRED_SAMPLE_RATE} Hz)"
    else:
        msg = f"Sample rate is {actual_rate} Hz but required {REQUIRED_SAMPLE_RATE} Hz"
    return CheckResult(name="Sample Rate", passed=passed, message=msg, value=f"{actual_rate} Hz")


def check_channels(actual_channels: int) -> CheckResult:
    passed = actual_channels == REQUIRED_CHANNELS
    if passed:
        msg = f"Channels: {actual_channels} (stereo)"
    else:
        msg = f"Channels: {actual_channels} but required {REQUIRED_CHANNELS} (stereo)"
    return CheckResult(name="Channels", passed=passed, message=msg, value=f"{actual_channels}")


def check_format(format_name: str, filepath: str) -> CheckResult:
    detected = format_name.lower()
    ext = os.path.splitext(filepath)[1].lstrip(".").lower()

    effective = None
    for fmt in ACCEPTABLE_FORMATS:
        if fmt in detected:
            effective = fmt
            break
    if effective is None and ext in ACCEPTABLE_FORMATS:
        effective = ext

    passed = effective is not None

    if passed:
        msg = f"Format: {effective.upper()} (detected: {format_name})"
    else:
        acceptable = ", ".join(f.upper() for f in sorted(ACCEPTABLE_FORMATS))
        msg = f"Format '{format_name}' not in acceptable set: {acceptable}"

    return CheckResult(
        name="Format", passed=passed, message=msg,
        value=effective.upper() if effective else format_name,
    )


def check_rms_level(rms_db: Optional[float]) -> CheckResult:
    if rms_db is None:
        return CheckResult(
            name="RMS Level", passed=False,
            message="Could not determine RMS level from sox stat output", value="N/A",
        )

    passed = RMS_MIN_DB <= rms_db <= RMS_MAX_DB

    if passed:
        msg = (
            f"RMS level: {rms_db:.2f} dB "
            f"(target: {RMS_TARGET_DB} dB, range: [{RMS_MIN_DB}, {RMS_MAX_DB}] dB)"
        )
    else:
        msg = (
            f"RMS level: {rms_db:.2f} dB "
            f"OUTSIDE acceptable range [{RMS_MIN_DB}, {RMS_MAX_DB}] dB"
        )

    return CheckResult(name="RMS Level", passed=passed, message=msg, value=f"{rms_db:.2f} dB")


def check_peak_level(peak_amplitude: Optional[float]) -> CheckResult:
    if peak_amplitude is None:
        return CheckResult(
            name="Peak Level", passed=False,
            message="Could not determine peak amplitude from sox stat output", value="N/A",
        )

    peak_db = amplitude_to_db(peak_amplitude)
    passed = peak_amplitude < PEAK_MAX_AMPLITUDE

    if passed:
        msg = f"Peak level: {peak_db:.2f} dB (below -0.1 dB threshold — no clipping)"
    else:
        msg = f"Peak level: {peak_db:.2f} dB EXCEEDS -0.1 dB threshold — CLIPPING DETECTED"

    return CheckResult(name="Peak Level (no clipping)", passed=passed, message=msg, value=f"{peak_db:.2f} dB")


def check_file_size(filepath: str, duration_seconds: float) -> CheckResult:
    file_size = os.path.getsize(filepath)
    bytes_per_second = file_size / duration_seconds if duration_seconds > 0 else 0
    passed = MIN_BYTES_PER_SECOND <= bytes_per_second <= MAX_BYTES_PER_SECOND

    size_mb = file_size / (1024 * 1024)
    bps = bytes_per_second

    if passed:
        msg = (
            f"File size: {size_mb:.1f} MB ({bps:.0f} B/s) — reasonable for "
            f"{format_duration(duration_seconds)} of audio"
        )
    elif bytes_per_second < MIN_BYTES_PER_SECOND:
        msg = (
            f"File size: {size_mb:.1f} MB ({bps:.0f} B/s) — too small for "
            f"{format_duration(duration_seconds)} of audio "
            f"(minimum {MIN_BYTES_PER_SECOND} B/s)"
        )
    else:
        msg = (
            f"File size: {size_mb:.1f} MB ({bps:.0f} B/s) — too large for "
            f"{format_duration(duration_seconds)} of audio "
            f"(maximum {MAX_BYTES_PER_SECOND} B/s)"
        )

    return CheckResult(name="File Size", passed=passed, message=msg, value=f"{size_mb:.1f} MB")


def format_duration(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def validate(
    filepath: str,
    target_duration: float = DEFAULT_TARGET_DURATION,
    verbose: bool = False,
) -> ValidationResult:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    result = ValidationResult()

    probe = run_ffprobe(filepath)
    duration = parse_ffprobe_duration(probe)
    sample_rate = parse_ffprobe_sample_rate(probe)
    channels = parse_ffprobe_channels(probe)
    format_name = parse_ffprobe_format_name(probe)

    result.add(check_duration(duration, target_duration))
    result.add(check_sample_rate(sample_rate))
    result.add(check_channels(channels))
    result.add(check_format(format_name, filepath))
    result.add(check_file_size(filepath, duration))

    try:
        stat_output = run_sox_stat(filepath)
        rms_db = parse_sox_rms_db(stat_output)
        peak_amp = parse_sox_peak_amplitude(stat_output)
    except Exception as exc:
        print(f"WARNING: sox stat failed ({exc}), skipping RMS/peak checks", file=sys.stderr)
        rms_db = None
        peak_amp = None

    result.add(check_rms_level(rms_db))
    result.add(check_peak_level(peak_amp))

    status_icon = lambda passed: "PASS" if passed else "FAIL"
    for check in result.checks:
        if verbose or not check.passed:
            print(f"  [{status_icon(check.passed)}] {check.name}: {check.message}")
        else:
            print(f"  [{status_icon(check.passed)}] {check.name}")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a dub techno mix against acceptance criteria.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Checks performed:\n"
            "  - Duration: within ±5%% of target (default 2h)\n"
            "  - Sample rate: exactly 48000 Hz\n"
            "  - Channels: exactly 2 (stereo)\n"
            "  - Format: FLAC or WAV\n"
            "  - RMS level: -18 to -14 dB (target -16 dB)\n"
            "  - Peak level: below -0.1 dB (no clipping)\n"
            "  - File size: reasonable for duration and format\n"
            "\n"
            "Requires: ffprobe and sox installed on PATH.\n"
            "\n"
            "Exit codes: 0 = all checks pass, 1 = one or more failures."
        ),
    )
    parser.add_argument("--input", "-i", required=True, help="Path to the audio file to validate")
    parser.add_argument(
        "--duration", "-d", type=float, default=None,
        help="Expected duration in seconds (default: 7200 for 2h)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Show detailed measurements")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    target_duration = args.duration if args.duration is not None else DEFAULT_TARGET_DURATION

    print(f"Validating: {args.input}")
    print(f"Target duration: {format_duration(target_duration)}")
    print(f"Tolerance: ±{DURATION_TOLERANCE_PCT}%")
    print()

    try:
        result = validate(args.input, target_duration=target_duration, verbose=args.verbose)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: Validation failed: {exc}", file=sys.stderr)
        return 1

    print()
    if result.passed:
        print(f"RESULT: ALL {len(result.checks)} checks PASSED")
        return 0
    else:
        failed = sum(1 for c in result.checks if not c.passed)
        total = len(result.checks)
        print(f"RESULT: {failed}/{total} checks FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
