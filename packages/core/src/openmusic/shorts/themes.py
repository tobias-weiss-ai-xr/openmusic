"""Themed visual templates for artistic short video clips.

Each theme returns a self-contained HTML page with embedded CSS animations
and SVG visual elements, designed for Playwright headless video recording.
Supports both portrait (1080x1920) and landscape (1920x1080) layouts.
"""

from __future__ import annotations

from openmusic.shorts.quotes import StoicQuote

THEME_NAMES = ["solar_flare", "oceanic_tones", "urban_decay", "neon_dusk"]


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ─── Solar Flare ────────────────────────────────────────────────────────────

def solar_flare_html(quote: StoicQuote, duration: int = 30, portrait: bool = True) -> str:
    """Warm amber/gold celestial theme — radiant corona, rising particles."""
    text = _esc(quote.text)
    author = _esc(quote.author)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{'1080px; height:1920px' if portrait else '1920px; height:1080px'};
  background: radial-gradient(ellipse 80% 60% at 50% 25%, #3a1a08 0%, #1a0a04 40%, #080202 100%);
  overflow:hidden; position:relative; }}
/* ── Corona rings ── */
.corona {{ position:absolute; top:15%; left:50%; transform:translateX(-50%); }}
.corona-ring {{ position:absolute; border-radius:50%;
  border:1px solid rgba(232,180,80,0.15);
  animation: pulse-ring 4s ease-in-out infinite; }}
.corona-ring:nth-child(1) {{ width:300px; height:300px; animation-delay:0s; }}
.corona-ring:nth-child(2) {{ width:450px; height:450px; animation-delay:0.8s; border-color:rgba(232,180,80,0.10); }}
.corona-ring:nth-child(3) {{ width:620px; height:620px; animation-delay:1.6s; border-color:rgba(232,180,80,0.06); }}
.corona-ring:nth-child(4) {{ width:800px; height:800px; animation-delay:2.4s; border-color:rgba(200,120,40,0.04); }}
@keyframes pulse-ring {{
  0%,100% {{ transform:translate(-50%,-50%) scale(1); opacity:0.4; }}
  50% {{ transform:translate(-50%,-50%) scale(1.25); opacity:0.8; }}
}}
/* ── Core glow ── */
.core {{ position:absolute; top:15%; left:50%; transform:translate(-50%,-50%);
  width:120px; height:120px; border-radius:50%;
  background:radial-gradient(circle, #f0c040 0%, #d08020 30%, transparent 70%);
  animation: core-pulse 3s ease-in-out infinite; }}
@keyframes core-pulse {{
  0%,100% {{ transform:translate(-50%,-50%) scale(1); opacity:0.8; }}
  50% {{ transform:translate(-50%,-50%) scale(1.15); opacity:1; }}
}}
/* ── Particles ── */
.particle {{ position:absolute; width:3px; height:3px; border-radius:50%;
  background:#e8a040; opacity:0; }}
.p1 {{ left:42%; top:30%; animation:rise 6s 0s infinite; }}
.p2 {{ left:48%; top:25%; animation:rise 7s 0.5s infinite; width:2px; height:2px; }}
.p3 {{ left:55%; top:28%; animation:rise 5s 1s infinite; background:#f0d080; }}
.p4 {{ left:38%; top:35%; animation:rise 8s 0.3s infinite; width:4px; height:4px; }}
.p5 {{ left:60%; top:32%; animation:rise 6.5s 1.5s infinite; background:#f0c060; }}
.p6 {{ left:45%; top:22%; animation:rise 7.5s 2s infinite; width:2px; height:2px; }}
.p7 {{ left:52%; top:27%; animation:rise 5.5s 0.8s infinite; }}
.p8 {{ left:35%; top:33%; animation:rise 9s 1.2s infinite; background:#ffd080; }}
@keyframes rise {{
  0% {{ transform:translateY(0) scale(0); opacity:0; }}
  20% {{ opacity:1; }}
  100% {{ transform:translateY(-300px) scale(1.5); opacity:0; }}
}}
/* ── Solar flare burst ── */
.flare {{ position:absolute; top:15%; left:50%; transform:translate(-50%,-50%);
  width:200px; height:4px; background:linear-gradient(90deg,transparent,#e8c060,transparent);
  animation: flare-rotate 8s linear infinite; transform-origin:center; }}
@keyframes flare-rotate {{ 0% {{ rotate:0deg; }} 100% {{ rotate:360deg; }} }}
.flare2 {{ composes:flare; width:160px; height:2px; animation:flare-rotate 12s linear infinite reverse; }}
/* ── Quote overlay ── */
.quote-overlay {{ position:absolute; top:0; left:0;
  width:{'1080px; height:1920px' if portrait else '1920px; height:1080px'};
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  pointer-events:none; z-index:10;
  animation: fadeIn 30s ease-in-out forwards; }}
@keyframes fadeIn {{
  0% {{ opacity:0; }} 12% {{ opacity:0; }} 18% {{ opacity:1; }}
  70% {{ opacity:1; }} 85% {{ opacity:1; }} 95% {{ opacity:0; }} 100% {{ opacity:0; }}
}}
.quote-text {{ font-family:Georgia,'Times New Roman',serif;
  font-size:{'64px' if portrait else '36px'}; font-weight:400; font-style:italic;
  color:#e8c878; text-align:center; line-height:1.4; letter-spacing:1px;
  text-shadow:0 0 60px rgba(232,200,120,0.15), 0 0 120px rgba(232,200,120,0.08);
  max-width:{'900px' if portrait else '1200px'}; margin-bottom:{'28px' if portrait else '20px'};
  padding:0 {'60px' if portrait else '40px'}; }}
.quote-attribution {{ font-family:Futura,'Century Gothic','Avenir Next',sans-serif;
  font-size:{'20px' if portrait else '14px'}; font-weight:300; letter-spacing:{'10px' if portrait else '6px'};
  color:#8a6a3a; text-transform:uppercase; margin-top:{'12px' if portrait else '8px'}; }}
</style></head><body>
<div class="corona"><div class="corona-ring"></div><div class="corona-ring"></div><div class="corona-ring"></div><div class="corona-ring"></div></div>
<div class="core"></div>
<div class="particle p1"></div><div class="particle p2"></div><div class="particle p3"></div>
<div class="particle p4"></div><div class="particle p5"></div><div class="particle p6"></div>
<div class="particle p7"></div><div class="particle p8"></div>
<div class="flare"></div>
<div class="quote-overlay">
  <div class="quote-text">&ldquo;{text}&rdquo;</div>
  <div class="quote-attribution">&mdash; {author}</div>
</div>
</body></html>"""
    return html


# ─── Oceanic Tones ──────────────────────────────────────────────────────────

def oceanic_tones_html(quote: StoicQuote, duration: int = 30, portrait: bool = True) -> str:
    """Deep ocean theme — undulating waves, drifting bioluminescent particles."""
    text = _esc(quote.text)
    author = _esc(quote.author)

    w = "1080px" if portrait else "1920px"
    h = "1920px" if portrait else "1080px"
    wave_svg_w = "1080" if portrait else "1920"
    wave_svg_h = "400" if portrait else "300"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{w}; height:{h};
  background:linear-gradient(180deg, #061224 0%, #0a1a38 25%, #061830 50%, #030c1a 80%, #01060e 100%);
  overflow:hidden; position:relative; }}
.waves {{ position:absolute; bottom:{'700px' if portrait else '350px'}; left:0; width:100%; height:{wave_svg_h}px; }}
.wave-svg {{ width:100%; height:100%; display:block; }}
@keyframes drift {{ 0% {{ transform:translateX(0); }} 100% {{ transform:translateX(-50px); }} }}
/* ── Bioluminescent particles ── */
.bio {{ position:absolute; border-radius:50%;
  box-shadow:0 0 8px rgba(100,220,255,0.4), 0 0 20px rgba(100,220,255,0.1);
  animation: float-up 8s ease-in-out infinite; opacity:0; }}
.b1 {{ width:5px; height:5px; left:25%; bottom:60%; background:#88eeff; animation-delay:0s; }}
.b2 {{ width:3px; height:3px; left:45%; bottom:55%; background:#66ddff; animation-delay:1.5s; }}
.b3 {{ width:6px; height:6px; left:65%; bottom:65%; background:#aaeeff; animation-delay:3s; }}
.b4 {{ width:4px; height:4px; left:35%; bottom:70%; background:#55ccff; animation-delay:0.8s; }}
.b5 {{ width:3px; height:3px; left:55%; bottom:58%; background:#88eeff; animation-delay:2.2s; }}
.b6 {{ width:7px; height:7px; left:75%; bottom:62%; background:#77ddff; animation-delay:4s; }}
.b7 {{ width:4px; height:4px; left:15%; bottom:68%; background:#99eeff; animation-delay:1s; }}
.b8 {{ width:5px; height:5px; left:85%; bottom:56%; background:#66eeff; animation-delay:3.5s; }}
@keyframes float-up {{
  0% {{ transform:translateY(0) scale(0); opacity:0; }}
  20% {{ opacity:0.8; }}
  80% {{ opacity:0.6; }}
  100% {{ transform:translateY(-200px) scale(1.2); opacity:0; }}
}}
/* ── Caustic light beams ── */
.light {{ position:absolute; width:2px; height:200px;
  background:linear-gradient(transparent,rgba(100,200,255,0.06),transparent);
  animation: sway 6s ease-in-out infinite; }}
.l1 {{ left:30%; top:5%; animation-delay:0s; }}
.l2 {{ left:50%; top:8%; animation-delay:1s; }}
.l3 {{ left:70%; top:3%; animation-delay:2s; height:150px; }}
@keyframes sway {{
  0%,100% {{ transform:translateX(0) rotate(0deg); opacity:0.3; }}
  50% {{ transform:translateX(20px) rotate(3deg); opacity:0.7; }}
}}
/* ── Quote ── */
.quote-overlay {{ position:absolute; top:0; left:0; width:{w}; height:{h};
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  pointer-events:none; z-index:10;
  animation: fadeIn 30s ease-in-out forwards; }}
@keyframes fadeIn {{
  0% {{ opacity:0; }} 12% {{ opacity:0; }} 18% {{ opacity:1; }}
  70% {{ opacity:1; }} 85% {{ opacity:1; }} 95% {{ opacity:0; }} 100% {{ opacity:0; }}
}}
.quote-text {{ font-family:Georgia,'Times New Roman',serif;
  font-size:{'64px' if portrait else '36px'}; font-weight:400; font-style:italic;
  color:#78c8d8; text-align:center; line-height:1.4; letter-spacing:1px;
  text-shadow:0 0 60px rgba(120,200,216,0.12), 0 0 120px rgba(120,200,216,0.06);
  max-width:{'900px' if portrait else '1200px'}; margin-bottom:{'28px' if portrait else '20px'};
  padding:0 {'60px' if portrait else '40px'}; }}
.quote-attribution {{ font-family:Futura,'Century Gothic','Avenir Next',sans-serif;
  font-size:{'20px' if portrait else '14px'}; font-weight:300; letter-spacing:{'10px' if portrait else '6px'};
  color:#4a8a9a; text-transform:uppercase; margin-top:{'12px' if portrait else '8px'}; }}
</style></head><body>
<svg class="wave-svg" viewBox="0 0 {wave_svg_w} {wave_svg_h}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;bottom:{'700px' if portrait else '350px'};left:0;">
  <defs><linearGradient id="w1" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="rgba(40,120,160,0.15)"/><stop offset="100%" stop-color="rgba(40,120,160,0)"/></linearGradient></defs>
  <path d="M0 200 Q100 100 200 180 T400 160 T600 190 T800 150 T1000 180 T1200 160 T1400 190 T1600 150 T1800 180 T{wave_svg_w} 160 L{wave_svg_w} {wave_svg_h} L0 {wave_svg_h} Z" fill="url(#w1)">
    <animate attributeName="d" dur="6s" repeatCount="indefinite"
      values="M0 200 Q100 100 200 180 T400 160 T600 190 T800 150 T1000 180 T1200 160 T1400 190 T1600 150 T1800 180 T{wave_svg_w} 160 L{wave_svg_w} {wave_svg_h} L0 {wave_svg_h} Z;
              M0 180 Q100 200 200 150 T400 190 T600 160 T800 180 T1000 150 T1200 190 T1400 160 T1600 180 T1800 150 T{wave_svg_w} 180 L{wave_svg_w} {wave_svg_h} L0 {wave_svg_h} Z;
              M0 200 Q100 100 200 180 T400 160 T600 190 T800 150 T1000 180 T1200 160 T1400 190 T1600 150 T1800 180 T{wave_svg_w} 160 L{wave_svg_w} {wave_svg_h} L0 {wave_svg_h} Z"/>
  </path>
  <path d="M0 240 Q150 160 300 220 T600 200 T900 230 T1200 190 T1500 220 T1800 200 T{wave_svg_w} 220 L{wave_svg_w} {wave_svg_h} L0 {wave_svg_h} Z" fill="rgba(30,100,140,0.08)">
    <animate attributeName="d" dur="8s" repeatCount="indefinite"
      values="M0 240 Q150 160 300 220 T600 200 T900 230 T1200 190 T1500 220 T1800 200 T{wave_svg_w} 220 L...;
              M0 220 Q150 240 300 190 T600 230 T900 200 T1200 240 T1500 200 T1800 230 T{wave_svg_w} 200 L...;
              M0 240 Q150 160 300 220 T600 200 T900 230 T1200 190 T1500 220 T1800 200 T{wave_svg_w} 220 L..."/>
  </path>
</svg>
<div class="bio b1"></div><div class="bio b2"></div><div class="bio b3"></div>
<div class="bio b4"></div><div class="bio b5"></div><div class="bio b6"></div>
<div class="bio b7"></div><div class="bio b8"></div>
<div class="light l1"></div><div class="light l2"></div><div class="light l3"></div>
<div class="quote-overlay">
  <div class="quote-text">&ldquo;{text}&rdquo;</div>
  <div class="quote-attribution">&mdash; {author}</div>
</div>
</body></html>"""


# ─── Urban Decay ────────────────────────────────────────────────────────────

def urban_decay_html(quote: StoicQuote, duration: int = 30, portrait: bool = True) -> str:
    """Industrial brutalist theme — geometric grid, scan lines, rust tones."""
    text = _esc(quote.text)
    author = _esc(quote.author)

    w = "1080px" if portrait else "1920px"
    h = "1920px" if portrait else "1080px"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{w}; height:{h};
  background:linear-gradient(180deg, #1a1410 0%, #120e0a 40%, #0a0806 100%);
  overflow:hidden; position:relative; }}
/* ── Industrial grid ── */
.grid {{ position:absolute; top:0; left:0; width:100%; height:100%;
  background-image:
    linear-gradient(rgba(180,120,60,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(180,120,60,0.06) 1px, transparent 1px);
  background-size:{'80px 80px' if portrait else '100px 100px'}; }}
/* ── Geometric blocks ── */
.block {{ position:absolute; border:1px solid rgba(180,120,60,0.12); background:rgba(180,120,60,0.03); }}
.blk1 {{ width:{'300px' if portrait else '400px'}; height:{'200px' if portrait else '250px'}; top:8%; left:{'30%' if portrait else '35%'};
  animation: block-pulse 6s ease-in-out infinite; }}
.blk2 {{ width:{'200px' if portrait else '320px'}; height:{'200px' if portrait else '250px'}; top:8%; left:{'55%' if portrait else '60%'};
  border-color:rgba(180,120,60,0.08); animation: block-pulse 6s ease-in-out infinite reverse; }}
.blk3 {{ width:{'400px' if portrait else '500px'}; height:2px; top:{'28%' if portrait else '20%'}; left:{'20%' if portrait else '30%'};
  background:rgba(200,140,60,0.08); border:none; animation: scan-h 4s ease-in-out infinite; }}
@keyframes block-pulse {{
  0%,100% {{ opacity:0.5; }}
  50% {{ opacity:1; }}
}}
@keyframes scan-h {{
  0%,100% {{ transform:scaleX(0.8); opacity:0.3; }}
  50% {{ transform:scaleX(1.2); opacity:0.7; }}
}}
/* ── Vertical struts ── */
.strut {{ position:absolute; width:1px; background:rgba(160,100,40,0.08); }}
.s1 {{ height:{'500px' if portrait else '400px'}; top:5%; left:{'15%' if portrait else '10%'}; }}
.s2 {{ height:{'600px' if portrait else '450px'}; top:3%; left:{'85%' if portrait else '88%'}; }}
.s3 {{ height:{'400px' if portrait else '350px'}; top:8%; left:{'5%' if portrait else '3%'}; }}
/* ── Scan line ── */
.scanline {{ position:absolute; left:0; width:100%; height:3px;
  background:linear-gradient(90deg,transparent,rgba(200,140,60,0.12),transparent);
  animation: scan-down {'12s' if portrait else '10s'} linear infinite; }}
@keyframes scan-down {{
  0% {{ top:0; opacity:0; }}
  10% {{ opacity:1; }}
  90% {{ opacity:1; }}
  100% {{ top:100%; opacity:0; }}
}}
/* ── Hazard corner markers ── */
.hazard {{ position:absolute; width:{'60px' if portrait else '80px'}; height:{'60px' if portrait else '80px'};
  border-color:rgba(200,140,60,0.15); }}
.hz-tl {{ top:3%; left:3%; border-top:2px solid; border-left:2px solid; }}
.hz-tr {{ top:3%; right:3%; border-top:2px solid; border-right:2px solid; }}
.hz-bl {{ bottom:{'30%' if portrait else '10%'}; left:3%; border-bottom:2px solid; border-left:2px solid; }}
.hz-br {{ bottom:{'30%' if portrait else '10%'}; right:3%; border-bottom:2px solid; border-right:2px solid; }}
/* ── Quote ── */
.quote-overlay {{ position:absolute; top:0; left:0; width:{w}; height:{h};
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  pointer-events:none; z-index:10;
  animation: fadeIn 30s ease-in-out forwards; }}
@keyframes fadeIn {{
  0% {{ opacity:0; }} 12% {{ opacity:0; }} 18% {{ opacity:1; }}
  70% {{ opacity:1; }} 85% {{ opacity:1; }} 95% {{ opacity:0; }} 100% {{ opacity:0; }}
}}
.quote-text {{ font-family:'Courier New',Consolas,monospace;
  font-size:{'54px' if portrait else '30px'}; font-weight:300;
  color:#c87838; text-align:center; line-height:1.45; letter-spacing:2px;
  text-shadow:0 0 30px rgba(200,120,56,0.10);
  max-width:{'900px' if portrait else '1100px'}; margin-bottom:{'28px' if portrait else '20px'};
  padding:0 {'60px' if portrait else '40px'}; }}
.quote-attribution {{ font-family:'Courier New',Consolas,monospace;
  font-size:{'16px' if portrait else '12px'}; font-weight:400; letter-spacing:{'6px' if portrait else '4px'};
  color:#6a4a2a; text-transform:uppercase; margin-top:{'12px' if portrait else '8px'}; }}
</style></head><body>
<div class="grid"></div>
<div class="strut s1"></div><div class="strut s2"></div><div class="strut s3"></div>
<div class="block blk1"></div><div class="block blk2"></div><div class="block blk3"></div>
<div class="scanline"></div>
<div class="hazard hz-tl"></div><div class="hazard hz-tr"></div><div class="hazard hz-bl"></div><div class="hazard hz-br"></div>
<div class="quote-overlay">
  <div class="quote-text">&ldquo;{text}&rdquo;</div>
  <div class="quote-attribution">&mdash; {author}</div>
</div>
</body></html>"""


# ─── Neon Dusk ──────────────────────────────────────────────────────────────

def neon_dusk_html(quote: StoicQuote, duration: int = 30, portrait: bool = True) -> str:
    """Cyberpunk neon theme — grid, neon triangles, glitch effects, magenta/cyan."""
    text = _esc(quote.text)
    author = _esc(quote.author)

    w = "1080px" if portrait else "1920px"
    h = "1920px" if portrait else "1080px"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{w}; height:{h};
  background:radial-gradient(ellipse 100% 70% at 50% 25%, #1a0020 0%, #0a0014 40%, #04000a 100%);
  overflow:hidden; position:relative; }}
/* ── Perspective grid ── */
.neon-grid {{ position:absolute; top:0; left:0; width:100%; height:{'70%' if portrait else '65%'};
  background-image:
    linear-gradient(90deg, rgba(255,0,200,0.04) 1px, transparent 1px),
    linear-gradient(rgba(0,200,255,0.04) 1px, transparent 1px);
  background-size:{'40px 40px' if portrait else '50px 50px'};
  transform:perspective(500px) rotateX(30deg);
  transform-origin:bottom center;
  animation: grid-pulse 4s ease-in-out infinite; }}
@keyframes grid-pulse {{
  0%,100% {{ opacity:0.6; }}
  50% {{ opacity:1; }}
}}
/* ── Floating geometric shapes ── */
.shape {{ position:absolute; opacity:0.5; }}
.tri1 {{ left:{'30%' if portrait else '25%'}; top:{'12%' if portrait else '10%'};
  width:0; height:0;
  border-left:40px solid transparent; border-right:40px solid transparent;
  border-bottom:70px solid rgba(255,0,200,0.12);
  animation: float-shape 7s ease-in-out infinite; }}
.tri2 {{ left:{'60%' if portrait else '65%'}; top:{'18%' if portrait else '15%'};
  width:0; height:0;
  border-left:30px solid transparent; border-right:30px solid transparent;
  border-bottom:52px solid rgba(0,200,255,0.10);
  animation: float-shape 9s ease-in-out infinite reverse; }}
.hex {{ position:absolute; left:{'42%' if portrait else '45%'}; top:{'22%' if portrait else '18%'};
  width:60px; height:60px; animation: float-shape 8s ease-in-out infinite; }}
.hex-inner {{ width:100%; height:100%; background:rgba(255,0,200,0.06);
  clip-path:polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  animation: shape-rotate 12s linear infinite; }}
@keyframes float-shape {{
  0%,100% {{ transform:translateY(0) rotate(0deg); }}
  50% {{ transform:translateY(-40px) rotate(10deg); }}
}}
@keyframes shape-rotate {{
  0% {{ transform:rotate(0deg); }}
  100% {{ transform:rotate(360deg); }}
}}
/* ── Glitch bar ── */
.glitch {{ position:absolute; left:0; width:100%; height:2px;
  background:linear-gradient(90deg,transparent,rgba(255,0,200,0.2),rgba(0,255,255,0.2),transparent);
  animation: glitch-fall 6s linear infinite; }}
.glitch2 {{ composes:glitch; height:1px;
  background:linear-gradient(90deg,transparent,rgba(0,255,255,0.15),transparent);
  animation: glitch-fall 5s linear infinite 2s; }}
@keyframes glitch-fall {{
  0% {{ top:-10px; opacity:0; }}
  10% {{ opacity:1; }}
  90% {{ opacity:1; }}
  100% {{ top:100%; opacity:0; }}
}}
/* ── Neon ring ── */
.n-ring {{ position:absolute; top:{'22%' if portrait else '17%'}; left:50%; transform:translateX(-50%);
  width:250px; height:250px; border-radius:50%;
  border:1px solid rgba(0,200,255,0.08);
  animation: ring-spin 10s linear infinite; }}
.n-ring2 {{ composes:n-ring; width:350px; height:350px; border-color:rgba(255,0,200,0.05);
  animation: ring-spin 15s linear infinite reverse; }}
@keyframes ring-spin {{
  0% {{ transform:translateX(-50%) rotate(0deg); }}
  100% {{ transform:translateX(-50%) rotate(360deg); }}
}}
/* ── Neon glitch text effect ── */
@keyframes glitch-text {{
  0%,90%,100% {{ opacity:1; transform:translate(0); }}
  92% {{ opacity:0.8; transform:translate(-3px,1px); }}
  94% {{ opacity:0.9; transform:translate(3px,-1px); }}
  96% {{ opacity:0.7; transform:translate(-2px,2px); }}
}}
/* ── Quote ── */
.quote-overlay {{ position:absolute; top:0; left:0; width:{w}; height:{h};
  display:flex; flex-direction:column;
  align-items:center; justify-content:center;
  pointer-events:none; z-index:10;
  animation: fadeIn 30s ease-in-out forwards; }}
@keyframes fadeIn {{
  0% {{ opacity:0; }} 12% {{ opacity:0; }} 18% {{ opacity:1; }}
  70% {{ opacity:1; }} 85% {{ opacity:1; }} 95% {{ opacity:0; }} 100% {{ opacity:0; }}
}}
.quote-text {{ font-family:Futura,'Century Gothic','Avenir Next',sans-serif;
  font-size:{'60px' if portrait else '34px'}; font-weight:200;
  color:#38f8f8; text-align:center; line-height:1.35; letter-spacing:4px;
  text-shadow:0 0 40px rgba(56,248,248,0.2), 0 0 80px rgba(56,248,248,0.1), 0 0 120px rgba(255,0,200,0.05);
  max-width:{'900px' if portrait else '1100px'}; margin-bottom:{'28px' if portrait else '20px'};
  padding:0 {'60px' if portrait else '40px'};
  animation: glitch-text 30s ease-in-out forwards; }}
.quote-attribution {{ font-family:Futura,'Century Gothic','Avenir Next',sans-serif;
  font-size:{'18px' if portrait else '13px'}; font-weight:300; letter-spacing:{'8px' if portrait else '5px'};
  color:#ff00c8; text-transform:uppercase; margin-top:{'12px' if portrait else '8px'};
  text-shadow:0 0 20px rgba(255,0,200,0.15); }}
</style></head><body>
<div class="neon-grid"></div>
<div class="n-ring"></div><div class="n-ring2"></div>
<div class="tri1"></div><div class="tri2"></div>
<div class="hex"><div class="hex-inner"></div></div>
<div class="glitch"></div><div class="glitch2"></div>
<div class="quote-overlay">
  <div class="quote-text">&ldquo;{text}&rdquo;</div>
  <div class="quote-attribution">&mdash; {author}</div>
</div>
</body></html>"""


# ─── Dispatcher ─────────────────────────────────────────────────────────────

THEME_REGISTRY = {
    "solar_flare": solar_flare_html,
    "oceanic_tones": oceanic_tones_html,
    "urban_decay": urban_decay_html,
    "neon_dusk": neon_dusk_html,
}


def render_themed_html(
    quote: StoicQuote,
    theme: str = "default",
    duration: int = 30,
    portrait: bool = True,
) -> str:
    """Generate HTML for a themed short.

    Args:
        quote: The quote to display.
        theme: Theme name (solar_flare, oceanic_tones, urban_decay, neon_dusk, or default).
        duration: Clip duration in seconds.
        portrait: True for 1080x1920 portrait layout.

    Returns:
        Self-contained HTML string.
    """
    fn = THEME_REGISTRY.get(theme)
    if fn:
        return fn(quote, duration=duration, portrait=portrait)
    # Fall back to default template (from templates.py)
    from openmusic.shorts.templates import render_short_html
    return render_short_html(quote, duration=duration, portrait=portrait)
