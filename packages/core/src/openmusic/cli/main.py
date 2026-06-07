import glob as globmod
import json
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
from openmusic.video import build_video_pipeline_graph
from openmusic.cli.shorts import short


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
    model: str = "ace-step",
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
        model=model,
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
@click.option(
    "--model",
    type=click.Choice(["ace-step", "stable-audio-open"]),
    default="ace-step",
    help="Audio generation model (default: ace-step)",
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
    model: str,
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
            model=model,
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
        # Auto-fill description with website link
        desc_parts = [description] if description else []
        desc_parts.append("https://graphwiz.ai")
        full_description = "\n\n".join(p for p in desc_parts if p)

        # Parse comma-separated tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create upload config
        config = YouTubeUploadConfig(
            title=title,
            description=full_description,
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
@click.option(
    "--bpm-schedule",
    required=False,
    default=None,
    help="Comma-separated per-segment BPM overrides, e.g. '0:125,20:130,40:122'",
)
@click.option(
    "--key-schedule",
    required=False,
    default=None,
    help="Comma-separated per-segment key overrides, e.g. '0:Dm,15:Am,30:F#m'",
)
@click.option(
    "--effects-modifiers",
    required=False,
    default=None,
    help="Semicolon-separated per-stage effect modifiers, e.g. 'peak-one:+delay/0.2;decay-one:*delay/0.5'",
)
@click.option("--title", default="Dub Techno Mix", help="Video title")
@click.option(
    "--description",
    default="",
    help="Description text (default: includes GitHub link if empty)",
)
@click.option(
    "--tags", default="dub techno,electronic music", help="Comma-separated tags"
)
@click.option(
    "--privacy",
    type=click.Choice(["public", "private", "unlisted"]),
    default="unlisted",
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
    help="Path to cookies.txt (for youtube-up fallback upload). Auto-detects cookies*.txt if not specified.",
)
@click.option(
    "--model",
    type=click.Choice(["ace-step", "stable-audio-open"]),
    default="ace-step",
    help="Audio generation model (default: ace-step)",
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
    bpm_schedule: Optional[str],
    key_schedule: Optional[str],
    effects_modifiers: Optional[str],
    model: str,
):
    """Generate mix, render MP4 with ffmpeg, and upload to YouTube in one command."""
    click.echo("Starting full publish pipeline...")

    # Auto-fill default description with GitHub link
    if not description:
        description = (
            f"Generated by OpenMusic — AI-powered dub techno generation\n"
            f"https://graphwiz.ai\n"
            f"https://github.com/tobias-weiss-ai-xr/openmusic"
        )
        click.echo(f"  Using default description with GitHub link")

    # Auto-detect cookies file if not specified
    if not cookies:
        cwd = Path.cwd()
        found = sorted(cwd.glob("cookies*.txt")) + sorted(
            cwd.glob(".secrets/cookies*.txt")
        )
        if found:
            cookies = str(found[-1])
            click.echo(f"  Auto-detected cookies: {cookies}")

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
            bpm_schedule=bpm_schedule,
            key_schedule=key_schedule,
            effects_modifiers=effects_modifiers,
            model=model,
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
                # Try CoverGenerator; if that fails (e.g. openart not on Linux),
                # fall back to dub_visual.svg from repo root if available
                try:
                    from openmusic.export.cover_generator import (  # type: ignore[import-untyped]
                        CoverGenerator,
                        MixCoverConfig,
                    )

                    gen = CoverGenerator(MixCoverConfig(
                        key=key,
                        bpm=bpm,
                        length=seconds,
                        title=title or Path(output).stem,
                    ))
                    gen.save_svg(str(cover_svg))
                    gen.save_png(str(cover_png))
                    cover_input = str(cover_png)
                except (ImportError, Exception):
                    dub_visual = Path(__file__).parent.parent.parent.parent.parent / "dub_visual.svg"
                    if dub_visual.exists():
                        subprocess.run(
                            ["rsvg-convert", "-w", "1920", "-h", "1080", str(dub_visual), "-o", str(cover_png)],
                            check=True, capture_output=True,
                        )
                        cover_input = str(cover_png)
                        click.echo("  Generated cover from dub_visual.svg")
                    else:
                        raise click.ClickException(
                            "No cover art available. Install openart or provide --cover-image."
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


# Register short commands
main.add_command(short)


@main.command("publish-video")
@click.option(
    "--audio",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to existing audio file (FLAC/WAV) - skips audio generation",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
    help="Path to a YAML config file",
)
@click.option(
    "--output",
    default="final_video.mp4",
    help="Output video path",
)
@click.option(
    "--use-svg",
    is_flag=True,
    default=False,
    help="Use lightweight SVG generation instead of SDXL (GPU-free)",
)
@click.option(
    "--sdxl-model",
    default="stabilityai/sdxl-turbo",
    help="HuggingFace SDXL model ID or local path",
)
@click.option(
    "--max-concurrent-images",
    default=2,
    type=int,
    help="Max parallel image generation tasks",
)
@click.option(
    "--crossfade-duration",
    default=30,
    type=int,
    help="Stage transition duration in seconds",
)
@click.option(
    "--confirm-upload/--no-confirm-upload",
    default=True,
    help="Interactive upload confirmation",
)
@click.option(
    "--playlist-id",
    default="Dub Odyssee",
    help="YouTube playlist to add to",
)
def publish_video(
    audio: Optional[str],
    config: Optional[str],
    output: str,
    use_svg: bool,
    sdxl_model: str,
    max_concurrent_images: int,
    crossfade_duration: int,
    confirm_upload: bool,
    playlist_id: str,
):
    """Generate enhanced video with AI imagery and upload to YouTube."""
    try:
        length = "1h"
        bpm = 125
        key = "Dm"

        if config:
            with open(config, "r") as f:
                cfg = yaml.safe_load(f) or {}
            length = str(cfg.get("length", length))
            bpm = int(cfg.get("bpm", bpm))
            key = str(cfg.get("key", key))

        seconds = _parse_length_to_seconds(length)

        audio_path = Path(audio) if audio else None

        graph_config = {
            "length": seconds,
            "bpm": bpm,
            "key": key,
            "output_path": output,
            "audio_path": audio_path,
        }

        click.echo("Starting video pipeline...")

        graph = build_video_pipeline_graph(
            graph_config,
            use_svg=use_svg,
            sdxl_model_path=sdxl_model,
            max_concurrent_images=max_concurrent_images,
            crossfade_duration=crossfade_duration,
            confirm_upload=confirm_upload,
            playlist_id=playlist_id,
        )

        import asyncio

        final_state = None

        async def run_pipeline():
            nonlocal final_state
            from openmusic.video.state import initialize_video_pipeline_state
            initial_state = initialize_video_pipeline_state(graph_config)
            async for update in graph.astream(initial_state):
                final_state = update

        asyncio.run(run_pipeline())

        if final_state and final_state.get("youtube_url"):
            click.echo(f"Video uploaded: {final_state['youtube_url']}")
        elif final_state and final_state.get("final_video"):
            click.echo(f"Video generated: {final_state['final_video']}")
        else:
            click.echo("Pipeline completed but no video produced")

    except Exception as e:
        raise click.ClickException(str(e))


@main.command()
@click.option(
    "--output",
    type=click.Path(),
    default="youtube_token.json",
    help="Output path for OAuth token file",
)
def auth_youtube(output: str):
    """Generate YouTube OAuth token using browser flow with localhost callback."""
    try:
        import secrets
        import requests
        from datetime import datetime, timedelta
        from http.server import HTTPServer, BaseHTTPRequestHandler
        from threading import Thread

        CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
        CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
        
        # Read from client_secrets.json or environment
        client_secrets_path = None
        if os.path.exists("client_secrets.json"):
            client_secrets_path = "client_secrets.json"

        if client_secrets_path:
            with open(client_secrets_path, "r") as f:
                secrets_data = json.load(f)
            installed = secrets_data.get("installed", secrets_data)
            CLIENT_ID = installed.get("client_id", CLIENT_ID)
            CLIENT_SECRET = installed.get("client_secret", CLIENT_SECRET)

        if not CLIENT_ID or not CLIENT_SECRET:
            raise click.ClickException("Missing YouTube OAuth credentials. Set YOUTUBE_CLIENT_ID/YOUTUBE_CLIENT_SECRET environment variables or provide client_secrets.json")

        state = secrets.token_urlsafe(16)
        PORT = 18080
        REDIRECT_URI = f"http://localhost:{PORT}"

        import urllib.parse
        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
            f"scope={' '.join(SCOPES)}&"
            "response_type=code&"
            "access_type=offline&"
            "prompt=consent&"
            f"state={state}"
        )

        class CallbackHandler(BaseHTTPRequestHandler):
            auth_code = None

            def do_GET(self):
                from urllib.parse import urlparse, parse_qs
                query = urlparse(self.path).query
                params = parse_qs(query)
                if 'code' in params:
                    CallbackHandler.auth_code = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Authorization successful!</h1><p>Close this window and return to terminal.</p></body></html>")
                else:
                    self.send_response(400)
                    self.wfile.write(b"<html><body><h1>Error</h1></body></html>")

            def log_message(self, format, *args):
                pass

        def start_server():
            HTTPServer.allow_reuse_address = True
            server = HTTPServer(('localhost', PORT), CallbackHandler)
            server.handle_request()

        server_thread = Thread(target=start_server, daemon=True)
        server_thread.start()

        click.echo("\n" + "=" * 70)
        click.echo("YouTube OAuth Authorization")
        click.echo("=" * 70)
        click.echo(f"\n1. Opening browser (or visit manually):\n")
        click.echo(f"{auth_url}")
        click.echo(f"\n2. Authorization will be captured automatically via localhost:{PORT}")
        click.echo("\n" + "=" * 70)

        try:
            import webbrowser
            webbrowser.open(auth_url)
        except:
            pass

        click.echo("\nWaiting for authorization (60s timeout)...")
        for _ in range(60):
            if CallbackHandler.auth_code:
                break
            import time
            time.sleep(1)
        else:
            click.echo("Timeout waiting for authorization.")
            return

        click.echo("\nAuthorization code received!")

        token_data = {
            "code": CallbackHandler.auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data=token_data
        )

        if response.status_code != 200:
            click.echo(f"Token exchange failed: {response.text}")
            return

        tokens = response.json()

        expiry_datetime = datetime.now() + timedelta(seconds=tokens.get('expires_in', 3600))

        token_file_data = {
            "token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": SCOPES,
            "expiry": expiry_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "universe_domain": "googleapis.com",
            "project_id": "gen-lang-client-0811477124"
        }

        with open(output, 'w') as f:
            json.dump(token_file_data, f, indent=2)

        click.echo(f"\nOAuth token saved to: {output}")
        click.echo(f"Expires at: {expiry_datetime}")
        click.echo("\n" + "=" * 70)

    except Exception as e:
        click.echo(f"Error generating OAuth token: {e}")
        raise click.ClickException(str(e))


@click.version_option(version="0.1.0")
def _noop_version():
    pass
