"""Tests for templates module."""
import pytest
from pathlib import Path

from openmusic.shorts.quotes import StoicQuote
from openmusic.shorts.templates import render_short_html


SAMPLE_QUOTE = StoicQuote("The universe is change.", "Marcus Aurelius")


class TestTemplates:
    def test_render_short_html_returns_string(self):
        html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
        assert isinstance(html, str)
        assert len(html) > 500
        assert "<!DOCTYPE html>" in html

    def test_render_short_html_contains_quote_text(self):
        html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
        assert "The universe is change." in html
        assert "Marcus Aurelius" in html

    def test_render_short_html_contains_svg(self):
        html = render_short_html(quote=SAMPLE_QUOTE, svg_path=None)
        assert "<svg" in html
        assert "</svg>" in html

    def test_render_short_html_with_custom_svg_path(self):
        dummy_svg = Path("/tmp/test_dub_visual.svg")
        dummy_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100"/></svg>')
        try:
            html = render_short_html(quote=SAMPLE_QUOTE, svg_path=str(dummy_svg))
            assert 'width="100"' in html
        finally:
            dummy_svg.unlink()

    def test_render_short_html_with_long_quote(self):
        long_quote = StoicQuote(
            "If you are distressed by anything external, the pain is not due "
            "to the thing itself, but to your estimate of it; and this you "
            "have the power to revoke at any moment.",
            "Marcus Aurelius",
        )
        html = render_short_html(quote=long_quote, svg_path=None)
        assert "distressed" in html
        assert "revoke" in html
