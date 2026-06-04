"""Split-screen HTML template generator for DevOps/AI tips.

Renders code snippets with syntax highlighting (Prism.js) and
explanatory text in a 70/30 split layout for vertical 9:16 shorts.
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
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-promql.min.js"></script>"""


def _render_prism_css() -> str:
    return """<link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />"""


def _render_split_screen_css(duration: int = 20) -> str:
    return f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  width: 1920px;
  height: 1080px;
  background: #020204;
  overflow: hidden;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
}}

.devops-container {{
  display: grid;
  grid-template-rows: 70% 30%;
  height: 1920px;
  width: 1080px;
  background: linear-gradient(180deg, #0a0a0c 0%, #020204 100%);
}}

.code-pane {{
  font-family: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
  font-size: 42px;
  line-height: 1.6;
  padding: 50px;
  overflow: hidden;
  background: #1a1b26;
  color: #a9b1d6;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}

.code-pane pre {{
  font-size: 38px;
  white-space: pre-wrap;
  word-break: break-word;
}}

.tip-pane {{
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: #020204;
  animation: tipFade {duration}s ease-in-out forwards;
  opacity: 2%;
}}

.tip-title {{
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 48px;
  font-weight: 600;
  color: #c8b898;
  letter-spacing: 1px;
  margin-bottom: 20px;
  text-align: center;
  text-shadow: 0 0 40px rgba(200,184,152,0.15);
}}

.tip-description {{
  font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 38px;
  font-weight: 300;
  color: #9ba3b8;
  line-height: 1.4;
  text-align: center;
}}

.category-badge {{
  position: absolute;
  top: 50px;
  left: 50px;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 24px;
  font-weight: 500;
  color: #7aa2f7;
  letter-spacing: 2px;
  text-transform: uppercase;
  padding: 15px 25px;
  background: rgba(122,162,247,0.1);
  border-radius: 8px;
  border: 1px solid rgba(122,162,247,0.2);
}}

@keyframes tipFade {{
  0%   {{ opacity: 0.03; }}
  10%  {{ opacity: 0.03; }}
  15%  {{ opacity: 1.0; }}
  70%  {{ opacity: 1.0; }}
  80%  {{ opacity: 1.0; }}
  90%  {{ opacity: 0.03; }}
  100% {{ opacity: 0.03; }}
}}

@media (prefers-color-scheme: dark) {{
  * {{
    color-scheme: dark;
  }}
}}
"""


def render_devops_html(
    tip: DevOpsTip,
    svg_path: Optional[str] = None,
    duration: int = 20,
) -> str:
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{tip.title}</title>
{_render_prism_css()}
<style>
{_render_split_screen_css(duration)}
</style>
{_render_prism_js()}
</head>
<body>

<div class="devops-container">
  <div class="category-badge">{tip.category}</div>

  <div class="code-pane">{_render_code_block(tip.code, tip.language)}</div>

  <div class="tip-pane">
    <div class="tip-title">{tip.title}</div>
    <div class="tip-description">{tip.description}</div>
  </div>
</div>

</body>
</html>"""

    return html


def _render_code_block(code: str, language: str) -> str:
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