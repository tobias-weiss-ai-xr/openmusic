import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TrackMetadata:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: int | None = None
    bpm: int | None = None
    key: str | None = None


class EmbeddingError(Exception):
    def __init__(self, message: str, stderr: str = ""):
        self.stderr = stderr
        if stderr:
            super().__init__(f"{message}: {stderr.strip()}")
        else:
            super().__init__(message)


def embed_metadata(file_path: str | Path, metadata: TrackMetadata, format: str) -> None:
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg,
        "-i",
        str(file_path),
        "-y",
        "-c",
        "copy",
    ]

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
            cmd.extend(["-metadata", f"{tag}={value}"])

    output_path = str(file_path)
    tmp_output = f"{file_path}.tmp"
    cmd.extend([tmp_output])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise EmbeddingError(
            f"Failed to embed metadata in {file_path}", stderr=result.stderr
        )

    Path(tmp_output).replace(output_path)
