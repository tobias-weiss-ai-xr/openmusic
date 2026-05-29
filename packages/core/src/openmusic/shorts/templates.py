"""HTML template generation for short video clips.

Embeds the animated SVG (dub_visual.svg) with a quote overlay on top.
The quote fades in after ~3s, stays visible, then fades out before the clip ends.
"""

from pathlib import Path
from typing import Optional

from openmusic.shorts.quotes import StoicQuote


def _find_svg() -> str:
    """Find dub_visual.svg from repo root or fallback."""
    candidates = [
        Path.cwd() / "dub_visual.svg",
        Path(__file__).parent.parent.parent.parent.parent / "dub_visual.svg",
        Path(__file__).parent.parent.parent.parent.parent.parent / "dub_visual.svg",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" '
        'width="1920" height="1080">'
        '<rect width="1920" height="1080" fill="#020204"/>'
        "</svg>"
    )


def _render_quote_overlay_css() -> str:
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
{_render_quote_overlay_css()}
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
