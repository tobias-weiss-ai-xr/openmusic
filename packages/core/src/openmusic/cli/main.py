import glob as globmod
import os
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
    effects_backend: str = "pedalboard",
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
        effects_backend=effects_backend,
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
    "--effects-backend",
    type=click.Choice(["pedalboard", "typescript", "none"]),
    default="pedalboard",
    help="Effects processing backend (default: pedalboard)",
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
@click.option(
    "--cover-image",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to custom cover image (PNG/JPG) instead of auto-generated",
)
def generate(
    length: str,
    bpm: int,
    key: str,
    output: str,
    config: Optional[str],
    no_effects: bool,
    effects_backend: str,
    cover: bool,
    cover_theme: str,
    cover_image: Optional[str],
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

        # If cover_image is provided, skip auto-generation
        generate_cover_flag = cover and not cover_image

        mix_config = _build_config_from_flags(
            length,
            bpm,
            key,
            output,
            skip_effects=no_effects,
            effects_backend=effects_backend,
            generate_cover=generate_cover_flag,
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
    default="public",
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
    default="dub odyssee",
    help="Playlist title (creates if not exists)",
)
@click.option(
    "--schedule",
    required=False,
    help="ISO 8601 datetime for premiere (e.g. 2025-12-31T23:59:59Z)",
)
@click.option(
    "--client-secrets",
    type=click.Path(dir_okay=False),
    required=False,
    default=None,
    help="Path to OAuth client_secrets.json (for YouTube API upload)",
)
@click.option(
    "--cookies",
    type=click.Path(dir_okay=False),
    required=False,
    default=None,
    help="Path to cookies.txt (for youtube-up fallback upload)",
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
    client_secrets: Optional[str],
    cookies: Optional[str],
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
@click.option(
    "--cover-image",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to custom cover image (PNG/JPG) instead of auto-generated",
)
@click.option(
    "--slideshow-dir",
    type=click.Path(exists=True, file_okay=False),
    required=False,
    help="Directory of images for slow slideshow video (e.g. ComfyUI output)",
)
@click.option(
    "--slideshow-framerate",
    default="auto",
    help="Image change interval in seconds, or 'auto' to calculate from mix length / image count",
)
@click.option("--title", default="Dub Techno Mix", help="Video title")
@click.option("--description", default="", help="Description text")
@click.option(
    "--tags", default="dub techno,electronic music", help="Comma-separated tags"
)
@click.option(
    "--privacy",
    type=click.Choice(["public", "private", "unlisted"]),
    default="public",
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
    default="dub odyssee",
    help="Playlist title (creates if not exists)",
)
@click.option(
    "--schedule",
    required=False,
    help="ISO 8601 datetime for premiere (e.g. 2025-12-31T23:59:59Z)",
)
@click.option(
    "--client-secrets",
    type=click.Path(dir_okay=False),
    required=False,
    default=None,
    help="Path to OAuth client_secrets.json (for YouTube API upload)",
)
@click.option(
    "--cookies",
    type=click.Path(dir_okay=False),
    required=False,
    default=None,
    help="Path to cookies.txt (for youtube-up fallback upload)",
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
    client_secrets: Optional[str],
    cookies: Optional[str],
    cover_image: Optional[str],
    slideshow_dir: Optional[str],
    slideshow_framerate: str,
):
    """Generate mix, render MP4 with ffmpeg, and upload to YouTube in one command."""
    click.echo("Starting full publish pipeline...")

    # Step 1: Generate mix with cover art
    click.echo(f"\n[1/3] Generating mix ({length}, {bpm} BPM, {key})...")
    try:
        seconds = _parse_length_to_seconds(length)
        # Skip auto-generated cover if custom cover or slideshow is provided
        generate_cover_flag = not (cover_image or slideshow_dir)
        mix_config = MixConfig(
            length=seconds,
            bpm=bpm,
            key=key,
            output_path=output,
            skip_effects=no_effects,
            generate_cover=generate_cover_flag,
            cover_theme=cover_theme,
            cover_title=title,
            cover_artist="OpenMusic",
        )
        orchestrator = MixOrchestrator(mix_config)
        mix_path = orchestrator.generate_mix()
        click.echo(f"[OK] Mix generated: {mix_path}")
    except Exception as e:
        raise click.ClickException(f"Mix generation failed: {e}")

    # Step 2: Render MP4 using ffmpeg
    click.echo("\n[2/3] Rendering MP4 video...")
    mp4_path = None
    try:
        mp4_path = str(Path(output).with_suffix(".mp4"))
        stem = Path(output).stem
        parent = Path(output).parent

        if slideshow_dir:
            # Slideshow mode: create video from directory of images
            click.echo(f"  Creating slideshow from {slideshow_dir}...")

            # Find all images in slideshow directory
            image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp")
            image_files = []
            for ext in image_extensions:
                image_files.extend(
                    sorted(globmod.glob(os.path.join(slideshow_dir, ext)))
                )
            image_files = sorted(set(image_files))  # deduplicate

            if not image_files:
                raise click.ClickException(f"No images found in {slideshow_dir}")

            click.echo(f"  Found {len(image_files)} images")

            # Calculate framerate: how long each image should display
            if slideshow_framerate == "auto":
                img_duration = seconds / len(image_files)
            else:
                img_duration = float(slideshow_framerate)

            fps = 1.0 / img_duration
            click.echo(f"  Image duration: {img_duration:.2f}s ({fps:.3f} fps)")

            # Create ffmpeg concat file
            concat_content = ""
            for img_path in image_files:
                # Normalize path for ffmpeg (forward slashes)
                normalized = img_path.replace("\\", "/")
                # Escape single quotes
                normalized = normalized.replace("'", "'\\''")
                concat_content += f"file '{normalized}'\n"
                concat_content += f"duration {img_duration}\n"

            # Write concat file
            concat_path = str(parent / f"{stem}_concat.txt")
            with open(concat_path, "w") as f:
                f.write(concat_content)

            # ffmpeg command with concat demuxer
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_path,
                "-i",
                str(mix_path),
                "-c:v",
                "libx264",
                "-vf",
                "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "256k",
                "-shortest",
                "-movflags",
                "+faststart",
                "-r",
                str(max(fps, 0.01)),  # ensure positive framerate
                mp4_path,
            ]

            click.echo(f"  Running ffmpeg (this may take a while)...")
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True, timeout=3600
            )

            # Clean up concat file
            try:
                Path(concat_path).unlink()
            except Exception:
                pass

        elif cover_image:
            # Custom cover image mode
            click.echo(f"  Using custom cover: {cover_image}")
            cmd = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                cover_image,
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
        else:
            # Auto-generated cover mode (existing behavior)
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

        click.echo(f"[OK] MP4 rendered: {mp4_path}")
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
        click.echo(f"[OK] Upload successful!")
        click.echo(f"  Video ID: {video_id}")
        click.echo(f"  URL: https://youtube.com/watch?v={video_id}")
    except YouTubeUploadError as e:
        click.echo(f"[!] YouTube upload failed: {e}")
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

    click.echo("\n[OK] Publish complete!")


@main.group(help="MCP orchestration commands")
def mcp():
    """Control external creative tools via MCP."""
    pass


@mcp.command()
@click.option("--host", default="127.0.0.1", help="Ableton Live host")
@click.option("--port", default=11044, type=int, help="Ableton Live port")
def ableton_status(host: str, port: int):
    """Check Ableton Live connection status."""
    from openmusic.mcp.orchestrator import MCPOrchestrator, MCPConfig

    config = MCPConfig(ableton_host=host, ableton_port=port)
    orch = MCPOrchestrator(config)
    status = orch.get_ableton_status()

    if status["connected"]:
        click.echo(f"Ableton Live connected at {host}:{port}")
    else:
        click.echo(f"Ableton Live not reachable: {status.get('error', 'unknown')}")


@mcp.command()
@click.option("--host", default="127.0.0.1", help="ComfyUI host")
@click.option("--port", default=8188, type=int, help="ComfyUI port")
def comfyui_status(host: str, port: int):
    """Check ComfyUI connection status."""
    from openmusic.mcp.orchestrator import MCPOrchestrator, MCPConfig

    config = MCPConfig(comfyui_host=host, comfyui_port=port)
    orch = MCPOrchestrator(config)
    status = orch.get_comfyui_status()

    if status["connected"]:
        click.echo(f"ComfyUI connected at {host}:{port}")
    else:
        click.echo(f"ComfyUI not reachable: {status.get('error', 'unknown')}")


@click.version_option(version="0.1.0")
def _noop_version():
    pass
