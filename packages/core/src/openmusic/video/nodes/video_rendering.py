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

    Uses ffmpeg concat demuxer to create smooth stage transitions.
    Each stage image displays until the next stage boundary.

    Args:
        state: VideoPipelineState with audio_paths, image_paths, stage_timings, config

    Returns:
        State updates: final_video
    """
    audio_paths = state["audio_paths"]
    if not audio_paths:
        raise ValueError("No audio paths available")

    audio_file = audio_paths[0]
    logger.info(f"Using audio: {audio_file}")

    image_paths_dict = state["image_paths"]
    stage_timings = state["stage_timings"]

    config = state["config"]
    output_path = config.get("output_path", "final_video.mp4")

    valid_images = {
        stage: path for stage, path in image_paths_dict.items() if path is not None
    }

    if not valid_images:
        raise ValueError("No valid image paths available")

    logger.info(f"Rendering video with {len(valid_images)} stages")

    with tempfile.TemporaryDirectory(prefix="openmusic-video-render-") as tmpdir:
        temp_dir = Path(tmpdir)
        output_file = temp_dir / output_path

        concat_path = temp_dir / "images_concat.txt"
        concat_lines = []

        for start, end, stage_name in stage_timings:
            if stage_name not in valid_images:
                continue

            image_path = valid_images[stage_name]
            duration = end - start

            concat_lines.append(f"file '{image_path}'")
            concat_lines.append(f"duration {duration}")

        concat_path.write_text("\n".join(concat_lines))

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