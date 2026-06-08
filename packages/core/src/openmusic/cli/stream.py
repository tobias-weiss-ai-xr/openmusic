"""CLI commands for live streaming generated mixes to YouTube and other platforms."""

import atexit
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional

import click

logger = logging.getLogger(__name__)

STREAM_PLATFORMS = ["youtube", "twitch", "facebook"]

_ffmpeg_available: Optional[bool] = None


def _check_ffmpeg() -> bool:
    """Check if ffmpeg is available (cached after first call)."""
    global _ffmpeg_available
    if _ffmpeg_available is not None:
        return _ffmpeg_available
    _ffmpeg_available = (
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
        ).returncode
        == 0
    )
    return _ffmpeg_available


def _get_stream_url(platform: str, stream_key: str) -> str:
    """Build RTMP ingest URL for a given platform."""
    urls = {
        "youtube": f"rtmp://a.rtmp.youtube.com/live2/{stream_key}",
        "twitch": f"rtmp://live.twitch.tv/app/{stream_key}",
        "facebook": f"rtmp://rtmp-api.facebook.com/rtmp/{stream_key}",
    }
    return urls.get(platform, "")


class StreamManager:
    """Manages a single ffmpeg live streaming subprocess."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None

    @property
    def is_running(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None

    def start(
        self,
        audio_path: str,
        platform: str,
        stream_key: str,
        cover_image: Optional[str] = None,
    ) -> None:
        """Start streaming an audio file to a live platform.

        Uses ffmpeg to loop an audio file and optionally a cover image
        as a static video feed.
        """
        if not _check_ffmpeg():
            raise RuntimeError(
                "ffmpeg is required for live streaming but not found"
            )

        if self.is_running:
            raise RuntimeError("Stream is already running")

        audio = Path(audio_path)
        if not audio.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        ingest_url = _get_stream_url(platform, stream_key)
        if not ingest_url:
            raise ValueError(
                f"Unsupported platform: {platform}. Options: {STREAM_PLATFORMS}"
            )

        if cover_image:
            cover = Path(cover_image)
            if not cover.exists():
                logger.warning(
                    "Cover image not found at %s, streaming audio-only", cover_image
                )
                cover_image = None

        cmd = [
            "ffmpeg",
            "-y",
            "-re",
            "-stream_loop",
            "-1",
            "-i",
            audio_path,
        ]

        if cover_image:
            cmd.extend(["-loop", "1", "-i", cover_image])
            map_flags = [
                "-map",
                "1:v:0",
                "-map",
                "0:a:0",
            ]
        else:
            map_flags = [
                "-map",
                "0:a:0",
            ]

        cmd.extend(map_flags)
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-tune",
                "stillimage",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-f",
                "flv",
                ingest_url,
            ]
        )

        logger.info("Starting stream to %s", platform)

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        def _log_ffmpeg_stderr(proc: subprocess.Popen) -> None:
            for line in proc.stderr or []:
                line = line.strip()
                if line:
                    logger.error("[ffmpeg] %s", line)

        thread = threading.Thread(
            target=_log_ffmpeg_stderr, args=(self._process,), daemon=True
        )
        thread.start()

    def stop(self) -> None:
        """Stop the running stream."""
        if self._process is None:
            logger.warning("No stream is running")
            return

        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._process = None
        logger.info("Stream stopped")

    def get_status(self) -> dict:
        """Get current stream status."""
        return {
            "running": self.is_running,
            "pid": self._process.pid
            if self._process and self.is_running
            else None,
        }


# Module-level singleton manages the stream process
_manager = StreamManager()
atexit.register(_manager.stop)


@click.group(help="Live stream generated mixes to YouTube, Twitch, or Facebook.")
def stream() -> None:
    """Live stream commands."""
    pass


@stream.command()
@click.option(
    "--audio",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Audio file to stream (looped)",
)
@click.option(
    "--platform",
    type=click.Choice(STREAM_PLATFORMS),
    default="youtube",
    help="Streaming platform",
)
@click.option(
    "--stream-key",
    required=True,
    envvar="STREAM_KEY",
    help=(
        "Stream key / ingest token for the streaming platform. "
        "Can also set STREAM_KEY or YOUTUBE_STREAM_KEY env var. "
        "WARNING: Stream key is visible in process listings (ps aux)."
    ),
)
@click.option(
    "--cover",
    type=click.Path(exists=True, dir_okay=False),
    help="Cover image for video feed (optional, audio-only otherwise)",
)
def start(
    audio: str, platform: str, stream_key: str, cover: Optional[str]
) -> None:
    """Start live streaming an audio file to a platform."""
    # Fallback: check legacy YOUTUBE_STREAM_KEY env var
    if not stream_key:
        stream_key = os.environ.get("YOUTUBE_STREAM_KEY", "")
    try:
        _manager.start(
            audio_path=audio,
            platform=platform,
            stream_key=stream_key,
            cover_image=cover,
        )
        click.echo(f"Streaming to {platform}...")
        click.echo(f" Audio: {audio}")
        if cover:
            click.echo(f" Cover: {cover}")
        click.echo("Use 'openmusic stream stop' to end the stream.")
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))


@stream.command()
def stop() -> None:
    """Stop the currently running stream."""
    _manager.stop()
    click.echo("Stream stopped.")


@stream.command()
def status() -> None:
    """Show stream status."""
    info = _manager.get_status()
    if info["running"]:
        click.echo(f"Stream is running (PID: {info['pid']})")
    else:
        click.echo("Stream is not running.")
