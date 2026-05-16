"""Procedural SVG cover generator driven by mix identity."""
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class MixCoverConfig:
    key: str = "Dm"
    bpm: int = 125
    length: float = 7200.0
    title: str = ""
    artist: str = "OpenMusic"
    output_path: Optional[str] = None


def _key_to_hue(key: str) -> int:
    root = key.lower()
    if root.endswith("minor"):
        root = root[:-5]
    elif root.endswith("m"):
        root = root[:-1]
    mapping = {
        "c": 0, "c#": 30, "db": 30, "d": 60, "d#": 90, "eb": 90,
        "e": 120, "f": 150, "f#": 180, "gb": 180, "g": 210,
        "g#": 240, "ab": 240, "a": 270, "a#": 300, "bb": 300, "b": 330,
    }
    return mapping.get(root, 0)


def _is_minor(key: str) -> bool:
    lower = key.lower()
    return lower.endswith("minor") or (lower.endswith("m") and not lower.endswith("maj"))


def _seed_from_config(config: MixCoverConfig) -> int:
    data = f"{config.key}{config.bpm}{config.length:.0f}{config.title}"
    return int(hashlib.sha256(data.encode()).hexdigest()[:16], 16)


def _build_background(hue: int, saturation: int, length: float) -> str:
    blur = 60 + (length / 120)
    mid = f"hsl({hue}, {saturation}%, 8%)"
    dark = f"hsl({hue}, {saturation}%, 5%)"
    return f"""  <radialGradient id="bg" cx="50%" cy="50%" r="{blur}">
    <stop offset="0%" stop-color="{dark}"/>
    <stop offset="60%" stop-color="{mid}"/>
    <stop offset="100%" stop-color="#040408"/>
  </radialGradient>
  <rect width="1920" height="1080" fill="url(#bg)"/>"""


def _build_beams(rng: random.Random, bpm: int, hue: int) -> str:
    count = bpm // 20 + 6
    lines = []
    for i in range(count):
        angle = rng.randint(0, 359)
        opacity = rng.uniform(0.03, 0.08)
        lines.append(
            f'    <line x1="960" y1="540" x2="960" y2="-100" '
            f'stroke="#1a3a6a" stroke-width="1" opacity="{opacity:.2f}" '
            f'transform="rotate({angle} 960 540)"/>'
        )
    dur = 120 - bpm // 5
    return f"""
  <g opacity="0.06">
    <animateTransform attributeName="transform" type="rotate" from="0 960 540" to="360 960 540" dur="{dur}s" repeatCount="indefinite"/>
{"".join(lines)}
  </g>"""


def _build_rings(rng: random.Random, length: float, hue: int, saturation: int) -> str:
    tier = min(3, max(1, int(length // 3600)))
    radii = [420 - i * 120 for i in range(tier + 1)]
    colors = [
        f"hsl({hue}, {saturation}%, 45%)",
        f"hsl({hue+30}, {saturation-5}%, 40%)",
        f"hsl({hue+60}, {saturation-10}%, 35%)",
        f"hsl({hue-20}, {saturation}%, 50%)",
    ]
    elements = []
    for r, color in zip(radii, colors):
        offset = rng.uniform(0.8, 1.5)
        dur_op = 10 + offset * 4
        dur_r = 8 + offset * 3
        elements.append(
            f'    <circle cx="960" cy="540" r="{r}" fill="none" stroke="{color}" stroke-width="1.2" opacity="0.45">'
            f'<animate attributeName="opacity" values="0.45;0.25;0.5;0.3;0.45" dur="{dur_op:.1f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="{r};{r+10};{r-5};{r+8};{r}" dur="{dur_r:.1f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
    return "".join(elements)


def _build_core(hue: int, saturation: int) -> str:
    color = f"hsl({hue}, {saturation}%, 55%)"
    return f"""  <circle cx="960" cy="540" r="50" fill="hsl({hue}, {saturation}%, 20%)" opacity="0.6">
    <animate attributeName="r" values="50;70;45;60;50" dur="15s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;0.3;0.7;0.4;0.6" dur="12s" repeatCount="indefinite"/>
  </circle>
  <circle cx="960" cy="540" r="4" fill="{color}" opacity="0.7">
    <animate attributeName="opacity" values="0.7;0.4;0.8;0.5;0.7" dur="8s" repeatCount="indefinite"/>
  </circle>"""


def _build_text(key: str, bpm: int, length: float, hue: int) -> str:
    if length >= 7200:
        weight = "200"
    elif length >= 3600:
        weight = "100"
    else:
        weight = "100"
    color = f"hsl({hue}, 30%, 40%)"
    return f"""  <text x="960" y="540" text-anchor="middle" dominant-baseline="central"
        font-family="'Helvetica Neue', 'Arial', sans-serif"
        font-size="72" font-weight="{weight}" letter-spacing="35"
        fill="{color}" opacity="0.45">
      {key} · {bpm} BPM
      <animate attributeName="opacity" values="0.45;0.25;0.5;0.3;0.45" dur="20s" repeatCount="indefinite"/>
    </text>"""


def _build_particles(rng: random.Random, bpm: int, hue: int) -> str:
    count = bpm // 5
    circles = []
    for i in range(count):
        cx = rng.randint(50, 1870)
        cy = rng.randint(50, 1030)
        r = rng.uniform(0.5, 1.5)
        dur = rng.randint(10, 25)
        color = f"hsl({hue + rng.randint(-20, 20)}, 40%, 50%)"
        begin = rng.uniform(0, 10)
        circles.append(
            f'    <circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.15;0.3;0.15;0" dur="{dur}s" repeatCount="indefinite" begin="{begin:.1f}s"/>'
            f'</circle>'
        )
    return "".join(circles)


class CoverGenerator:
    def __init__(self, config: MixCoverConfig):
        self.config = config
        self.seed = _seed_from_config(config)
        self.rng = random.Random(self.seed)
        self.hue = _key_to_hue(config.key)
        self.saturation = 40 if _is_minor(config.key) else 55

    def generate_svg(self) -> str:
        bg = _build_background(self.hue, self.saturation, self.config.length)
        beams = _build_beams(self.rng, self.config.bpm, self.hue)
        rings = _build_rings(self.rng, self.config.length, self.hue, self.saturation)
        core = _build_core(self.hue, self.saturation)
        text = _build_text(self.config.key, self.config.bpm, self.config.length, self.hue)
        particles = _build_particles(self.rng, self.config.bpm, self.hue)
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080">'
            + '<defs>'
            + '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
            + '<feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur"/>'
            + '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
            + '</filter>'
            + '</defs>'
            + bg
            + beams
            + '<g>' + rings + '</g>'
            + core
            + particles
            + text
            + '</svg>'
        )

    def save_svg(self, path: str) -> None:
        Path(path).write_text(self.generate_svg())

    def save_png(self, path: str) -> None:
        import subprocess
        subprocess.run(
            ["convert", "-density", "150", f"svg:{self.generate_svg()}", "-colorspace", "sRGB", path],
            capture_output=True, check=True,
        )