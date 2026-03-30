import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from openmusic.export.metadata import TrackMetadata, embed_metadata


class EncoderNotFoundError(Exception):
    pass


class EncodingError(Exception):
    def __init__(self, message: str, stderr: str = ""):
        self.stderr = stderr
        if stderr:
            super().__init__(f"{message}: {stderr.strip()}")
        else:
            super().__init__(message)


@dataclass
class AudioInfo:
    format: str
    duration: float
    sample_rate: int
    bitrate: int = 0
    channels: int = 2


class AudioEncoder:
    def __init__(
        self,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
    ):
        self.ffmpeg_path = ffmpeg_path or shutil.which("ffmpeg") or "ffmpeg"
        self.ffprobe_path = ffprobe_path or shutil.which("ffprobe") or "ffprobe"

    def is_available(self) -> bool:
        return shutil.which(self.ffmpeg_path) is not None

    def _ensure_ffmpeg(self) -> None:
        if not self.is_available():
            raise EncoderNotFoundError(f"ffmpeg not found at '{self.ffmpeg_path}'")

    def _metadata_args(self, metadata: TrackMetadata | None) -> list[str]:
        if metadata is None:
            return []
        args = []
        field_map = {
            "title": metadata.title,
            "artist": metadata.artist,
            "album": metadata.album,
            "genre": metadata.genre,
            "date": str(metadata.year) if metadata.year is not None else None,
            "bpm": str(metadata.bpm) if metadata.bpm is not None else None,
            "key": metadata.key,
        }
        for tag, value in field_map.items():
            if value is not None:
                args.extend(["-metadata", f"{tag}={value}"])
        return args

    def encode_flac(
        self,
        input_path: str | Path,
        output_path: str | Path,
        metadata: TrackMetadata | None = None,
    ) -> Path:
        self._ensure_ffmpeg()

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:a",
            "flac",
            "-sample_fmt",
            "s32",
            "-ar",
            "48000",
        ]
        cmd.extend(self._metadata_args(metadata))
        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise EncodingError(
                f"FLAC encoding failed for {input_path}",
                stderr=result.stderr,
            )

        return Path(output_path)

    def encode_mp3(
        self,
        input_path: str | Path,
        output_path: str | Path,
        bitrate: int = 320,
        metadata: TrackMetadata | None = None,
    ) -> Path:
        self._ensure_ffmpeg()

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{bitrate}k",
        ]
        cmd.extend(self._metadata_args(metadata))
        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise EncodingError(
                f"MP3 encoding failed for {input_path}",
                stderr=result.stderr,
            )

        return Path(output_path)

    def get_format_info(self, file_path: str | Path) -> AudioInfo:
        cmd = [
            self.ffprobe_path,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise EncodingError(
                f"Failed to probe {file_path}",
                stderr=result.stderr,
            )

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            raise EncodingError(f"Invalid ffprobe output for {file_path}")

        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        if not audio_stream:
            raise EncodingError(f"No audio stream found in {file_path}")

        fmt = data.get("format", {})

        duration = float(audio_stream.get("duration") or fmt.get("duration", 0))
        sample_rate = int(audio_stream.get("sample_rate", 0))
        channels = int(audio_stream.get("channels", 2))
        bitrate = int(audio_stream.get("bit_rate") or fmt.get("bit_rate", 0))

        codec_name = audio_stream.get("codec_name", "unknown")
        format_name = fmt.get("format_name", codec_name)

        return AudioInfo(
            format=format_name,
            duration=duration,
            sample_rate=sample_rate,
            bitrate=bitrate,
            channels=channels,
        )

    def probe_codecs(self) -> list[str]:
        cmd = [
            self.ffprobe_path,
            "-codecs",
            "-v",
            "quiet",
            "-print_format",
            "json",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return []

        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return []

        target_codecs = {"flac", "mp3", "wav", "aac"}
        found = set()
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                codec = stream.get("codec_name", "")
                if codec in target_codecs:
                    found.add(codec)

        return sorted(found)
