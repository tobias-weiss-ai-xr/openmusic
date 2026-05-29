# Shorts Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the manual stoic shorts workflow (HTML + Playwright recording + ffmpeg compositing) into a reusable CLI pipeline `openmusic short generate`.

**Architecture:** New `openmusic/shorts/` package with 5 modules: quotes DB, HTML templating, Playwright recording, ffmpeg compositing, and a pipeline orchestrator. CLI command groups under `openmusic short`. Reuses existing `YouTubeUploader` from `openmusic.export`.

**Tech Stack:** Python 3.12+, `click` (CLI), `playwright` (video capture), `ffmpeg` (audio extraction + compositing), `numpy` (crossfade support for future use). Reuses `dub_visual.svg` from repo root as animation source.

---

## File Structure

**New files:**
- `packages/core/src/openmusic/shorts/__init__.py` — exports
- `packages/core/src/openmusic/shorts/quotes.py` — curated stoic quotes with authors
- `packages/core/src/openmusic/shorts/templates.py` — HTML generation from SVG + quote
- `packages/core/src/openmusic/shorts/renderer.py` — Playwright video capture
- `packages/core/src/openmusic/shorts/compositor.py` — ffmpeg audio extraction + merging + shorts conversion
- `packages/core/src/openmusic/shorts/pipeline.py` — ShortsPipeline orchestrator
- `packages/core/src/openmusic/cli/shorts.py` — CLI command group
- `packages/core/tests/test_shorts/test_quotes.py` — quote DB tests
- `packages/core/tests/test_shorts/test_templates.py` — template generation tests
- `packages/core/tests/test_shorts/test_compositor.py` — compositor tests (mock ffmpeg)

**Modified files:**
- `packages/core/src/openmusic/cli/main.py` — register `short` command group

---

### Task 1: Quotes Database

**Files:**
- Create: `packages/core/src/openmusic/shorts/quotes.py`
- Test: `packages/core/tests/test_shorts/test_quotes.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for quotes module."""
from openmusic.shorts.quotes import QUOTES, get_random_quote, get_quotes_by_author, StoicQuote

def test_quotes_is_list_of_stoic_quotes():
    """QUOTES should be a list of StoicQuote namedtuples."""
    assert len(QUOTES) > 0
    for q in QUOTES:
        assert isinstance(q, StoicQuote)
        assert isinstance(q.text, str) and len(q.text) > 0
        assert isinstance(q.author, str) and len(q.author) > 0

def test_get_random_quote():
    """get_random_quote returns a StoicQuote from the list."""
    q = get_random_quote()
    assert q in QUOTES

def test_get_random_quote_with_seed():
    """get_random_quote with seed returns deterministic results."""
    q1 = get_random_quote(seed=42)
    q2 = get_random_quote(seed=42)
    assert q1 == q2
    assert q1.text == q2.text

def test_get_quotes_by_author():
    """get_quotes_by_author returns only quotes by that author."""
    marcus = get_quotes_by_author("Marcus Aurelius")
    assert len(marcus) > 0
    assert all(q.author == "Marcus Aurelius" for q in marcus)
    # Case insensitive
    marcus_lower = get_quotes_by_author("marcus aurelius")
    assert len(marcus_lower) == len(marcus)

def test_get_quotes_by_author_unknown():
    """get_quotes_by_author returns empty list for unknown author."""
    assert get_quotes_by_author("Unknown Person") == []

def test_quote_text_has_no_curly_braces():
    """Quote text should not contain curly braces (template injection risk)."""
    for q in QUOTES:
        assert "{" not in q.text, f"Quote contains '{{': {q.text[:50]}..."
        assert "}" not in q.text, f"Quote contains '}}': {q.text[:50]}..."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_shorts/ -v 2>&1 | head -20`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Create quotes module**

```python
"""Curated stoic quotes for short video generation."""
from collections import namedtuple
import random

StoicQuote = namedtuple("StoicQuote", ["text", "author"])

QUOTES: list[StoicQuote] = [
    # Marcus Aurelius
    StoicQuote("The universe is change; our life is what our thoughts make it.", "Marcus Aurelius"),
    StoicQuote("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    StoicQuote("You have power over your mind — not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    StoicQuote("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    StoicQuote("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    StoicQuote("The soul becomes dyed with the color of its thoughts.", "Marcus Aurelius"),
    StoicQuote("If you are distressed by anything external, the pain is not due to the thing itself, but to your estimate of it.", "Marcus Aurelius"),
    StoicQuote("When you arise in the morning, think of what a precious privilege it is to be alive — to breathe, to think, to enjoy, to love.", "Marcus Aurelius"),
    # Epictetus
    StoicQuote("No man is free who is not master of himself.", "Epictetus"),
    StoicQuote("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    StoicQuote("First say to yourself what you would be; then do what you have to do.", "Epictetus"),
    StoicQuote("The key is to keep company only with people who uplift you, whose presence calls forth your best.", "Epictetus"),
    StoicQuote("He who laughs at himself never runs out of things to laugh at.", "Epictetus"),
    # Seneca
    StoicQuote("We suffer more often in imagination than in reality.", "Seneca"),
    StoicQuote("Luck is what happens when preparation meets opportunity.", "Seneca"),
    StoicQuote("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    StoicQuote("Sometimes even to live is an act of courage.", "Seneca"),
    StoicQuote("The whole future lies in uncertainty: live immediately.", "Seneca"),
    # Zeno of Citium
    StoicQuote("Man conquers the world by conquering himself.", "Zeno of Citium"),
    StoicQuote("We have two ears and one mouth, so we should listen more than we say.", "Zeno of Citium"),
]

def get_random_quote(seed: int | None = None) -> StoicQuote:
    """Return a random quote from the collection."""
    rng = random.Random(seed)
    return rng.choice(QUOTES)

def get_quotes_by_author(author: str) -> list[StoicQuote]:
    """Return all quotes by a given author (case-insensitive)."""
    author_lower = author.lower()
    return [q for q in QUOTES if q.author.lower() == author_lower]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_shorts/test_quotes.py -v`
Expected: 6/6 PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/shorts/quotes.py packages/core/tests/test_shorts/test_quotes.py packages/core/tests/test_shorts/__init__.py packages/core/src/openmusic/shorts/__init__.py
git commit -m "feat: add quotes database for short generation"
```

---

### Task 2: HTML Template Engine

**Files:**
- Create: `packages/core/src/openmusic/shorts/templates.py`
- Test: `packages/core/tests/test_shorts/test_templates.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for templates module."""
from pathlib import Path
from openmusic.shorts.templates import (
    render_short_html,
    render_quote_overlay_css,
    StoicQuote,
)

SAMPLE_QUOTE = StoicQuote("The universe is change.", "Marcus Aurelius")

def test_render_short_html_returns_string():
    """render_short_html should return a valid HTML string."""
    html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
    assert isinstance(html, str)
    assert len(html) > 500
    assert "<!DOCTYPE html>" in html

def test_render_short_html_contains_quote_text():
    """The quote text should appear in the rendered HTML."""
    html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
    assert "The universe is change." in html
    assert "Marcus Aurelius" in html

def test_render_short_html_contains_svg():
    """The HTML should contain SVG tags."""
    html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
    assert "<svg" in html
    assert "</svg>" in html

def test_render_short_html_with_custom_svg_path():
    """When svg_path is given, it should be read and embedded."""
    dummy_svg = Path("/tmp/test_dub_visual.svg")
    dummy_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>')
    try:
        html = render_short_html(quote=SAMPLE_QUOTE, svg_path=str(dummy_svg))
        assert 'width="100"' in html
    finally:
        dummy_svg.unlink()

def test_render_short_html_with_long_quote():
    """Long quotes should still render (no truncation)."""
    long_quote = StoicQuote(
        "If you are distressed by anything external, the pain is not due "
        "to the thing itself, but to your estimate of it; and this you "
        "have the power to revoke at any moment.",
        "Marcus Aurelius",
    )
    html = render_short_html(quote=long_quote, svg_path=None)
    assert "distressed" in html
    assert "revoke" in html

def test_render_quote_overlay_css():
    """render_quote_overlay_css returns CSS with quote animations."""
    css = render_quote_overlay_css()
    assert "quote-overlay" in css
    assert "quote-text" in css
    assert "quote-breath" in css or "quoteBreath" in css
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_shorts/test_templates.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create templates module**

```python
"""HTML template generation for short video clips.

Embeds the animated SVG (dub_visual.svg) with a quote overlay on top.
The quote fades in after ~3s, stays visible, then fades out before the clip ends.
"""

from pathlib import Path
from typing import Optional

from openmusic.shorts.quotes import StoicQuote, QUOTES


def _find_svg() -> str:
    """Find dub_visual.svg from repo root or fallback."""
    # Search from common locations
    candidates = [
        Path.cwd() / "dub_visual.svg",
        Path(__file__).parent.parent.parent.parent.parent / "dub_visual.svg",
        Path(__file__).parent.parent.parent.parent.parent.parent / "dub_visual.svg",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text()
    # Last resort: return minimal valid SVG as fallback
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" '
        'width="1920" height="1080">'
        '<rect width="1920" height="1080" fill="#020204"/>'
        "</svg>"
    )


def render_quote_overlay_css() -> str:
    """Return CSS for the quote overlay with fade-in/out and breathing animation."""
    return """
.quote-overlay {
  position: absolute; top: 0; left: 0;
  width: 1920px; height: 1080px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  pointer-events: none;
  animation: quoteContainer 30s ease-in-out forwards;
}
@keyframes quoteContainer {
  0%   { opacity: 0; }
  10%  { opacity: 0; }
  15%  { opacity: 1; }
  70%  { opacity: 1; }
  80%  { opacity: 1; }
  90%  { opacity: 0; }
  100% { opacity: 0; }
}
.quote-text {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 34px; font-weight: 400; font-style: italic;
  color: #c8b898;
  letter-spacing: 1px; line-height: 1.5;
  text-align: center;
  text-shadow: 0 0 40px rgba(200,184,152,0.08), 0 0 80px rgba(200,184,152,0.04);
  animation: quoteBreath 6s ease-in-out infinite;
  margin-bottom: 20px; max-width: 1200px;
}
.quote-attribution {
  font-family: Futura, 'Century Gothic', 'Avenir Next', sans-serif;
  font-size: 14px; font-weight: 300; letter-spacing: 6px;
  color: #7a6a4a; text-transform: uppercase;
  text-shadow: 0 0 20px rgba(122,106,74,0.06);
  margin-top: 8px;
}
@keyframes quoteBreath {
  0%, 100% { opacity: 0.85; transform: scale(1); }
  50%      { opacity: 1;    transform: scale(1.01); }
}
.divider-line {
  width: 60px; height: 1px;
  background: linear-gradient(90deg, transparent, #6a5a3a, transparent);
  margin: 12px auto; opacity: 0.3;
}"""


def render_short_html(
    quote: StoicQuote,
    svg_path: Optional[str] = None,
    duration: int = 30,
) -> str:
    """Generate a self-contained HTML page with animated SVG + quote overlay.

    Args:
        quote: The StoicQuote to display.
        svg_path: Path to SVG file to embed (default: auto-find dub_visual.svg).
        duration: Total clip duration in seconds (controls fade timing).
    """
    if svg_path:
        svg_content = Path(svg_path).read_text()
    else:
        svg_content = _find_svg()

    # Escape quote text for HTML (prevent XSS from template injection)
    text_escaped = quote.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    author_escaped = quote.author.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  width: 1920px; height: 1080px;
  background: #020204;
  overflow: hidden;
  position: relative;
}}
svg {{ display: block; width: 1920px; height: 1080px; }}
{render_quote_overlay_css()}
</style>
</head>
<body>

{svg_content}

<div class="quote-overlay">
  <div class="quote-text">
    &ldquo;{text_escaped}&rdquo;
  </div>
  <div class="divider-line"></div>
  <div class="quote-attribution">&mdash; {author_escaped}</div>
</div>

</body>
</html>"""

    return html
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_shorts/test_templates.py -v`
Expected: 6/6 PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/shorts/templates.py packages/core/tests/test_shorts/test_templates.py
git commit -m "feat: add HTML template engine for quote + SVG shorts"
```

---

### Task 3: Playwright Renderer

**Files:**
- Create: `packages/core/src/openmusic/shorts/renderer.py`

No unit test — requires Playwright with browser binary. Test manually after implementation.

- [ ] **Step 1: Create renderer module**

```python
"""Playwright-based renderer for recording animated SVG pages as video.

Opens the generated HTML in a headless Chromium, records the animation
using Playwright's built-in video recording (recordVideo context option).
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PLAYWRIGHT_AVAILABLE: bool = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class PlaywrightNotAvailableError(RuntimeError):
    """Raised when playwright is not installed or browsers are not found."""

    pass


class ShortsRenderer:
    """Records animated HTML pages as video using Playwright headless Chromium.

    The HTML page must have SMIL/CSS animations that play automatically on load.
    Opens the page in a headless browser, records the viewport for N seconds.
    """

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 25,
        headless: bool = True,
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.headless = headless

    def is_available(self) -> bool:
        """Check if Playwright and browser are available."""
        return PLAYWRIGHT_AVAILABLE

    def record_html(
        self,
        html_path: str,
        output_path: str,
        duration: int = 32,
        progress_callback=None,
    ) -> str:
        """Record an HTML file's animation as video.

        Args:
            html_path: Path to the HTML file to record.
            output_path: Path for the output video file (will be WebM).
            duration: Recording duration in seconds (default 32 for 30s clip).
            progress_callback: Optional callable(percent) for progress.

        Returns:
            Path to the output video file.

        Raises:
            PlaywrightNotAvailableError: if playwright is not installed.
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise PlaywrightNotAvailableError(
                "playwright is not installed. Install with: "
                "pip install playwright && playwright install chromium"
            )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        html_file = Path(html_path)
        if not html_file.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        # Use a temporary directory for Playwright's video output
        with tempfile.TemporaryDirectory(prefix="openmusic_shorts_") as tmpdir:
            video_path = str(Path(tmpdir) / "recording.webm")

            with sync_playwright() as p:
                # Launch browser with video recording
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--autoplay-policy=no-user-gesture-required",
                        "--disable-gpu",
                        "--disable-software-rasterizer",
                    ],
                )

                context = browser.new_context(
                    viewport={"width": self.width, "height": self.height},
                    record_video_dir=tmpdir,
                    record_video_size={"width": self.width, "height": self.height},
                )

                page = context.new_page()

                # Navigate to the HTML file
                page.goto(f"file://{html_file.resolve()}", wait_until="networkidle")

                # Wait for SVG animations to initialize
                page.wait_for_timeout(1000)

                logger.info(
                    f"Recording {duration}s of animation to {output_path}..."
                )

                # Record for the specified duration
                steps = max(10, min(duration, 100))
                for i in range(duration):
                    page.wait_for_timeout(1000)
                    if progress_callback:
                        progress_callback((i + 1) / duration * 100)

                # Close page and context to finalize video
                context.close()
                browser.close()

            # Find the recorded video file
            recorded = list(Path(tmpdir).glob("*.webm"))
            if not recorded:
                raise RuntimeError(
                    "Playwright did not produce a video recording. "
                    "Check that Chromium is installed."
                )

            # Move to output location
            import shutil
            shutil.move(str(recorded[0]), str(output))

        logger.info(f"Animation recorded: {output}")
        return str(output)
```

- [ ] **Step 2: Test manually**

```python
# Run from project root with:
# ACE-Step-1.5/.venv/bin/python -c "
# from openmusic.shorts.quotes import get_random_quote
# from openmusic.shorts.templates import render_short_html
# from openmusic.shorts.renderer import ShortsRenderer
# import tempfile, os
#
# html = render_short_html(get_random_quote(seed=1))
# with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
#     f.write(html)
#     html_path = f.name
#
# r = ShortsRenderer()
# print(f'Playwright available: {r.is_available()}')
# if r.is_available():
#     out = r.record_html(html_path, '/tmp/test_short.webm', duration=5)
#     print(f'Output: {out}')
# os.unlink(html_path)
# "
```

Expected: WebM file created at /tmp/test_short.webm

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/shorts/renderer.py
git commit -m "feat: add Playwright renderer for animated SVG recording"
```

---

### Task 4: Compositor (ffmpeg wrapper)

**Files:**
- Create: `packages/core/src/openmusic/shorts/compositor.py`
- Test: `packages/core/tests/test_shorts/test_compositor.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Tests for compositor module."""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from openmusic.shorts.compositor import (
    extract_audio_segment,
    merge_audio_video,
    convert_to_shorts,
    CompositorError,
)


def test_extract_audio_segment_no_input():
    """extract_audio_segment should raise FileNotFoundError for missing input."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FileNotFoundError):
            extract_audio_segment("/nonexistent.flac", 0, 30, "/tmp/out.wav")


def test_extract_audio_segment_calls_ffmpeg():
    """extract_audio_segment should call ffmpeg with correct args."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        result = extract_audio_segment("/input.flac", 30.0, 32.0, "/tmp/out.wav")
        assert result == "/tmp/out.wav"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args[0]
        assert "-ss" in args
        assert "30.0" in args
        assert "-t" in args
        assert "32.0" in args


def test_merge_audio_video_calls_ffmpeg():
    """merge_audio_video should call ffmpeg with correct args."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        result = merge_audio_video("/video.webm", "/audio.wav", "/output.mp4")
        assert result == "/output.mp4"
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args[0]
        assert "-i" in args
        assert "/video.webm" in args
        assert "/audio.wav" in args


def test_convert_to_shorts_calls_ffmpeg():
    """convert_to_shorts should call ffmpeg with correct 9:16 args."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        result = convert_to_shorts("/input.mp4", "/output_shorts.mp4")
        assert result == "/output_shorts.mp4"
        args = mock_run.call_args[0][0]
        assert "ffmpeg" in args[0]
        # Should have scale/pad for 9:16 vertical
        cmd_str = " ".join(args)
        assert "1080" in cmd_str
        assert "1920" in cmd_str or "scale" in cmd_str


def test_compositor_error():
    """CompositorError should be a proper exception."""
    err = CompositorError("test error")
    assert str(err) == "test error"
    assert isinstance(err, Exception)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest packages/core/tests/test_shorts/test_compositor.py -v`
Expected: FAIL (imports not found)

- [ ] **Step 3: Create compositor module**

```python
"""ffmpeg-based audio/video compositing for short clips."""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CompositorError(RuntimeError):
    """Raised when ffmpeg operations fail."""

    pass


def extract_audio_segment(
    audio_path: str,
    start_time: float,
    duration: float,
    output_path: str,
) -> str:
    """Extract a segment from an audio file using ffmpeg.

    Args:
        audio_path: Path to source audio file (FLAC/WAV/MP3).
        start_time: Start time in seconds.
        duration: Duration to extract in seconds.
        output_path: Path for output WAV file.

    Returns:
        Path to the extracted audio segment.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-i", audio_path,
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        logger.info(f"Audio segment extracted: {output} ({duration}s at {start_time}s)")
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg audio extraction failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e


def merge_audio_video(
    video_path: str,
    audio_path: str,
    output_path: str,
    video_bitrate: str = "5M",
    audio_bitrate: str = "192k",
) -> str:
    """Merge video with audio, replacing the video's audio track.

    Args:
        video_path: Path to input video (WebM from renderer).
        audio_path: Path to input audio (WAV).
        output_path: Path for output MP4.
        video_bitrate: Video bitrate (default 5M).
        audio_bitrate: Audio bitrate (default 192k).

    Returns:
        Path to the merged MP4.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-shortest",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        logger.info(f"Video+audio merged: {output}")
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg merge failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e


def convert_to_shorts(
    input_path: str,
    output_path: str,
    background_color: str = "020204",
) -> str:
    """Convert a horizontal video to vertical 9:16 shorts format.

    Scales to fit 1080 width, pads to 1920 height with background color.

    Args:
        input_path: Path to input video (16:9 horizontal).
        output_path: Path for output shorts video (9:16 vertical).
        background_color: Hex color for padding (default: 020204, near-black).

    Returns:
        Path to the shorts-formatted video.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf",
        f"scale=1080:1920:force_original_aspect_ratio=decrease,"
        f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#{background_color}",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        logger.info(f"Shorts conversion: {output}")
        return str(output)
    except subprocess.CalledProcessError as e:
        raise CompositorError(f"ffmpeg shorts conversion failed: {e.stderr}") from e
    except FileNotFoundError as e:
        raise CompositorError("ffmpeg not found. Install ffmpeg first.") from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest packages/core/tests/test_shorts/test_compositor.py -v`
Expected: 5/5 PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/openmusic/shorts/compositor.py packages/core/tests/test_shorts/test_compositor.py
git commit -m "feat: add ffmpeg compositor for shorts (audio extract, merge, shorts conversion)"
```

---

### Task 5: ShortsPipeline Orchestrator

**Files:**
- Create: `packages/core/src/openmusic/shorts/pipeline.py`

- [ ] **Step 1: Create pipeline orchestrator**

```python
"""Full shorts generation pipeline orchestrator.

Combines quote selection, HTML templating, Playwright recording,
and ffmpeg compositing into a single configurable flow.
"""

import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from openmusic.shorts.quotes import StoicQuote, get_random_quote, get_quotes_by_author
from openmusic.shorts.templates import render_short_html
from openmusic.shorts.renderer import ShortsRenderer, PlaywrightNotAvailableError
from openmusic.shorts.compositor import (
    extract_audio_segment,
    merge_audio_video,
    convert_to_shorts,
    CompositorError,
)

logger = logging.getLogger(__name__)


@dataclass
class ShortConfig:
    """Configuration for generating a single short clip."""

    # Quote configuration
    quote: Optional[StoicQuote] = None
    quote_text: Optional[str] = None
    quote_author: Optional[str] = None
    quote_seed: Optional[int] = None

    # Audio configuration
    audio_path: str = ""
    audio_start_time: float = 0.0
    clip_duration: int = 30

    # Output configuration
    output_path: str = ""
    make_shorts: bool = True
    svg_path: Optional[str] = None

    # Tags (used for upload metadata)
    tags: list[str] = field(default_factory=lambda: [
        "stoic", "dub techno", "meditation", "philosophy", "openmusic",
    ])


class ShortsPipeline:
    """Orchestrates the full shorts generation pipeline.

    Usage:
        pipeline = ShortsPipeline()
        result = pipeline.generate_short(ShortConfig(
            audio_path="mix_10h.flac",
            audio_start_time=1800,
            quote_seed=42,
            output_path="output_shorts.mp4",
        ))
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
        logger.info(f"[{stage}] {percent:.0f}%")

    def generate_short(self, config: ShortConfig) -> str:
        """Run the full pipeline: quote → HTML → record → compose → shorts.

        Args:
            config: Configuration for the short.

        Returns:
            Path to the final output video file.

        Raises:
            PlaywrightNotAvailableError: if playwright not installed.
            CompositorError: if ffmpeg operations fail.
            FileNotFoundError: if audio file not found.
        """
        # 1. Resolve quote
        if config.quote:
            quote = config.quote
        elif config.quote_text and config.quote_author:
            quote = StoicQuote(config.quote_text, config.quote_author)
        else:
            quote = get_random_quote(seed=config.quote_seed)

        self._progress("quote", 5)

        # 2. Generate HTML
        html_content = render_short_html(
            quote=quote,
            svg_path=config.svg_path,
            duration=config.clip_duration,
        )

        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(html_content)
            html_path = f.name

        self._progress("html", 15)

        try:
            # 3. Record via Playwright (record 32s for a 30s clip)
            record_duration = config.clip_duration + 2  # extra buffer

            if not self.renderer.is_available():
                raise PlaywrightNotAvailableError(
                    "Playwright is not available. "
                    "Install with: pip install playwright && playwright install chromium"
                )

            with tempfile.NamedTemporaryFile(
                suffix=".webm", delete=False
            ) as tmp:
                raw_video_path = tmp.name

            self.renderer.record_html(
                html_path=html_path,
                output_path=raw_video_path,
                duration=record_duration,
            )

            self._progress("record", 50)
        finally:
            # Clean up HTML temp file
            try:
                Path(html_path).unlink()
            except Exception:
                pass

        try:
            # 4. Extract audio segment
            audio_segment_path = raw_video_path + "_audio.wav"
            extract_audio_segment(
                audio_path=config.audio_path,
                start_time=config.audio_start_time,
                duration=config.clip_duration,
                output_path=audio_segment_path,
            )

            self._progress("audio", 65)

            # 5. Merge recorded video with extracted audio
            merged_path = raw_video_path + "_merged.mp4"
            merge_audio_video(
                video_path=raw_video_path,
                audio_path=audio_segment_path,
                output_path=merged_path,
            )

            self._progress("merge", 80)

            # 6. Convert to shorts format (9:16 vertical) if requested
            if config.make_shorts:
                final_output = config.output_path or f"short_{config.audio_start_time:.0f}s.mp4"
                convert_to_shorts(
                    input_path=merged_path,
                    output_path=final_output,
                )

                self._progress("shorts", 95)

                # Clean up merged intermediate
                try:
                    Path(merged_path).unlink()
                except Exception:
                    pass
            else:
                final_output = config.output_path or f"short_{config.audio_start_time:.0f}s.mp4"
                Path(merged_path).rename(final_output)

            # Clean up intermediates
            for p in [raw_video_path, audio_segment_path]:
                try:
                    Path(p).unlink()
                except Exception:
                    pass

            self._progress("done", 100)
            logger.info(f"Short generated: {final_output}")
            return final_output

        except (CompositorError, FileNotFoundError) as e:
            # Cleanup on failure
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
            logger.info(f"Skipping existing: {output_path}")
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
```

- [ ] **Step 2: Test manually**

```python
# ACE-Step-1.5/.venv/bin/python -c "
# from openmusic.shorts.pipeline import ShortConfig, ShortsPipeline
# p = ShortsPipeline()
# result = p.generate_short(ShortConfig(
#     audio_path='mix_10h.flac',
#     audio_start_time=30,
#     quote_seed=42,
#     output_path='/tmp/test_short_pipeline.mp4',
# ))
# print(f'Result: {result}')
# "
```

Expected: ~30s short video at /tmp/test_short_pipeline.mp4

- [ ] **Step 3: Commit**

```bash
git add packages/core/src/openmusic/shorts/pipeline.py
git commit -m "feat: add ShortsPipeline orchestrator with batch generation"
```

---

### Task 6: CLI Commands

**Files:**
- Create: `packages/core/src/openmusic/cli/shorts.py`
- Modify: `packages/core/src/openmusic/cli/main.py` (register group)

- [ ] **Step 1: Create cli command module**

```python
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

    # Resolve quote
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
    from openmusic.shorts.quotes import QUOTES
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
```

- [ ] **Step 2: Register in main.py**

Add after `from openmusic.video import build_video_pipeline_graph`:
```python
from openmusic.cli.shorts import short
```

Add after `@main.group(help="MCP orchestration commands")` block:
```python
# Register short commands
main.add_command(short)
```

- [ ] **Step 3: Test CLI**

Run: `ACE-Step-1.5/.venv/bin/python -m openmusic.cli.main short list-authors`
Expected: Lists available authors

Run: `ACE-Step-1.5/.venv/bin/python -m openmusic.cli.main short list-quotes`
Expected: Lists all quotes

Run: `ACE-Step-1.5/.venv/bin/python -m openmusic.cli.main short generate --help`
Expected: Shows help text

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/openmusic/cli/shorts.py packages/core/src/openmusic/cli/main.py
git commit -m "feat: add CLI commands for short generation"
```

---

### Task 7: Final Verification

- [ ] **Step 1: Run existing test suite**

Run: `uv run pytest packages/core/tests/ -v --tb=short 2>&1 | tail -30`
Expected: No new test failures (same pre-existing failures as before)

- [ ] **Step 2: Run LSP diagnostics**

Run LSP diagnostics on new files:
- `packages/core/src/openmusic/shorts/`
- `packages/core/src/openmusic/cli/shorts.py`

Expected: No errors (missing optional deps like playwright are expected to be flagged)

- [ ] **Step 3: Run short generation end-to-end (manual)**

```bash
ACE-Step-1.5/.venv/bin/python -m openmusic.cli.main short generate \
  --audio mix_10h.flac \
  --position 60 \
  --output /tmp/e2e_test_short.mp4
```
Expected: Short video generated at /tmp/e2e_test_short.mp4

- [ ] **Step 4: Commit any remaining changes**

```bash
git add -A
git commit -m "chore: shorts pipeline final polish"
```

---

## Design Decisions

- **No external Celery/Redis dependency**: Shorts generation runs synchronously in-process. For batch jobs, each clip is processed sequentially. Keeps dependencies minimal.
- **HTML temp files cleaned up**: The HTML file is created in a temp dir and deleted after recording. The pipeline is careful to clean up intermediate WebM, WAV, and MP4 files even on failure.
- **Shorts format**: 1080×1920 vertical (YouTube Shorts standard) with `#020204` padding to match the SVG background. Conversion uses ffmpeg scale+pad.
- **Playwright recording**: Uses `recordVideo` context option rather than frame-by-frame screenshots. This is the most reliable way to capture SMIL animations at full framerate.
- **Audio extraction**: Uses WAV (pcm_s16le 44100Hz) as intermediate format — lossless, universally compatible with ffmpeg.
- **Quote injection prevention**: HTML escaping of quote text + no use of `{curly}` templates that could be confused with format strings.
