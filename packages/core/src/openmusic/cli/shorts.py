"""CLI commands for generating short video clips."""
import logging
from pathlib import Path

import click

from openmusic.shorts.quotes import get_random_quote, get_quotes_by_author, QUOTES
from openmusic.shorts.pipeline import ShortConfig, ShortsPipeline, generate_batch


@click.group(help="Generate short video clips with stoic quotes and animated visuals.")
def short():
    pass


@short.command()
@click.option("--audio", required=True, type=click.Path(exists=True, dir_okay=False),
              help="Path to audio file (FLAC/WAV) to extract from")
@click.option("--position", required=True, type=float,
              help="Start time in seconds for audio extraction")
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
@click.option("--duration", default=30, type=int,
              help="Clip duration in seconds (default: 30)")
@click.option("--svg", default=None, type=click.Path(exists=True, dir_okay=False),
              help="Custom SVG file for animation (default: dub_visual.svg)")
@click.option("--verbose", "-v", is_flag=True, default=False,
              help="Verbose logging")
def generate(
    audio: str,
    position: float,
    quote_text: str | None,
    quote_author: str | None,
    author: str | None,
    seed: int | None,
    output: str | None,
    no_shorts: bool,
    duration: int,
    svg: str | None,
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

    click.echo(f"Quote: \"{quote.text}\" — {quote.author}")
    click.echo(f"Audio: {audio} @ {position}s ({duration}s)")
    click.echo(f"Output: {output or '(auto)'}")

    config = ShortConfig(
        quote=quote,
        audio_path=audio,
        audio_start_time=position,
        clip_duration=duration,
        output_path=output or "",
        make_shorts=not no_shorts,
        svg_path=svg,
    )

    pipeline = ShortsPipeline()
    result = pipeline.generate_short(config)
    click.echo(f"\nShort generated: {result}")


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
