"""SVG-based artistic image generation for video pipeline.

Generates minimalist stage-specific SVG artwork as lightweight fallback
for GPU-constrained environments (no SDXL/AI models needed).
"""

import logging
import math
from pathlib import Path
from typing import Dict, Any

from openmusic.video.state import VideoPipelineState

logger = logging.getLogger(__name__)


_STAGE_COLORS = {
    "ambient-intro": {"bg": "#0a0a0a", "accent": "#001a1a", "_element": "#003333"},
    "early-build": {"bg": "#0d0d0d", "accent": "#001a1a", "_element": "#004444"},
    "mid-build": {"bg": "#111111", "accent": "#002222", "_element": "#005555"},
    "pre-peak-one": {"bg": "#141414", "accent": "#002a2a", "_element": "#006666"},
    "peak-one": {"bg": "#0f0f0f", "accent": "#003333", "_element": "#008888"},
    "peak-two": {"bg": "#121212", "accent": "#003a3a", "_element": "#009999"},
    "post-peak": {"bg": "#0e0e0e", "accent": "#002828", "_element": "#006666"},
    "decay-one": {"bg": "#0b0b0b", "accent": "#001a1a", "_element": "#004444"},
    "decay-two": {"bg": "#0c0c0c", "accent": "#001a1a", "_element": "#003333"},
    "dissolution": {"bg": "#080808", "accent": "#000f0f", "_element": "#002222"},
}


def _generate_svg_stage_artwork(stage_name: str, output_path: Path) -> None:
    """Generate minimalist SVG artwork for a stage.

    Uses geometric abstraction with color schemes that reflect
    the emotional progression through dub techno stages.

    Args:
        stage_name: Stage identifier (e.g., "ambient-intro")
        output_path: Where to save the SVG file
    """
    colors = _STAGE_COLORS.get(stage_name, _STAGE_COLORS["ambient-intro"])
    bg = colors["bg"]
    accent = colors["accent"]
    element = colors["_element"]

    stage_num = list(_STAGE_COLORS.keys()).index(stage_name)
    base_size = 1920
    height = 1080

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {base_size} {height}">
  <rect width="{base_size}" height="{height}" fill="{bg}"/>

  {'' if stage_name == "ambient-intro" else f'''
  <defs>
    <linearGradient id="grad{stage_num}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{element};stop-opacity:0.6" />
    </linearGradient>
    <filter id="blur{stage_num}">
      <feGaussianBlur in="SourceGraphic" stdDeviation="{2 + stage_num * 0.5}" />
    </filter>
  </defs>
  '''}
'''

    svg_content += f'''

  <circle cx="{base_size//2}" cy="{height//2}" r="{300 + stage_num * 40}"
          fill="{f'url(#grad{stage_num})' if stage_name != 'ambient-intro' else accent}"
          opacity="{0.1 + stage_num * 0.02}"
          filter="{f'url(#blur{stage_num})' if stage_name != 'ambient-intro' else ''}" />

  <rect x="{100 + stage_num * 50}" y="{100 + stage_num * 30}" 
        width="{400 - stage_num * 20}" height="{height - 200 - stage_num * 60}" 
        fill="none" stroke="{accent}" stroke-width="{1 + stage_num * 0.2}" 
        opacity="{0.3 + stage_num * 0.05}" />

  <rect x="{base_size - 500 + stage_num * 50}" y="{100 + stage_num * 30}" 
        width="{400 - stage_num * 20}" height="{height - 200 - stage_num * 60}" 
        fill="none" stroke="{element}" stroke-width="{1 + stage_num * 0.2}" 
        opacity="{0.3 + stage_num * 0.05}" />

'''

    if stage_num > 0:
        intensity = min(0.8, 0.3 + stage_num * 0.08)
        svg_content += f'''
  <polygon points="{base_size//2},{height//2 - 200} {base_size//2 - 250},{height//2 + 200} {base_size//2 + 250},{height//2 + 200}"
           fill="{accent}" opacity="{intensity * 0.3}" />

  <circle cx="{base_size//2}" cy="{height//2}" r="{50 + stage_num * 10}" 
          fill="{element}" opacity="{intensity * 0.2}" />
'''

    if stage_num >= 3:
        num_rays = 8 + (stage_num - 3) * 2
        for i in range(num_rays):
            angle = (2 * math.pi * i) / num_rays
            x1 = base_size // 2
            y1 = height // 2
            length = 200 + (stage_num - 3) * 30
            x2 = x1 + int(length * math.cos(angle))
            y2 = y1 + int(length * math.sin(angle))
            svg_content += f'''
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
        stroke="{element}" stroke-width="2" opacity="{0.2 + stage_num * 0.03}" />
'''

    svg_content += f'''
  <text x="{base_size - 100}" y="{height - 50}" 
        font-family="monospace" font-size="14" fill="{element}" opacity="0.5">
    {stage_name.upper()}
  </text>
</svg>'''

    output_path.write_text(svg_content)
    logger.info(f"SVG artwork generated for {stage_name}: {output_path}")


def generate_svg_image_for_stage(state: VideoPipelineState) -> Dict[str, Any]:
    """Generate SVG artwork for one musical stage.

    Lightweight alternative to SDXL that uses procedural SVG generation.
    No GPU or AI models required.

    Args:
        state: VideoPipelineState with stage_name

    Returns:
        State update: image_paths[stage_name] = Path
    """
    stage_name = state.get("stage_name", "ambient-intro")

    output_dir = Path.home() / ".cache" / "openmusic" / "video" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stage_name}.svg"

    try:
        _generate_svg_stage_artwork(stage_name, output_path)
        return {"image_paths": {stage_name: output_path}}

    except Exception as e:
        logger.error(f"SVG generation failed for {stage_name}: {e}")
        return {"image_paths": {stage_name: None}}