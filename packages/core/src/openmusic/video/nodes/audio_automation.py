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
) -> np.ndarray:
    """Apply stage-specific audio effects."""
    board = pedalboard.Pedalboard()

    if stage in ["ambient-intro", "dissolution"]:
        board.append(pedalboard.LowpassFilter(cutoff_frequency=500))
        board.append(pedalboard.Reverb(wet_level=0.4))

    elif stage in ["peak-one", "peak-two"]:
        board.append(pedalboard.LowShelfFilter(gain_db=4, cutoff_frequency=80))
        board.append(pedalboard.HighpassFilter(cutoff_frequency=25))
        board.append(pedalboard.Compressor(threshold_db=-18, ratio=4.0))

    else:
        board.append(pedalboard.Compressor(threshold_db=-14, ratio=3.0))

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
                processed_segment = _apply_stage_modifications(stage_segment, sample_rate, stage_name)
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