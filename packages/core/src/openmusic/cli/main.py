import subprocess
from pathlib import Path
from typing import Optional

import click
import yaml

from openmusic.orchestrator.mix import MixConfig, MixOrchestrator
from openmusic.orchestrator.progress import ProgressReporter
from openmusic.export.youtube_uploader import (
    YouTubeUploader,
    YouTubeUploadConfig,
    YouTubeUploadError,
)


def _parse_length_to_seconds(length: str) -> float:
    if isinstance(length, (int, float)):
        return float(length)
    s = str(length).strip()
    if s.endswith("h"):
        try:
            return float(s[:-1]) * 3600.0
        except ValueError:
            pass
    if s.endswith("m"):
        try:
            return float(s[:-1]) * 60.0
        except ValueError:
            pass
    if s.endswith("s"):
        try:
            return float(s[:-1])
        except ValueError:
            pass
    # Fallback: assume seconds
    try:
        return float(s)
    except ValueError:
        raise click.BadParameter(f"Invalid length value: {length}")


def _build_config_from_flags(
    length: str,
    bpm: int,
    key: str,
    output: str,
    skip_effects: bool = False,
    generate_cover: bool = False,
    cover_theme: str = "dark_industrial",
) -> MixConfig:
    seconds = _parse_length_to_seconds(length)
    return MixConfig(
        length=float(seconds),
        bpm=bpm,
        key=key,
        output_path=output,
        skip_effects=skip_effects,
        generate_cover=generate_cover,
        cover_theme=cover_theme,
    )


@click.group(help="OpenMusic CLI: generate mixes, validate configs and show version")
def main():
    pass


@main.command()
@click.option("--length", default="1h", help="Mix length (e.g. 2h, 30m, 45s)")
@click.option("--bpm", default=125, type=int, help="Beats per minute")
@click.option("--key", default="Dm", help="Musical key, e.g. Dm, C, F#")
@click.option(
    "--output", default="mix.flac", help="Output file path for the generated mix"
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to a YAML config file to generate from",
)
@click.option(
    "--no-effects",
    is_flag=True,
    default=False,
    help="Bypass effects processing; assemble raw audio segments directly",
)
@click.option(
    "--cover",
    is_flag=True,
    default=False,
    help="Generate cover art alongside the mix",
)
@click.option(
    "--cover-theme",
    default="dark_industrial",
    help="Cover art theme (dark_industrial, deep_atmospheric, minimal_geometric, retro_dub_plate)",
)
def generate(
    length: str,
    bpm: int,
    key: str,
    output: str,
    config: Optional[str],
    no_effects: bool,
    cover: bool,
    cover_theme: str,
):
    """Generate a new mix using MixOrchestrator.

    You can either pass explicit flags (length/bpm/key/output) or a --config file
    containing the configuration.
    """
    try:
        if config:
            with open(config, "r") as f:
                cfg = yaml.safe_load(f) or {}
            # Expect a simple mapping with the same field names used below
            length = str(cfg.get("length", length))
            bpm = int(cfg.get("bpm", bpm))
            key = str(cfg.get("key", key))
            output = str(cfg.get("output_path", cfg.get("output", output)))

        mix_config = _build_config_from_flags(
            length,
            bpm,
            key,
            output,
            skip_effects=no_effects,
            generate_cover=cover,
            cover_theme=cover_theme,
        )
        # Use a progress reporter as a lightweight progress indicator
        total_segments = max(
            1, int((mix_config.length) / getattr(mix_config, "segment_duration", 180.0))
        )
        pr = ProgressReporter(total=total_segments)
        orchestrator = MixOrchestrator(mix_config)
        # Start a simple progress indicator (best-effort, no deep integration)
        pr.start_segment(0)
        result_path = orchestrator.generate_mix()
        pr.finish_segment(0.0)
        click.echo(str(result_path))
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.argument("config_path", type=click.Path(exists=True, dir_okay=False))
def validate(config_path: str):
    """Validate a YAML/JSON config file for OpenMusic."""
    try:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        # Basic validation: require some essential keys
        required = ["length", "bpm", "key", "output_path"]
        missing = [k for k in required if k not in data]
        if missing:
            raise click.ClickException(
                f"Invalid config. Missing keys: {', '.join(missing)}"
            )
        click.echo("Config is valid.")
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
def version():
    """Show the OpenMusic CLI version."""
    click.echo("0.1.0")


@main.command()
@click.option(
    "--video",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Path to video file (MP4)",
)
@click.option("--title", default="Dub Techno Mix", help="Video title")
@click.option("--description", default="", help="Description text")
@click.option(
    "--tags",
    default="dub techno,electronic music",
    help="Comma-separated tags",
)
@click.option(
    "--privacy",
    type=click.Choice(["public", "private", "unlisted"]),
    default="private",
    help="Privacy status",
)
@click.option(
    "--thumbnail",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to thumbnail image (PNG/JPG)",
)
@click.option(
    "--playlist",
    required=False,
    help="Playlist title (creates if not exists)",
)
@click.option(
    "--schedule",
    required=False,
    help="ISO 8601 datetime for premiere (e.g. 2025-12-31T23:59:59Z)",
)
@click.option(
    "--client-secrets",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default="client_secrets.json",
    help="Path to OAuth client_secrets.json",
)
@click.option(
    "--cookies",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default="cookies.txt",
    help="Path to cookies.txt for youtube-up fallback",
)
def upload(
    video: str,
    title: str,
    description: str,
    tags: str,
    privacy: str,
    thumbnail: Optional[str],
    playlist: Optional[str],
    schedule: Optional[str],
    client_secrets: str,
    cookies: str,
):
    """Upload a video to YouTube with automatic fallback."""
    try:
        # Parse comma-separated tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create upload config
        config = YouTubeUploadConfig(
            title=title,
            description=description,
            tags=tag_list,
            privacy=privacy,
            thumbnail_path=thumbnail,
            playlist_title=playlist,
            publish_at=schedule,
            client_secrets_file=client_secrets,
            cookies_file=cookies,
        )

        # Create uploader and upload
        uploader = YouTubeUploader(config)
        video_id = uploader.upload(video)

        click.echo(f"Upload successful!")
        click.echo(f"Video ID: {video_id}")
        click.echo(f"URL: https://youtube.com/watch?v={video_id}")

    except YouTubeUploadError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Unexpected error: {e}")


@main.command()
@click.option("--length", default="1h", help="Mix length (e.g. 2h, 30m, 45s)")
@click.option("--bpm", default=125, type=int, help="Beats per minute")
@click.option("--key", default="Dm", help="Musical key, e.g. Dm, C, F#")
@click.option(
    "--output", default="mix.flac", help="Output file path for the generated mix"
)
@click.option(
    "--no-effects", is_flag=True, default=False, help="Bypass effects processing"
)
@click.option("--cover-theme", default="dark_industrial", help="Cover art theme")
@click.option("--title", default="Dub Techno Mix", help="Video title")
@click.option("--description", default="", help="Description text")
@click.option(
    "--tags", default="dub techno,electronic music", help="Comma-separated tags"
)
@click.option(
    "--privacy",
    type=click.Choice(["public", "private", "unlisted"]),
    default="private",
    help="Privacy status",
)
@click.option(
    "--thumbnail",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to thumbnail image (PNG/JPG)",
)
@click.option(
    "--playlist",
    required=False,
    help="Playlist title (creates if not exists)",
)
@click.option(
    "--schedule",
    required=False,
    help="ISO 8601 datetime for premiere (e.g. 2025-12-31T23:59:59Z)",
)
@click.option(
    "--client-secrets",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default="client_secrets.json",
    help="Path to OAuth client_secrets.json",
)
@click.option(
    "--cookies",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    default="cookies.txt",
    help="Path to cookies.txt for youtube-up fallback",
)
def publish(
    length: str,
    bpm: int,
    key: str,
    output: str,
    no_effects: bool,
    cover_theme: str,
    title: str,
    description: str,
    tags: str,
    privacy: str,
    thumbnail: Optional[str],
    playlist: Optional[str],
    schedule: Optional[str],
    client_secrets: str,
    cookies: str,
):
    """Generate mix, render MP4 with ffmpeg, and upload to YouTube in one command."""
    click.echo("Starting full publish pipeline...")

    # Step 1: Generate mix with cover art
    click.echo(f"\n[1/3] Generating mix ({length}, {bpm} BPM, {key})...")
    try:
        seconds = _parse_length_to_seconds(length)
        mix_config = MixConfig(
            length=seconds,
            bpm=bpm,
            key=key,
            output_path=output,
            skip_effects=no_effects,
            generate_cover=True,
            cover_theme=cover_theme,
            cover_title=title,
            cover_artist="OpenMusic",
        )
        orchestrator = MixOrchestrator(mix_config)
        mix_path = orchestrator.generate_mix()
        click.echo(f"✓ Mix generated: {mix_path}")
    except Exception as e:
        raise click.ClickException(f"Mix generation failed: {e}")

    # Step 2: Render MP4 using ffmpeg
    click.echo("\n[2/3] Rendering MP4 video...")
    mp4_path = None
    try:
        mp4_path = str(Path(output).with_suffix(".mp4"))
        stem = Path(output).stem
        parent = Path(output).parent

        # Find cover file (prefer PNG, fall back to SVG)
        cover_png = parent / f"{stem}_cover.png"
        cover_svg = parent / f"{stem}_cover.svg"

        if cover_png.exists():
            cover_input = str(cover_png)
        elif cover_svg.exists():
            cover_input = str(cover_svg)
        else:
            raise click.ClickException(
                f"Cover art not found. Expected {cover_png} or {cover_svg}"
            )

        cmd = [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            cover_input,
            "-i",
            str(mix_path),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "256k",
            "-shortest",
            "-movflags",
            "+faststart",
            "-pix_fmt",
            "yuv420p",
            mp4_path,
        ]

        click.echo(f"  Running ffmpeg (this may take a while)...")
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=3600
        )
        click.echo(f"✓ MP4 rendered: {mp4_path}")
    except subprocess.TimeoutExpired:
        raise click.ClickException("ffmpeg timed out after 1 hour")
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"ffmpeg failed: {e.stderr}")
    except Exception as e:
        raise click.ClickException(f"MP4 rendering failed: {e}")

    # Step 3: Upload to YouTube
    click.echo("\n[3/3] Uploading to YouTube...")
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        upload_config = YouTubeUploadConfig(
            title=title,
            description=description,
            tags=tag_list,
            privacy=privacy,
            thumbnail_path=thumbnail,
            playlist_title=playlist,
            publish_at=schedule,
            client_secrets_file=client_secrets,
            cookies_file=cookies,
        )
        uploader = YouTubeUploader(upload_config)
        video_id = uploader.upload(mp4_path)
        click.echo(f"✓ Upload successful!")
        click.echo(f"  Video ID: {video_id}")
        click.echo(f"  URL: https://youtube.com/watch?v={video_id}")
    except YouTubeUploadError as e:
        click.echo(f"✗ YouTube upload failed: {e}")
        click.echo(f"\nMP4 file saved at: {mp4_path}")
        click.echo("You can upload it manually to YouTube.")
        return 1
    except Exception as e:
        raise click.ClickException(f"YouTube upload error: {e}")

    # Step 4: Cleanup prompt
    click.echo("\n" + "=" * 50)
    intermediate_files = [
        str(mix_path),
        str(Path(output).parent / f"{Path(output).stem}_cover.svg"),
        str(Path(output).parent / f"{Path(output).stem}_cover.png"),
        mp4_path,
    ]
    existing_intermediate = [f for f in intermediate_files if Path(f).exists()]

    if existing_intermediate:
        click.echo("Intermediate files created:")
        for f in existing_intermediate:
            click.echo(f"  - {f}")

        if click.confirm("\nKeep intermediate files?", default=True):
            click.echo("Files preserved.")
        else:
            for f in existing_intermediate:
                try:
                    Path(f).unlink()
                    click.echo(f"  Deleted: {f}")
                except Exception as e:
                    click.echo(f"  Failed to delete {f}: {e}")

    click.echo("\n✓ Publish complete!")


@click.version_option(version="0.1.0")
def _noop_version():
    pass
