"""Playwright-based renderer for recording animated SVG pages as video.

Opens the generated HTML in a headless Chromium, records the animation
using Playwright's built-in video recording (recordVideo context option).
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

PLAYWRIGHT_AVAILABLE: bool = False
try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class PlaywrightNotAvailableError(RuntimeError):
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
        return PLAYWRIGHT_AVAILABLE

    def record_html(
        self,
        html_path: str,
        output_path: str,
        duration: int = 32,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Record an HTML file's animation as video.

        Args:
            html_path: Path to the HTML file to record.
            output_path: Path for the output video file (WebM).
            duration: Recording duration in seconds.
            progress_callback: Optional callable(percent) for progress.

        Returns:
            Path to the output video file.
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

        with tempfile.TemporaryDirectory(prefix="openmusic_shorts_") as tmpdir:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
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
                page.goto(f"file://{html_file.resolve()}", wait_until="networkidle")
                page.wait_for_timeout(1000)

                logger.info("Recording %ss of animation to %s...", duration, output_path)

                for i in range(duration):
                    page.wait_for_timeout(1000)
                    if progress_callback:
                        progress_callback((i + 1) / duration * 100)

                context.close()
                browser.close()

            recorded = list(Path(tmpdir).glob("*.webm"))
            if not recorded:
                raise RuntimeError(
                    "Playwright did not produce a video recording. "
                    "Check that Chromium is installed."
                )

            shutil.move(str(recorded[0]), str(output))

        logger.info("Animation recorded: %s", output)
        return str(output)
