"""HTML template generation for short video clips.

Supports themed visual templates and a default SVG-embedding template.
The quote fades in after ~3s, stays visible, then fades out before the clip ends.

Supports both landscape (1920x1080) and native portrait (1080x1920) layouts.
"""

from pathlib import Path
from typing import Optional

from openmusic.shorts.quotes import StoicQuote
from openmusic.shorts.themes import render_themed_html, THEME_NAMES


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
    """Return CSS for landscape (1920x1080) quote overlay."""
    return """
.quote-overlay {
  position: absolute; top: 0; left: 0;
  width: 1920px; height: 1080px;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  pointer-events: none;
  z-index: 2;
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


def _render_portrait_quote_overlay_css() -> str:
    """Return CSS for native portrait (1080x1920) quote overlay.

    SVG scales to fill the top ~56% of the canvas; the quote sits in the
    lower portion with enlarged text for mobile readability. A smooth gradient
    blend transitions from the SVG bottom edge into the quote area.
    """
    return """
.svg-wrapper {
  position: absolute; top: 0; left: 0;
  width: 1080px; height: 607px;
  overflow: hidden;
}
.svg-wrapper svg {
  width: 1080px; height: auto;
  display: block;
}
.fade-overlay {
  position: absolute;
  top: 560px; left: 0;
  width: 1080px; height: 200px;
  background: linear-gradient(to bottom, rgba(2,2,4,0) 0%, #020204 100%);
  pointer-events: none;
  z-index: 2;
}
.quote-overlay {
  position: absolute; top: 0; left: 0;
  width: 1080px; height: 1920px;
  display: flex; flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200px;
  pointer-events: none;
  z-index: 3;
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
  font-size: 64px;
  font-weight: 400; font-style: italic;
  color: #c8b898;
  letter-spacing: 1px; line-height: 1.4;
  text-align: center;
  text-shadow: 0 0 60px rgba(200,184,152,0.10), 0 0 120px rgba(200,184,152,0.05);
  animation: quoteBreath 6s ease-in-out infinite;
  margin-bottom: 28px;
  max-width: 900px;
  padding: 0 60px;
}
.quote-attribution {
  font-family: Futura, 'Century Gothic', 'Avenir Next', sans-serif;
  font-size: 20px;
  font-weight: 300; letter-spacing: 10px;
  color: #7a6a4a; text-transform: uppercase;
  text-shadow: 0 0 30px rgba(122,106,74,0.08);
  margin-top: 12px;
}
@keyframes quoteBreath {
  0%, 100% { opacity: 0.85; transform: scale(1); }
  50%      { opacity: 1;    transform: scale(1.01); }
}"""


def render_short_html(
    quote: StoicQuote,
    svg_path: Optional[str] = None,
    duration: int = 30,
    portrait: bool = True,
    theme: str = "default",
) -> str:
    """Generate a self-contained HTML page with animated SVG + quote overlay.

    Args:
        quote: The StoicQuote to display.
        svg_path: Path to SVG file to embed (default: auto-find dub_visual.svg).
        duration: Total clip duration in seconds (controls fade timing).
        portrait: If True, render at 1080x1920 (native YouTube Shorts) with
            enlarged text for mobile. If False, render at 1920x1080 (landscape).
        theme: Visual theme name (solar_flare, oceanic_tones, urban_decay,
            neon_dusk, or 'default' for standard SVG-embedding template).
    """
    if theme != "default":
        return render_themed_html(quote, theme=theme, duration=duration, portrait=portrait)
    if svg_path:
        svg_content = Path(svg_path).read_text()
    else:
        svg_content = _find_svg()

    text_escaped = quote.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    author_escaped = quote.author.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    if portrait:
        css = _render_portrait_quote_overlay_css()
        body_style = "width: 1080px; height: 1920px;"
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  {body_style}
  background: #020204;
  overflow: hidden;
  position: relative;
}}
{css}
</style>
</head>
<body>

<div class="svg-wrapper">
{svg_content}
</div>
<div class="fade-overlay"></div>

<div class="quote-overlay">
  <div class="quote-text">
    &ldquo;{text_escaped}&rdquo;
  </div>
  <div class="quote-attribution">&mdash; {author_escaped}</div>
</div>

</body>
</html>"""
    else:
        css = _render_quote_overlay_css()
        body_style = "width: 1920px; height: 1080px;"
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  {body_style}
  background: #020204;
  overflow: hidden;
  position: relative;
}}
svg {{ display: block; width: 1920px; height: 1080px; }}
{css}
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
