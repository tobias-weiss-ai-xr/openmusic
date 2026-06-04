"""Full shorts generation pipeline orchestrator.

Combines quote selection, HTML templating, Playwright recording,
and ffmpeg compositing into a single configurable flow.

Supports both Stoic quotes and DevOps tips content types.
"""

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Union

from openmusic.shorts.quotes import StoicQuote, get_random_quote
from openmusic.shorts.templates import render_short_html
from openmusic.shorts.renderer import ShortsRenderer, PlaywrightNotAvailableError
from openmusic.shorts.compositor import (
    extract_audio_segment,
    merge_audio_video,
    convert_to_shorts,
    CompositorError,
)

from openmusic.shorts.devops_content import DevOpsTip, get_random_devops_tip
from openmusic.shorts.devops_templates import render_devops_html

logger = logging.getLogger(__name__)


@dataclass
class ShortConfig:
    """Configuration for generating a single short clip."""

    quote: Optional[StoicQuote] = None
    quote_text: Optional[str] = None
    quote_author: Optional[str] = None
    quote_seed: Optional[int] = None
    devops_seed: Optional[int] = None
    audio_path: str = ""
    audio_start_time: float = 0.0
    clip_duration: int = 30
    output_path: str = ""
    make_shorts: bool = True
    portrait: bool = True
    svg_path: Optional[str] = None
    theme: str = "default"
    tags: list[str] = field(default_factory=lambda: [
        "stoic", "dub techno", "meditation", "philosophy", "openmusic",
    ])


class ShortsPipeline:
    """Orchestrates the full shorts generation pipeline (quote → HTML → record → compose).
    """

    def __init__(
        self,
        renderer: Optional[ShortsRenderer] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        self.renderer = renderer or ShortsRenderer()
        self.progress_callback = progress_callback

    def _progress(self, stage: str, percent: float) -> None:
        if self.progress_callback:
            self.progress_callback(stage, percent)
        logger.info("[%s] %.0f%%", stage, percent)

    def generate_short(self, config: ShortConfig) -> str:
        """Run the full pipeline: quote → HTML → record → compose.

        Supports both StoicQuote and DevOpsTip content types.

        Args:
            config: Configuration for the short.

        Returns:
            Path to the final output video file.
        """
        if config.devops_seed is not None:
            tip = get_random_devops_tip(seed=config.devops_seed)
            html_content = render_devops_html(
                tip=tip,
                svg_path=config.svg_path,
                duration=config.clip_duration,
            )
        elif config.quote:
            quote = config.quote
            html_content = render_short_html(
                quote=quote,
                svg_path=config.svg_path,
                duration=config.clip_duration,
                portrait=config.portrait,
                theme=config.theme,
            )
        elif config.quote_text and config.quote_author:
            quote = StoicQuote(config.quote_text, config.quote_author)
            html_content = render_short_html(
                quote=quote,
                svg_path=config.svg_path,
                duration=config.clip_duration,
                portrait=config.portrait,
                theme=config.theme,
            )
        else:
            quote = get_random_quote(seed=config.quote_seed)
            html_content = render_short_html(
                quote=quote,
                svg_path=config.svg_path,
                duration=config.clip_duration,
                portrait=config.portrait,
                theme=config.theme,
            )

        self._progress("html", 15)

        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(html_content)
            html_path = f.name

        self._progress("html", 30)

        record_duration = config.clip_duration + 2
        raw_video_path = ""

        # Use appropriate renderer dimensions
        renderer = self.renderer
        if config.portrait and (renderer.width != 1080 or renderer.height != 1920):
            renderer = ShortsRenderer(width=1080, height=1920)

        try:
            if not renderer.is_available():
                raise PlaywrightNotAvailableError(
                    "Playwright is not available. "
                    "Install with: pip install playwright && playwright install chromium"
                )

            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                raw_video_path = tmp.name

            renderer.record_html(
                html_path=html_path,
                output_path=raw_video_path,
                duration=record_duration,
            )

            self._progress("record", 50)
        finally:
            try:
                Path(html_path).unlink()
            except Exception:
                pass

        audio_segment_path = raw_video_path + "_audio.wav"

        try:
            extract_audio_segment(
                audio_path=config.audio_path,
                start_time=config.audio_start_time,
                duration=config.clip_duration,
                output_path=audio_segment_path,
            )

            self._progress("audio", 65)

            merged_path = raw_video_path + "_merged.mp4"
            merge_audio_video(
                video_path=raw_video_path,
                audio_path=audio_segment_path,
                output_path=merged_path,
            )

            self._progress("merge", 80)

            if config.portrait:
                # Native portrait render — skip shorts conversion
                final_output = config.output_path or f"short_{config.audio_start_time:.0f}s.mp4"
                shutil.move(merged_path, final_output)
            elif config.make_shorts:
                # Landscape render — convert to 9:16
                final_output = config.output_path or f"short_{config.audio_start_time:.0f}s.mp4"
                convert_to_shorts(
                    input_path=merged_path,
                    output_path=final_output,
                )
                self._progress("shorts", 95)
                try:
                    Path(merged_path).unlink()
                except Exception:
                    pass
            else:
                final_output = config.output_path or f"short_{config.audio_start_time:.0f}s.mp4"
                shutil.move(merged_path, final_output)

            for p in [raw_video_path, audio_segment_path]:
                try:
                    Path(p).unlink()
                except Exception:
                    pass

            self._progress("done", 100)
            logger.info("Short generated: %s", final_output)
            return final_output

        except (CompositorError, FileNotFoundError) as e:
            for p in [raw_video_path, audio_segment_path]:
                try:
                    Path(p).unlink()
                except Exception:
                    pass
            raise


def generate_batch(
    audio_path: str,
    positions: list[float],
    *,
    output_dir: str = ".",
    quote_seed_start: int = 0,
    svg_path: Optional[str] = None,
    make_shorts: bool = True,
    skip_existing: bool = True,
) -> list[str]:
    """Generate multiple shorts from a single audio file at given positions.

    Args:
        audio_path: Path to audio file to extract from.
        positions: List of start times in seconds.
        output_dir: Directory for output files.
        quote_seed_start: Starting seed for quote selection (increments per clip).
        svg_path: Path to SVG file.
        make_shorts: Convert to 9:16 format.
        skip_existing: Skip clips whose output already exists.

    Returns:
        List of output file paths.
    """
    pipeline = ShortsPipeline()
    outputs = []

    for i, pos in enumerate(positions):
        output_name = f"short_{i+1}_{int(pos)}s.mp4"
        output_path = str(Path(output_dir) / output_name)

        if skip_existing and Path(output_path).exists():
            logger.info("Skipping existing: %s", output_path)
            outputs.append(output_path)
            continue

        config = ShortConfig(
            audio_path=audio_path,
            audio_start_time=pos,
            output_path=output_path,
            make_shorts=make_shorts,
            svg_path=svg_path,
            quote_seed=quote_seed_start + i,
        )
        result = pipeline.generate_short(config)
        outputs.append(result)

    return outputs
