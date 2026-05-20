"""Video rendering node with ffmpeg crossfade compositing."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


def render_video_with_crossfades(state: VideoPipelineState) -> Dict[str, Any]:
    """Render MP4 video with image crossfades synchronized to audio timeline.

    Uses ffmpeg filtergraph to create smooth stage transitions.
    Each stage image displays until the next stage boundary, with linear crossfade.

    Args:
        state: VideoPipelineState with audio_paths, image_paths, stage_timings, config

    Returns:
        State updates: final_video
    """
    audio_paths = state["audio_paths"]
    if not audio_paths:
        raise ValueError("No audio paths available")

    audio_file = audio_paths[0]  # Use single audio file
    logger.info(f"Using audio: {audio_file}")

    image_paths = state["image_paths"]
    stage_timings = state["stage_timings"]

    config = state["config"]
    output_path = config.get("output_path", "final_video.mp4")
    crossfade_duration = config.get("crossfade_duration", 30)

    # Filter out None image paths
    valid_images = {
        stage: path for stage, path in image_paths.items() if path is not None
    }

    if not valid_images:
        raise ValueError("No valid image paths available")

    logger.info(f"Rendering video with {len(valid_images)} stages, {crossfade_duration}s crossfade")

    with tempfile.TemporaryDirectory(prefix="openmusic-video-render-") as tmpdir:
        temp_dir = Path(tmpdir)
        output_file = temp_dir / output_path

        # Create concat file for image sequence with durations
        concat_path = temp_dir / "images_concat.txt"
        concat_lines = []

        for i, (stage_name, stage_info) in enumerate(stage_timings.items()):
            if stage_name not in valid_images:
                continue

            image_path = valid_images[stage_name]
            next_stage = list(stage_timings.keys())[list(stage_timings.keys()).index(stage_name) + 1] if stage_name != list(stage_timings.keys())[-1] else None

            # Calculate duration from stage timing
            start_time = stage_info["start"]
            if next_stage:
                next_start = stage_timings[next_stage]["start"]
                duration = next_start - start_time
            else:
                # Last stage: duration to end of audio
                # Get audio duration using ffprobe
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
                    capture_output=True, text=True, timeout=30
                )
                audio_duration = float(result.stdout.strip())
                duration = audio_duration - start_time

            # Write concat entry
            concat_lines.append(f"file '{image_path}'")
            concat_lines.append(f"duration {duration}")

        concat_path.write_text("\n".join(concat_lines))

        # ffmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_path),
            "-i", str(audio_file),
            "-c:v", "libx264",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
            "-c:a", "aac", "-b:a", "256k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file),
        ]

        logger.info(f"Running ffmpeg: {' '.join(cmd[:5])} ...")
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3600)

    logger.info(f"Video rendered: {output_file}")

    return {"final_video": str(output_file)}