"""Audio generation node for video pipeline."""

import logging
import math
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any

from openmusic.acestep import ACEStepGenerator
from openmusic.orchestrator.mix import _get_stage_for_segment
from openmusic.video.state import VideoPipelineState
from openmusic.video.utils.stage_timing import STAGE_PROMPTS, _compute_stage_timings

logger = logging.getLogger(__name__)


def generate_all_audio_segments(state: VideoPipelineState) -> Dict[str, Any]:
    """Generate all audio segments and capture stage boundary timings.

    Wraps existing ACEStepGenerator to produce audio segments across
    the full mix length, capturing stage timings for parallel image dispatch.

    Args:
        state: VideoPipelineState with config

    Returns:
        State updates: audio_paths, stage_timings, stage_prompts
    """
    config = state["config"]
    segment_duration = config.get("segment_duration", 180.0)
    total_length = config.get("length", 3600.0)

    stage_timings = _compute_stage_timings(total_length)

    segment_count = math.ceil(total_length / segment_duration)

    generator = ACEStepGenerator()

    audio_paths = []
    with tempfile.TemporaryDirectory(prefix="openmusic-video-audio-") as tmpdir:
        temp_dir = Path(tmpdir)

        for i in range(segment_count):
            stage_id = _get_stage_for_segment(i, segment_count)
            stage_prompts = STAGE_PROMPTS.get(stage_id, STAGE_PROMPTS["decay-one"])
            prompt = f"dub techno, {stage_prompts[0]} in {config['key']}, {config['bpm']} BPM"

            seg_bpm = config.get("bpm", 125)
            seg_key = config.get("key", "Dm")

            logger.info(f"Generating segment {i + 1}/{segment_count} (stage: {stage_id})")

            segment_path = generator.generate_texture(
                prompt=prompt,
                duration=int(segment_duration),
                bpm=seg_bpm,
                key=seg_key,
            )

            persistent_path = temp_dir / f"segment_{i:04d}.wav"
            shutil.copy(str(segment_path), str(persistent_path))
            audio_paths.append(persistent_path)

    logger.info(f"Generated {len(audio_paths)} audio segments")

    return {
        "audio_paths": audio_paths,
        "stage_timings": stage_timings,
        "stage_prompts": {stage: prompts[0] for stage, prompts in STAGE_PROMPTS.items()},
    }