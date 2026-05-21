"""Audio automation node for per-stage processing."""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pedalboard
import soundfile as sf

from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


def _apply_stage_modifications(
    audio: np.ndarray,
    sr: int,
    stage: str,
    key: str = "Dm",
    bpm: int = 125,
) -> np.ndarray:
    """Apply stage-specific audio effects for harmonic expression.

    Enhanced dynamics and EQ based on stage emotional intensity:
    - Intro/dissolution: spacious, filtered
    - Build: subtle drive, upward sweep
    - Peak: aggressive, saturated
    - Post-peak: varied, broken

    Args:
        audio: Audio segment (stereo)
        sr: Sample rate
        stage: Stage identifier
        key: Musical key for harmonic context
        bpm: BPM for rhythmic modulation

    Returns:
        Processed audio segment
    """
    board = pedalboard.Pedalboard()

    if stage == "ambient-intro":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=400))
        board.append(pedalboard.Reverb(wet_level=0.5, decay_seconds=4.0))
        board.append(pedalboard.Limiter(limit_db=-3.0))

    elif stage == "early-build":
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=40))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=800, gain_db=2, q=1.0))
        board.append(pedalboard.Compressor(threshold_db=-16, ratio=3.0))
        board.append(pedalboard.Reverb(wet_level=0.3))

    elif stage == "mid-build":
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=50))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=1200, gain_db=3, q=0.8))
        board.append(pedalboard.Compressor(threshold_db=-18, ratio=3.5))

    elif stage == "pre-peak-one":
        board.append(pedalboard.LowShelfFilter(gain_db=3, cutoff_frequency_hz=120))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=60))
        board.append(pedalboard.Bitcrush(bit_depth=16))
        board.append(pedalboard.Compressor(threshold_db=-20, ratio=4.0))

    elif stage == "peak-one":
        board.append(pedalboard.LowShelfFilter(gain_db=6, cutoff_frequency_hz=100))
        board.append(pedalboard.HighpassFilter(cutoff_frequency_hz=80))
        board.append(pedalboard.Distortion(drive_db=12))
        board.append(pedalboard.Compressor(threshold_db=-24, ratio=5.0))
        board.append(pedalboard.Tanh())

    elif stage == "peak-two":
        board.append(pedalboard.LowShelfFilter(gain_db=5, cutoff_frequency_hz=110))
        board.append(pedalboard.PeakFilter(peak_frequency_hz=2000, gain_db=4, q=1.2))
        board.append(pedalboard.Saturation(drive_db=18))
        board.append(pedalboard.Compressor(threshold_db=-22, ratio=4.5))

    elif stage == "post-peak":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=6000))
        board.append(pedalboard.BiquadFilter(cutoff_frequency_hz=200, gain_db=-3))
        board.append(pedalboard.Delay(delay_seconds=0.125, feedback=0.3))
        board.append(pedalboard.Compressor(threshold_db=-16, ratio=3.5))

    elif stage == "decay-one":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=1500))
        board.append(pedalboard.Reverb(wet_level=0.6, decay_seconds=3.0))
        board.append(pedalboard.Compressor(threshold_db=-12, ratio=2.5))

    elif stage == "decay-two":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=800))
        board.append(pedalboard.Reverb(wet_level=0.7, decay_seconds=5.0))
        board.append(pedalboard.Delay(delay_seconds=0.25, feedback=0.4))
        board.append(pedalboard.Limiter(limit_db=-6.0))

    elif stage == "dissolution":
        board.append(pedalboard.LowpassFilter(cutoff_frequency_hz=400))
        board.append(pedalboard.Reverb(wet_level=0.8, decay_seconds=8.0))
        board.append(pedalboard.Limiter(limit_db=-12.0))

    return board(audio, sr)


def apply_per_stage_audio_automation(state: VideoPipelineState) -> Dict[str, Any]:
    """Apply stage-specific EQ/compression to enhance musical expression.

    Args:
        state: VideoPipelineState with audio_paths, stage_timings, config

    Returns:
        State update: audio_with_automation = Path
    """
    config = state["config"]
    audio_paths = state["audio_paths"]
    stage_timings = state["stage_timings"]
    key = config.get("key", "Dm")
    bpm = config.get("bpm", 125)

    if not audio_paths:
        raise ValueError("No audio paths to process")

    with tempfile.TemporaryDirectory(prefix="openmusic-video-base-") as tmpdir:
        temp_dir = Path(tmpdir)

        base_audio, sr = sf.read(str(audio_paths[0]))
        for other_path in audio_paths[1:]:
            other_audio, other_sr = sf.read(str(other_path))
            assert other_sr == sr, "Sample rate mismatch"
            base_audio = np.concatenate([base_audio, other_audio])

        processed_audio = base_audio.copy()
        sample_rate = sr

        for start_sec, end_sec, stage_name in stage_timings:
            start_sample = int(start_sec * sample_rate)
            end_sample = min(int(end_sec * sample_rate), len(processed_audio))

            if start_sample >= end_sample:
                continue

            stage_segment = processed_audio[start_sample:end_sample]

            try:
                processed_segment = _apply_stage_modifications(stage_segment, sample_rate, stage_name, key, bpm)
                processed_audio[start_sample:end_sample] = processed_segment
                logger.info(f"Applied automation for stage {stage_name} ({start_sec}-{end_sec}s)")
            except Exception as e:
                logger.warning(f"Failed to apply automation for stage {stage_name}: {e}")

        output_dir = Path.home() / ".cache" / "openmusic" / "video" / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_with_automation = output_dir / "audio_with_automation.flac"

        sf.write(str(audio_with_automation), processed_audio, sample_rate)
        logger.info(f"Saved audio with automation to {audio_with_automation}")

    return {"audio_with_automation": audio_with_automation}