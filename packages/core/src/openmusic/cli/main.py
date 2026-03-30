import json
from pathlib import Path
from typing import Optional

import click
import yaml

from openmusic.orchestrator.mix import MixConfig, MixOrchestrator
from openmusic.orchestrator.progress import ProgressReporter


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


def _build_config_from_flags(length: str, bpm: int, key: str, output: str) -> MixConfig:
    seconds = _parse_length_to_seconds(length)
    return MixConfig(
        length=float(seconds),
        bpm=bpm,
        key=key,
        output_path=output,
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
def generate(length: str, bpm: int, key: str, output: str, config: Optional[str]):
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

        mix_config = _build_config_from_flags(length, bpm, key, output)
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


@click.version_option(version="0.1.0")
def _noop_version():
    pass
