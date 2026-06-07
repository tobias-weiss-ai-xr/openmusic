"""CLI commands for generating short video clips."""
import logging
import shutil
import tempfile
from pathlib import Path

import click

from openmusic.shorts.quotes import get_random_quote, get_quotes_by_author, QUOTES
from openmusic.shorts.pipeline import ShortConfig, ShortsPipeline, generate_batch
from openmusic.shorts.themes import THEME_NAMES
from openmusic.shorts.devops_content import (
    get_random_devops_tip,
    get_tips_by_category,
    get_tips_by_language,
    get_categories,
    get_languages,
)

DEFAULT_DUB_PROMPT = "dub techno texture, deep bass, atmospheric pads, warm analog feel"


@click.group(help="Generate short video clips with stoic quotes and animated visuals.")
def short():
    pass


@short.command()
@click.option("--audio", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Path to audio file (FLAC/WAV) to extract from")
@click.option("--position", default=None, type=float,
              help="Start time in seconds for audio extraction")
@click.option("--generate-audio", is_flag=True, default=False,
              help="Generate fresh audio instead of extracting from existing file")
@click.option("--model", default="ace-step",
              type=click.Choice(["ace-step", "stable-audio-open"]),
              help="Audio generation model (default: ace-step)")
@click.option("--bpm", default=125, type=int,
              help="Beats per minute for generated audio (default: 125)")
@click.option("--key", default="Dm",
              help="Musical key for generated audio (default: Dm)")
@click.option("--quote-text", default=None,
              help="Custom quote text (if not using random)")
@click.option("--quote-author", default=None,
              help="Quote author (required with --quote-text)")
@click.option("--author", default=None,
              help="Filter quotes by author (e.g. 'Marcus Aurelius')")
@click.option("--seed", default=None, type=int,
              help="Random seed for quote selection (deterministic)")
@click.option("--output", "-o", default=None,
              help="Output video path")
@click.option("--no-shorts", is_flag=True, default=False,
              help="Skip 9:16 shorts conversion (keep 16:9)")
@click.option("--landscape", is_flag=True, default=False,
              help="Render in landscape 16:9 instead of native portrait 9:16")
@click.option("--duration", default=30, type=int,
              help="Clip duration in seconds (default: 30)")
@click.option("--svg", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Custom SVG file for animation (default: dub_visual.svg)")
@click.option("--theme", default="default",
              type=click.Choice(["default"] + THEME_NAMES),
              help="Visual theme: default (SVG), solar_flare, oceanic_tones, urban_decay, neon_dusk")
@click.option("--upload", is_flag=True, default=False,
              help="Upload to YouTube after generation")
@click.option("--cookies", default=None,
              help="Path to cookies.txt for YouTube upload (auto-detected)")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging")
def generate(
    audio: str | None,
    position: float | None,
    generate_audio: bool,
    model: str,
    bpm: int,
    key: str,
    quote_text: str | None,
    quote_author: str | None,
    author: str | None,
    seed: int | None,
    output: str | None,
    no_shorts: bool,
    landscape: bool,
    duration: int,
    svg: str | None,
    theme: str,
    upload: bool,
    cookies: str | None,
    verbose: bool,
):
    """Generate a single short video clip with stoic quote and audio segment."""
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if quote_text:
        if not quote_author:
            raise click.ClickException("--quote-author is required when using --quote-text")
        from openmusic.shorts.quotes import StoicQuote as SQ
        quote = SQ(quote_text, quote_author)
    elif author:
        quotes = get_quotes_by_author(author)
        if not quotes:
            raise click.ClickException(f"No quotes found for author: {author}")
        import random
        rng = random.Random(seed)
        quote = rng.choice(quotes)
    else:
        quote = get_random_quote(seed=seed)

    # Resolve audio source: generated or from existing file
    clip_duration = duration
    if generate_audio:
        if audio is not None or position is not None:
            raise click.ClickException("--audio/--position cannot be used with --generate-audio")

        # Use the configured duration as the generation duration (no extraction)
        click.echo(f"Generating {duration}s audio with {model} @ {bpm}bpm {key}...")

        if model == "stable-audio-open":
            from openmusic.generators.stable_audio import StableAudioGenerator
            gen = StableAudioGenerator()
        else:
            from openmusic.acestep.generator import ACEStepGenerator
            gen = ACEStepGenerator()

        if not gen.is_available():
            raise click.ClickException(
                f"{model} is not available (dependencies missing). "
                f"Install ACE-Step or try --model stable-audio-open"
            )

        output_path = gen.generate_texture(
            prompt=DEFAULT_DUB_PROMPT,
            duration=duration,
            bpm=bpm,
            key=key,
        )

        # Copy to a temp location (pipeline does not clean up original audio_path)
        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_wav.close()
        shutil.copy2(output_path, tmp_wav.name)
        audio_path = tmp_wav.name
        start_time = 0.0

        click.echo(f"Audio generated: {audio_path}")
    else:
        if not audio:
            raise click.ClickException("Either --audio or --generate-audio is required")
        if position is None:
            raise click.ClickException("--position is required when using --audio")
        audio_path = audio
        start_time = position
        click.echo(f"Audio: {audio_path} @ {start_time}s ({clip_duration}s)")

    click.echo(f"Quote: \"{quote.text}\" — {quote.author}")
    click.echo(f"Output: {output or '(auto)'}")

    config = ShortConfig(
        quote=quote,
        audio_path=audio_path,
        audio_start_time=start_time,
        clip_duration=clip_duration,
        output_path=output or "",
        make_shorts=not no_shorts,
        portrait=not landscape,
        svg_path=svg,
        theme=theme,
    )

    pipeline = ShortsPipeline()
    result = pipeline.generate_short(config)
    click.echo(f"\nShort generated: {result}")

    if upload:
        click.echo("Uploading to YouTube...")
        from openmusic.export.youtube_uploader import (
            YouTubeUploader,
            YouTubeUploadConfig,
        )

        cookies_path: str | None = cookies
        if not cookies_path:
            for f in sorted(Path(".").glob("cookies*.txt")):
                cookies_path = str(f)
                click.echo(f"Using cookies: {cookies_path}")
                break
        if not cookies_path:
            raise click.ClickException(
                "No cookies file found for YouTube upload. "
                "Pass --cookies <path> or create cookies_*.txt"
            )

        q_text = quote.text
        q_author = quote.author
        theme_label = theme.replace("_", " ").title() if theme != "default" else ""

        upload_config = YouTubeUploadConfig(
            title=f"\"{q_text[:60]}\" — Stoic Wisdom{f' | {theme_label}' if theme_label else ''} | Dub Techno",
            description=(
                f"\"{q_text}\" — {q_author}\n\n"
                f"A {'themed ' if theme_label else ''}meditative dub techno short generated with OpenMusic.\n"
                f"{f'Theme: {theme_label}. ' if theme_label else ''}"
                "AI-powered texture from ACE-Step, processed through analog-style effects.\n\n"
                "Generated by OpenMusic: https://github.com/tobias-weiss-ai-xr/openmusic\n"
                "https://graphwiz.ai"
            ),
            tags=["stoic", "philosophy", "dub techno", "meditation", "ambient", "openmusic"]
            + ([theme_label.lower().replace(" ", "_")] if theme_label else []),
            privacy="unlisted",
            playlist_title=None,
            cookies_file=cookies_path,
        )
        uploader = YouTubeUploader(upload_config)
        video_id = uploader.upload(result)
        click.echo(f"\nUploaded: https://youtube.com/watch?v={video_id}")


@short.command()
@click.option("--audio", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to audio file (FLAC/WAV) to extract from")
@click.option("--positions", required=True,
              help="Comma-separated start times in seconds, e.g. '30,180,600,1800'")
@click.option("--output-dir", default=".",
              help="Directory for output files (default: current dir)")
@click.option("--seed-start", default=0, type=int,
              help="Starting seed for quote selection (increments per clip)")
@click.option("--no-shorts", is_flag=True, default=False,
              help="Skip 9:16 shorts conversion (keep 16:9)")
@click.option("--no-skip", is_flag=True, default=False,
              help="Regenerate clips even if output exists")
@click.option("--svg", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Custom SVG file for animation")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging")
def batch(
    audio: str,
    positions: str,
    output_dir: str,
    seed_start: int,
    no_shorts: bool,
    no_skip: bool,
    svg: str | None,
    verbose: bool,
):
    """Generate multiple short clips from a single audio file."""
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    try:
        pos_list = [float(p.strip()) for p in positions.split(",") if p.strip()]
    except ValueError as e:
        raise click.ClickException(f"Invalid positions format: {e}")
    if not pos_list:
        raise click.ClickException("At least one position required")

    click.echo(f"Generating {len(pos_list)} shorts from {audio}")
    click.echo(f"Positions: {pos_list}")
    click.echo(f"Output dir: {output_dir}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = generate_batch(
        audio_path=audio,
        positions=pos_list,
        output_dir=output_dir,
        quote_seed_start=seed_start,
        svg_path=svg,
        make_shorts=not no_shorts,
        skip_existing=not no_skip,
    )

    click.echo(f"\nGenerated {len(results)} shorts:")
    for r in results:
        click.echo(f"  {r}")


@short.command(name="list-authors")
def list_authors():
    """List all available quote authors."""
    authors = sorted(set(q.author for q in QUOTES))
    click.echo("Available quote authors:")
    for a in authors:
        count = len([q for q in QUOTES if q.author == a])
        click.echo(f"  {a} ({count} quotes)")


@short.command(name="list-quotes")
@click.option("--author", default=None, help="Filter by author")
def list_quotes(author: str | None):
    """List available stoic quotes."""
    if author:
        quotes = get_quotes_by_author(author)
        if not quotes:
            raise click.ClickException(f"No quotes found for author: {author}")
    else:
        quotes = QUOTES

    for i, q in enumerate(quotes, 1):
        click.echo(f"{i:3d}. \"{q.text}\" — {q.author}")


@short.command(name="devops-generate")
@click.option("--audio", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Path to audio file (FLAC/WAV) to extract from")
@click.option("--position", default=None, type=float,
              help="Start time in seconds for audio extraction")
@click.option("--generate-audio", is_flag=True, default=False,
              help="Generate fresh audio instead of extracting from existing file")
@click.option("--model", default="ace-step",
              type=click.Choice(["ace-step", "stable-audio-open"]),
              help="Audio generation model (default: ace-step)")
@click.option("--bpm", default=125, type=int,
              help="Beats per minute for generated audio (default: 125)")
@click.option("--key", default="Dm",
              help="Musical key for generated audio (default: Dm)")
@click.option("--category", default=None,
              help="Filter DevOps tips by category (e.g. docker, kubernetes, ai)")
@click.option("--language", default=None,
              help="Filter DevOps tips by language (e.g. docker, yaml, python)")
@click.option("--seed", default=None, type=int,
              help="Random seed for tip selection (deterministic)")
@click.option("--output", "-o", default=None,
              help="Output video path")
@click.option("--duration", default=20, type=int,
              help="Clip duration in seconds (default: 20)")
@click.option("--svg", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Custom SVG file for animation (default: dub_visual.svg)")
@click.option("--upload", is_flag=True, default=False,
              help="Upload to YouTube after generation")
@click.option("--cookies", default=None,
              help="Path to cookies.txt for YouTube upload (auto-detected)")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging")
def devops_generate(
    audio: str | None,
    position: float | None,
    generate_audio: bool,
    model: str,
    bpm: int,
    key: str,
    category: str | None,
    language: str | None,
    seed: int | None,
    output: str | None,
    duration: int,
    svg: str | None,
    upload: bool,
    cookies: str | None,
    verbose: bool,
):
    """Generate a short video clip with DevOps/AI tip and syntax-highlighted code."""
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    category_lower = category.lower() if category else None
    language_lower = language.lower() if language else None

    if category_lower and language_lower:
        category_tips = get_tips_by_category(category_lower)
        tips = [t for t in category_tips if t.language.lower() == language_lower]
    elif category_lower:
        tips = get_tips_by_category(category_lower)
    elif language_lower:
        tips = get_tips_by_language(language_lower)
    else:
        tips = [
            get_random_devops_tip(seed=seed)
            for _ in range(10)
        ]

    if not tips:
        if category_lower and language_lower:
            raise click.ClickException(f"No tips found for category '{category}' and language '{language}'")
        elif category_lower:
            raise click.ClickException(f"No tips found for category '{category}'")
        elif language_lower:
            raise click.ClickException(f"No tips found for language '{language}'")

    import random
    if not seed:
        tip = random.choice(tips)
    else:
        rng = random.Random(seed)
        tip = rng.choice(tips)

    clip_duration = duration
    if generate_audio:
        if audio is not None or position is not None:
            raise click.ClickException("--audio/--position cannot be used with --generate-audio")

        click.echo(f"Generating {duration}s audio with {model} @ {bpm}bpm {key}...")

        if model == "stable-audio-open":
            from openmusic.generators.stable_audio import StableAudioGenerator
            gen = StableAudioGenerator()
        else:
            from openmusic.acestep.generator import ACEStepGenerator
            gen = ACEStepGenerator()

        if not gen.is_available():
            raise click.ClickException(
                f"{model} is not available (dependencies missing). "
                f"Install ACE-Step or try --model stable-audio-open"
            )

        output_path = gen.generate_texture(
            prompt=DEFAULT_DUB_PROMPT,
            duration=duration,
            bpm=bpm,
            key=key,
        )

        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_wav.close()
        shutil.copy2(output_path, tmp_wav.name)
        audio_path = tmp_wav.name
        start_time = 0.0

        click.echo(f"Audio generated: {audio_path}")
    else:
        if not audio:
            raise click.ClickException("Either --audio or --generate-audio is required")
        if position is None:
            raise click.ClickException("--position is required when using --audio")
        audio_path = audio
        start_time = position
        click.echo(f"Audio: {audio_path} @ {start_time}s ({clip_duration}s)")

    click.echo(f"Tip: {tip.title} [{tip.category}, {tip.language}]")
    click.echo(f"Code: {tip.code[:80]}{'...' if len(tip.code) > 80 else ''}")
    click.echo(f"Output: {output or '(auto)'}")

    config = ShortConfig(
        devops_seed=seed or hash(tip.title + tip.code) % (2**31),
        audio_path=audio_path,
        audio_start_time=start_time,
        clip_duration=clip_duration,
        output_path=output or "",
        make_shorts=True,
        portrait=True,
        svg_path=svg,
        theme="default",
        tags=["devops", "programming", "tech", "tutorial", "openmusic"] + ([tip.category] if tip.category else []),
    )

    pipeline = ShortsPipeline()
    result = pipeline.generate_short(config)
    click.echo(f"\nShort generated: {result}")

    if upload:
        click.echo("Uploading to YouTube...")
        from openmusic.export.youtube_uploader import (
            YouTubeUploader,
            YouTubeUploadConfig,
        )

        cookies_path: str | None = cookies
        if not cookies_path:
            for f in sorted(Path(".").glob("cookies*.txt")):
                cookies_path = str(f)
                click.echo(f"Using cookies: {cookies_path}")
                break
        if not cookies_path:
            raise click.ClickException(
                "No cookies file found for YouTube upload. "
                "Pass --cookies <path> or create cookies_*.txt"
            )

        theme_label = f"{tip.category.upper()}" if tip.category else "DevOps"

        upload_config = YouTubeUploadConfig(
            title=f"{tip.title} | {theme_label} Tip | Programming Tutorial | Dub Techno",
            description=(
                f"{tip.title}\n\n"
                f"{tip.description}\n\n"
                f"A {theme_label} technical tutorial with syntax highlighting, "
                f"set to meditative dub techno music.\n\n"
                f"Category: {tip.category}\n"
                f"Language: {tip.language}\n\n"
                "AI-powered texture from ACE-Step, processed through analog-style effects.\n\n"
                "Generated by OpenMusic: https://github.com/tobias-weiss-ai-xr/openmusic\n"
                "https://graphwiz.ai"
            ),
            tags=["devops", "programming", "tutorial", "tech", "tutorial"]
            + ([tip.category] if tip.category else [])
            + ([tip.language] if tip.language else []),
            privacy="unlisted",
            playlist_title="DevOps Tips | GraphWiz",
            cookies_file=cookies_path,
        )
        uploader = YouTubeUploader(upload_config)
        video_id = uploader.upload(result)
        click.echo(f"\nUploaded: https://youtube.com/watch?v={video_id}")


@short.command(name="devops-list-categories")
def devops_list_categories():
    """List all available DevOps tip categories."""
    categories = get_categories()
    click.echo("Available DevOps categories:")
    for c in categories:
        tips = get_tips_by_category(c)
        count = len(tips)
        click.echo(f"  {c} ({count} tips)")


@short.command(name="devops-list-tips")
@click.option("--category", default=None, help="Filter by category")
@click.option("--language", default=None, help="Filter by language")
def devops_list_tips(category: str | None, language: str | None):
    """List available DevOps tips."""
    category_lower = category.lower() if category else None
    language_lower = language.lower() if language else None

    if category_lower and language_lower:
        category_tips = get_tips_by_category(category_lower)
        tips = [t for t in category_tips if t.language.lower() == language_lower]
    elif category_lower:
        tips = get_tips_by_category(category_lower)
    elif language_lower:
        tips = get_tips_by_language(language_lower)
    else:
        from openmusic.shorts.devops_content import (
            DOCKER_TIPS,
            K8S_TIPS,
            CI_TIPS,
            ANSIBLE_TIPS,
            AI_TIPS,
            GIT_TIPS,
            LINUX_TIPS,
            MONITORING_TIPS,
        )
        tips = (
            DOCKER_TIPS + K8S_TIPS + CI_TIPS + ANSIBLE_TIPS +
            AI_TIPS + GIT_TIPS + LINUX_TIPS + MONITORING_TIPS
        )

    if not tips:
        if category_lower and language_lower:
            raise click.ClickException(f"No tips found for category '{category}' and language '{language}'")
        elif category_lower:
            raise click.ClickException(f"No tips found for category '{category}'")
        elif language_lower:
            raise click.ClickException(f"No tips found for language '{language}'")

    for i, tip in enumerate(tips, 1):
        click.echo(f"{i:3d}. [{tip.category}/{tip.language}] {tip.title}")
        click.echo(f"     {tip.description[:70]}{'...' if len(tip.description) > 70 else ''}")
        click.echo(f"     {tip.code[:80]}{'...' if len(tip.code) > 80 else ''}")
        click.echo()
