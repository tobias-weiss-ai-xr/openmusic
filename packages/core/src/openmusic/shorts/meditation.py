"""Meditative sentence flow with smooth SVG-based transitions.

Generates a self-contained HTML page where meditative sentences cycle
with gentle crossfade transitions against an animated SVG background.
Designed for Playwright headless video recording or direct browser viewing.

The visual aesthetic is minimal, dark, and slow — inspired by ambient
visualization and meditation apps. Each sentence breathes for several
seconds before yielding to the next.
"""

from __future__ import annotations

from typing import Sequence

_MEDITATIVE_SENTENCES: list[str] = [
    "Breathe in stillness.",
    "You are exactly where you need to be.",
    "Let thoughts drift like clouds.",
    "This moment is all there is.",
    "Peace begins within.",
    "Surrender to the quiet.",
    "You are enough.",
    "Everything unfolds in its own time.",
    "Be present. Be still. Be free.",
    "The silence holds the answers.",
    "Release what you cannot control.",
    "Your breath is an anchor.",
    "There is no destination. Only this step.",
    "Let go of the need to know.",
    "You are not your thoughts.",
    "Rest in the awareness beneath it all.",
    "Each exhale releases tension.",
    "The present moment is perfect.",
    "You are held by the universe.",
    "Nothing is missing.",
    "Allow things to be as they are.",
    "Return to the breath.",
    "The mind is a guest. Let it pass.",
    "You are the sky. Everything else is weather.",
    "Stillness is your native language.",
    "There is nowhere to go. Nothing to do.",
    "This too shall pass.",
    "Be kind to yourself.",
    "Listen to the silence between sounds.",
    "Everything is connected.",
    "You are already whole.",
    "Grace is in the letting go.",
    "Infinite patience brings immediate results.",
    "The only way out is through.",
    "Love is the fabric of reality.",
    "You are a wave in an ocean of consciousness.",
    "Nothing real can be threatened.",
    "Awaken to the miracle of the ordinary.",
    "Your presence is your gift.",
    "Trust the process of life.",
    "Sit with what is.",
    "You are not alone.",
    "The universe speaks in whispers.",
    "Joy is your natural state.",
    "In the stillness, you find yourself.",
    "Every ending is a new beginning.",
    "Cultivate gratitude for this breath.",
    "You are the observer of your experience.",
    "Let your heart be at ease.",
    "The light you seek is within you.",
]


def _build_svg_background() -> str:
    return """  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="45%" r="60%">
      <stop offset="0%" stop-color="#0a0a1a"/>
      <stop offset="50%" stop-color="#060612"/>
      <stop offset="100%" stop-color="#020208"/>
    </radialGradient>
    <radialGradient id="auraGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="rgba(80,160,220,0.08)"/>
      <stop offset="60%" stop-color="rgba(80,160,220,0.03)"/>
      <stop offset="100%" stop-color="rgba(80,160,220,0)"/>
    </radialGradient>
    <filter id="softGlow">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <rect width="100%" height="100%" fill="url(#bgGlow)"/>

  <!-- Central aura -- pulsing sphere of light -->
  <circle cx="50%" cy="40%" r="35%" fill="url(#auraGrad)" filter="url(#softGlow)">
    <animate attributeName="r" values="30%;38%;32%;36%;30%"
      dur="12s" repeatCount="indefinite" calcMode="spline"
      keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/>
  </circle>

  <!-- Floating concentric rings -->
  <g opacity="0.15">
    <circle cx="50%" cy="40%" r="15%" fill="none" stroke="rgba(140,200,255,0.12)" stroke-width="0.5">
      <animate attributeName="r" values="10%;25%;10%"
        dur="15s" repeatCount="indefinite" calcMode="spline"
        keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
      <animate attributeName="opacity" values="0.2;0.05;0.2"
        dur="15s" repeatCount="indefinite"/>
    </circle>
    <circle cx="50%" cy="40%" r="20%" fill="none" stroke="rgba(140,200,255,0.08)" stroke-width="0.3">
      <animate attributeName="r" values="18%;38%;18%"
        dur="20s" repeatCount="indefinite" calcMode="spline"
        keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
      <animate attributeName="opacity" values="0.15;0.02;0.15"
        dur="20s" repeatCount="indefinite"/>
    </circle>
    <circle cx="50%" cy="40%" r="25%" fill="none" stroke="rgba(200,160,255,0.06)" stroke-width="0.3">
      <animate attributeName="r" values="25%;50%;25%"
        dur="25s" repeatCount="indefinite" calcMode="spline"
        keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
    </circle>
  </g>

  <!-- Slow rotating beam -->
  <g opacity="0.04">
    <line x1="50%" y1="40%" x2="50%" y2="-10%"
      stroke="rgba(140,200,255,0.3)" stroke-width="1">
      <animateTransform attributeName="transform" type="rotate"
        from="0" to="360" dur="60s" repeatCount="indefinite"/>
    </line>
    <line x1="50%" y1="40%" x2="50%" y2="-10%"
      stroke="rgba(200,160,255,0.2)" stroke-width="0.5">
      <animateTransform attributeName="transform" type="rotate"
        from="0" to="360" dur="45s" repeatCount="indefinite"/>
    </line>
  </g>

  <!-- Ambient floating particles -->
  <g opacity="0.25">
    <circle cx="25%" cy="55%" r="1.5" fill="rgba(140,200,255,0.4)">
      <animate attributeName="cy" values="55%;45%;55%"
        dur="14s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.2;0.5;0.2"
        dur="14s" repeatCount="indefinite"/>
    </circle>
    <circle cx="70%" cy="50%" r="1" fill="rgba(200,160,255,0.3)">
      <animate attributeName="cy" values="50%;38%;50%"
        dur="18s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.1;0.4;0.1"
        dur="18s" repeatCount="indefinite"/>
    </circle>
    <circle cx="35%" cy="65%" r="1.2" fill="rgba(160,220,200,0.3)">
      <animate attributeName="cy" values="65%;52%;65%"
        dur="12s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.15;0.45;0.15"
        dur="12s" repeatCount="indefinite"/>
    </circle>
    <circle cx="60%" cy="60%" r="0.8" fill="rgba(140,200,255,0.3)">
      <animate attributeName="cy" values="60%;48%;60%"
        dur="16s" repeatCount="indefinite"/>
    </circle>
    <circle cx="45%" cy="48%" r="1.8" fill="rgba(200,180,255,0.2)">
      <animate attributeName="cy" values="48%;35%;48%"
        dur="22s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0.05;0.3;0.05"
        dur="22s" repeatCount="indefinite"/>
    </circle>
    <circle cx="80%" cy="70%" r="1" fill="rgba(180,220,255,0.2)">
      <animate attributeName="cy" values="70%;55%;70%"
        dur="20s" repeatCount="indefinite"/>
    </circle>
    <circle cx="20%" cy="42%" r="0.6" fill="rgba(220,200,255,0.2)">
      <animate attributeName="cy" values="42%;30%;42%"
        dur="17s" repeatCount="indefinite"/>
    </circle>
  </g>

  <!-- Thin horizontal ambient line -->
  <line x1="0" y1="85%" x2="100%" y2="85%"
    stroke="rgba(140,200,255,0.04)" stroke-width="0.5">
    <animate attributeName="opacity" values="0.02;0.06;0.02"
      dur="8s" repeatCount="indefinite"/>
  </line>"""


def render_meditation_flow(
    sentences: Sequence[str] | None = None,
    duration_per_sentence: int = 8,
    portrait: bool = True,
) -> str:
    """Generate a self-contained HTML page with transitioning meditative sentences.

    Each sentence fades in gently, holds for several seconds, then fades
    out before the next sentence appears. The cycle repeats indefinitely.

    Args:
        sentences: List of meditative sentences. Defaults to curated list.
        duration_per_sentence: Seconds each sentence is visible.
        portrait: If True, 1080x1920 portrait layout. If False, 1920x1080.

    Returns:
        Complete HTML document as a string.
    """
    if sentences is None:
        sentences = _MEDITATIVE_SENTENCES

    w, h = ("1080", "1920") if portrait else ("1920", "1080")
    body_dim = f"width:{w}px;height:{h}px"

    # Build CSS keyframes for each sentence
    # Total animation cycle = len(sentences) * duration_per_sentence
    # Each sentence: fade in (10%), hold (60%), fade out (15%), hidden (15%)
    total_duration = len(sentences) * duration_per_sentence
    step_pct = 100.0 / len(sentences)

    # Animation keyframes: each sentence gets a portion of the full cycle
    sentence_styles: list[str] = []
    for i in range(len(sentences)):
        start = (i * step_pct)
        fade_in = start + step_pct * 0.1
        hold_end = start + step_pct * 0.75
        fade_out = start + step_pct * 0.9
        visible = start + step_pct * 0.02  # tiny initial hold before fade-in

        sentence_styles.append(
            f""".s{i} {{
  animation: cycle-{i} {total_duration}s ease-in-out infinite;
  opacity: 0;
}}
@keyframes cycle-{i} {{
  {start:.2f}% {{ opacity: 0; transform: translateY(8px); }}
  {visible:.2f}% {{ opacity: 0; transform: translateY(8px); }}
  {fade_in:.2f}% {{ opacity: 1; transform: translateY(0); }}
  {hold_end:.2f}% {{ opacity: 1; transform: translateY(0); }}
  {fade_out:.2f}% {{ opacity: 0; transform: translateY(-8px); }}
  100% {{ opacity: 0; transform: translateY(-8px); }}
}}"""
        )

    text_class = "text-portrait" if portrait else "text-landscape"

    # Build the sentence elements
    sentence_elements = []
    for i, sentence in enumerate(sentences):
        escaped = (
            sentence.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        sentence_elements.append(
            f'  <div class="sentence s{i} {text_class}">{escaped}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={w}, height={h}">
<title>Meditative Flow</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  {body_dim}
  background: #020208;
  overflow: hidden;
  position: relative;
}}
svg {{
  position: absolute;
  top: 0; left: 0;
  width: {w}px; height: {h}px;
  display: block;
}}

/* ── Sentence container ── */
.sentence-container {{
  position: absolute;
  top: 0; left: 0;
  width: {w}px; height: {h}px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;
  padding: 0 80px;
}}

/* ── Individual sentence ── */
.sentence {{
  position: absolute;
  width: 80%;
  text-align: center;
  pointer-events: none;
}}

.text-portrait {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 56px;
  font-weight: 300;
  font-style: italic;
  color: #c8d8e8;
  line-height: 1.4;
  letter-spacing: 1px;
  text-shadow:
    0 0 60px rgba(140,200,255,0.08),
    0 0 120px rgba(140,200,255,0.04),
    0 0 200px rgba(140,200,255,0.02);
}}

.text-landscape {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 36px;
  font-weight: 300;
  font-style: italic;
  color: #c8d8e8;
  line-height: 1.5;
  letter-spacing: 1px;
  text-shadow:
    0 0 40px rgba(140,200,255,0.08),
    0 0 80px rgba(140,200,255,0.04);
}}

/* ── Soft pulse on the text layer ── */
.text-landscape, .text-portrait {{
  animation: textBreath {total_duration}s ease-in-out infinite;
}}
@keyframes textBreath {{
  0%, 100% {{ filter: brightness(0.95); }}
  50% {{ filter: brightness(1.05); }}
}}

{chr(10).join(sentence_styles)}
</style>
</head>
<body>

<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {w} {h}" width="{w}" height="{h}">
{_build_svg_background()}
</svg>

<div class="sentence-container">
{chr(10).join(sentence_elements)}
</div>

</body>
</html>"""
