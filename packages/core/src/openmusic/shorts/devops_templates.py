"""Animated split-screen HTML template generator for DevOps/AI shorts.

Features:
- Particle canvas background (floating dots)
- Animated gradient background (slowly shifting)
- Code line-by-line reveal with staggered fade-in + slide-up
- Active line highlight that progresses through code
- Category badge slide-in
- Progress bar at bottom
- Title/description slide-up into tip pane
All animations are timed to fit exactly within ``duration`` seconds.
"""

from pathlib import Path
from typing import Optional

from openmusic.shorts.devops_content import DevOpsTip

PRISM_LANGUAGES = {
    "bash": "bash",
    "sh": "bash",
    "docker": "docker",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "python": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "go": "go",
    "groovy": "groovy",
    "ini": "ini",
    "nginx": "nginx",
    "prometheus": "promql",
    "promql": "promql",
    "cypher": "none",
}


def _get_prism_language(language: str) -> str:
    return PRISM_LANGUAGES.get(language.lower(), "bash")


def _render_prism_js() -> str:
    return """<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-docker.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-typescript.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-go.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-groovy.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-ini.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-nginx.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-promql.min.js"></script>
"""


def _render_prism_css() -> str:
    return """<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />"""


def _render_split_screen_css(duration: int = 20) -> str:
    return f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  width: 1080px;
  height: 1920px;
  overflow: hidden;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #020204;
}}

/* animated gradient background */
.gradient-bg {{
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #020204 0%, #0d1117 30%, #161b22 60%, #020204 100%);
  background-size: 400% 400%;
  animation: gradientShift {duration}s ease-in-out infinite;
  z-index: 0;
}}

@keyframes gradientShift {{
  0%   {{ background-position: 0% 50%; }}
  50%  {{ background-position: 100% 50%; }}
  100% {{ background-position: 0% 50%; }}
}}

/* particle canvas overlay */
#particle-canvas {{
  position: fixed;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}}

/* main grid */
.devops-container {{
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-rows: 64% 36%;
  height: 100%;
  width: 100%;
}}

/* code pane */
.code-pane {{
  font-family: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
  font-size: 38px;
  line-height: 1.5;
  padding: 56px 50px 36px 50px;
  overflow: hidden;
  background: rgba(26,27,38,0.85);
  backdrop-filter: blur(8px);
  color: #a9b1d6;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  position: relative;
  border-bottom: 1px solid rgba(122,162,247,0.15);
}}

.code-pane pre {{
  font-size: 34px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}}

/* individual code lines (transition used for JS-controlled stagger reveals) */
.code-line {{
  display: block;
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.5s ease-out, transform 0.5s ease-out;
  position: relative;
  padding: 2px 0;
}}

/* active line highlight */
.code-line.active {{
  background: linear-gradient(90deg, rgba(122,162,247,0.12) 0%, transparent 90%);
  border-left: 3px solid #7aa2f7;
  padding-left: 12px;
  animation: linePulse 1.5s ease-in-out infinite;
}}

@keyframes linePulse {{
  0%, 100% {{ border-left-color: #7aa2f7; }}
  50% {{ border-left-color: #c0caf5; }}
}}

.code-line.dimmed {{
  opacity: 0.5;
}}

/* category badge */
.category-badge {{
  position: absolute;
  top: 30px;
  left: 0;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 22px;
  font-weight: 600;
  color: #c8b898;
  letter-spacing: 3px;
  text-transform: uppercase;
  padding: 10px 24px;
  background: rgba(200,184,152,0.08);
  border-right: 2px solid rgba(200,184,152,0.3);
  border-top: 1px solid rgba(200,184,152,0.15);
  border-bottom: 1px solid rgba(200,184,152,0.15);
  border-radius: 0 8px 8px 0;
  transform: translateX(-120%);
  animation: badgeSlideIn 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: 0.3s;
}}

@keyframes badgeSlideIn {{
  0%   {{ transform: translateX(-120%); opacity: 0; }}
  60%  {{ transform: translateX(8px); opacity: 1; }}
  100% {{ transform: translateX(0); opacity: 1; }}
}}

/* progress bar */
.progress-bar {{
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #7aa2f7, #c0caf5, #7aa2f7);
  background-size: 200% 100%;
  animation: progressGrow {duration}s linear forwards, progressShimmer 2s ease-in-out infinite;
  width: 0%;
  z-index: 5;
}}

@keyframes progressGrow {{
  0%   {{ width: 0%; }}
  100% {{ width: 100%; }}
}}

@keyframes progressShimmer {{
  0%, 100% {{ background-position: 0% 50%; }}
  50% {{ background-position: 100% 50%; }}
}}

/* tip pane */
.tip-pane {{
  padding: 28px 60px 40px 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(2,2,4,0.92);
  position: relative;
  transform: translateY(100%);
  animation: tipSlideUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: 1.2s;
  overflow: hidden;
}}

@keyframes tipSlideUp {{
  0%   {{ transform: translateY(100%); opacity: 0; }}
  100% {{ transform: translateY(0); opacity: 1; }}
}}

.tip-title {{
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 42px;
  font-weight: 600;
  color: #c8b898;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  text-align: center;
  text-shadow: 0 0 40px rgba(200,184,152,0.12);
  opacity: 0;
  animation: fadeInUp 0.6s ease-out forwards;
  animation-delay: 1.6s;
  max-width: 960px;
}}

@keyframes fadeInUp {{
  0%   {{ opacity: 0; transform: translateY(16px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}

.tip-description {{
  font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 32px;
  font-weight: 300;
  color: #9ba3b8;
  line-height: 1.35;
  text-align: center;
  max-width: 920px;
  max-height: 86px; /* 2 lines at 32px * 1.35 */
  opacity: 0;
  animation: fadeInUp 0.6s ease-out forwards;
  animation-delay: 1.9s;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: opacity 0.6s ease, transform 0.6s ease;
}}

/* end card - fades in over tip content */
.end-card {{
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: radial-gradient(ellipse at center, rgba(122,162,247,0.05) 0%, transparent 70%);
  z-index: 10;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.8s ease;
}}

.end-card.show {{
  opacity: 1;
}}

.end-card .ring {{
  position: absolute;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  border: 1px solid rgba(200,184,152,0.15);
  animation: ringPulse 4s ease-in-out infinite;
}}

@keyframes ringPulse {{
  0%, 100% {{ transform: scale(1); opacity: 0.4; }}
  50% {{ transform: scale(1.08); opacity: 0.8; }}
}}

.end-card .logo {{
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 48px;
  font-weight: 700;
  color: #c8b898;
  letter-spacing: 6px;
  text-shadow: 0 0 60px rgba(200,184,152,0.2);
  margin-bottom: 16px;
  z-index: 1;
}}

.end-card .tagline {{
  font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 24px;
  font-weight: 300;
  color: #7aa2f7;
  letter-spacing: 8px;
  text-transform: uppercase;
  z-index: 1;
}}

@media (prefers-color-scheme: dark) {{
  * {{ color-scheme: dark; }}
}}
"""


def _render_particle_js(duration: int) -> str:
    """Render JavaScript for canvas particle system."""
    return f"""
const PARTICLE_COUNT = 80;
const DURATION = {duration};

function initParticles() {{
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = 1080;
  canvas.height = 1920;

  const particles = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {{
    particles.push({{
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      size: Math.random() * 3 + 1,
      speedX: (Math.random() - 0.5) * 0.4,
      speedY: -(Math.random() * 0.6 + 0.2),
      opacity: Math.random() * 0.5 + 0.1,
      pulse: Math.random() * Math.PI * 2,
    }});
  }}

  function animate() {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const time = Date.now() / 1000;
    for (const p of particles) {{
      p.x += p.speedX;
      p.y += p.speedY;
      p.pulse += 0.02;

      if (p.y < -10) {{ p.y = canvas.height + 10; p.x = Math.random() * canvas.width; }}
      if (p.x < -10) p.x = canvas.width + 10;
      if (p.x > canvas.width + 10) p.x = -10;

      const pulseOpacity = p.opacity * (0.7 + 0.3 * Math.sin(p.pulse));
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(122, 162, 247, ${{pulseOpacity * 0.5}})`;
      ctx.fill();

      // glow
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(122, 162, 247, ${{pulseOpacity * 0.08}})`;
      ctx.fill();
    }}
    requestAnimationFrame(animate);
  }}
  animate();
}}

document.addEventListener('DOMContentLoaded', initParticles);
"""


def _render_code_reveal_js(duration: int, line_count: int) -> str:
    """Render JavaScript that stages the code line-by-line reveal.

    Timing logic:
    - After Prism.js highlights the code, split lines into individual spans
    - Each line gets revealed with a staggered delay
    - The active line highlight moves down as lines appear
    - After all lines are revealed, show end card with branding
    """
    if line_count == 0:
        return ""

    reveal_start = 0.8
    reveal_end = max(duration - 2.0, reveal_start + 0.5)
    reveal_window = reveal_end - reveal_start
    stagger = min(reveal_window / max(line_count, 1), 0.8)

    return f"""
function initCodeReveal() {{
  const codeEl = document.querySelector('.code-pane code');
  if (!codeEl) return;

  // Split highlighted HTML by lines
  const html = codeEl.innerHTML;
  const lines = html.split('\\n');
  const wrapped = lines.map(line => '<span class="code-line">' + (line || ' ') + '</span>').join('\\n');
  codeEl.innerHTML = wrapped;

  const lineEls = document.querySelectorAll('.code-line');
  if (!lineEls.length) return;

  const lineCount = {line_count};
  const staggerDelay = {stagger};

  lineEls.forEach((line, i) => {{
    setTimeout(() => {{
      line.style.opacity = '1';
      line.style.transform = 'translateY(0)';

      lineEls.forEach(l => l.classList.remove('active'));
      line.classList.add('active');

      for (let j = 0; j < i; j++) {{
        lineEls[j].classList.add('dimmed');
      }}
    }}, {int(reveal_start * 1000)} + i * staggerDelay * 1000);
  }});

  const lastReveal = {int(reveal_start * 1000)} + (lineCount - 1) * staggerDelay * 1000;
  const endCardDelay = Math.min(lastReveal + 1500, ({duration} - 0.5) * 1000);

  setTimeout(() => {{
    const endCard = document.getElementById('end-card');
    if (endCard) endCard.classList.add('show');
    // Fade out tip content gracefully
    document.querySelectorAll('.tip-title, .tip-description').forEach(el => {{
      el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(16px)';
    }});
  }}, endCardDelay);
}}

// Wait for Prism.js to highlight, then init
if (document.querySelector('.code-pane code')) {{
  if (window.Prism) {{
    window.setTimeout(initCodeReveal, 600);
  }} else {{
    document.addEventListener('DOMContentLoaded', function() {{
      window.setTimeout(initCodeReveal, 800);
    }});
  }}
}}
"""


def render_devops_html(
    tip: DevOpsTip,
    svg_path: Optional[str] = None,
    duration: int = 20,
) -> str:
    code_lines = tip.code.strip().split("\n")
    line_count = len(code_lines)
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{_escape_html(tip.title)}</title>
{_render_prism_css()}
<style>
{_render_split_screen_css(duration)}
</style>
{_render_prism_js()}
</head>
<body>
<div class="gradient-bg"></div>
<canvas id="particle-canvas"></canvas>

<div class="devops-container">
  <div class="code-pane">
    <div class="category-badge">{_escape_html(tip.category)}</div>
    {_render_code_lines(tip.code, tip.language)}
    <div class="progress-bar"></div>
  </div>

  <div class="tip-pane">
    <div class="tip-title">{_escape_html(tip.title)}</div>
    <div class="tip-description">{_escape_html(tip.description)}</div>
    <div id="end-card" class="end-card">
      <div class="ring"></div>
      <div class="logo">✦ GRAPHWIZ</div>
      <div class="tagline">graphwiz.ai</div>
    </div>
  </div>
</div>

<script>
{_render_particle_js(duration)}
{_render_code_reveal_js(duration, line_count)}
</script>
</body>
</html>"""
    return html


def _render_code_lines(code: str, language: str) -> str:
    """Render code as a standard Prism.js code block (no line spans — JS handles splitting after Prism highlights)."""
    prism_lang = _get_prism_language(language)
    escaped_code = (
        code.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f'<pre class="language-{prism_lang}"><code>{escaped_code}</code></pre>'


def _render_code_block(code: str, language: str) -> str:
    """Legacy renderer used by render_code_only_html."""
    prism_lang = _get_prism_language(language)
    escaped_code = (
        code.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return f'<pre class="language-{prism_lang}"><code>{escaped_code}</code></pre>'


def render_tip_html(
    tip: DevOpsTip,
    svg_path: Optional[str] = None,
    duration: int = 20,
) -> str:
    return render_devops_html(tip=tip, svg_path=svg_path, duration=duration)


def render_code_only_html(
    code: str,
    language: str,
    title: str = "",
    duration: int = 20,
) -> str:
    temp_tip = DevOpsTip(
        title=title or "Code Snippet",
        code=code,
        language=language,
        description="",
        category="code",
        source="",
    )
    return render_devops_html(tip=temp_tip, svg_path=None, duration=duration)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
