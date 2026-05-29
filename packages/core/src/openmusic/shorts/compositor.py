"""ffmpeg-based audio/video compositing for short clips."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class CompositorError(RuntimeError):
    """Raised when ffmpeg operations fail."""
    pass


def extract_audio_segment(
    audio_path: str,
    start_time: float,
    duration: float,
    output_path: str,
) -> str:
    """Extract a segment from an audio file using ffmpeg."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-i", audio_path,
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(output),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        logger.info("Audio segment extracted: %s (%ss at %ss)", output, duration, start_time)
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg audio extraction failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e


def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    video_bitrate: str = "5M",
    audio_bitrate: str = "192k",
) -> str:
    """Merge video with audio, replacing the video's audio track."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-shortest",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        logger.info("Video+audio merged: %s", output)
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg merge failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e


def convert_to_shorts(
    input_path: str,
    output_path: str,
    background_color: str = "020204",
) -> str:
    """Convert a horizontal video to vertical 9:16 shorts format.

    Scales to fit 1080 width, pads to 1920 height with background color.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf",
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#{background_color}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        logger.info("Shorts conversion: %s", output)
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg shorts conversion failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e
