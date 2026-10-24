"""
hero.py - the interactive "water" hero for the Overview page.

The campus photo is drawn on a canvas and a small water simulation runs on
top of it: moving the cursor (or a finger on a phone) drags ripples through
the image, and gentle drops fall on their own. Everything is plain
JavaScript, so no extra library or internet download is needed.
"""
import base64
from pathlib import Path


def hero_html(image_path: Path, kicker: str, title: str, lead: str, hint: str,
              navy: str = "#29337F", red: str = "#ED1E24") -> str:
    img64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    return f"""
<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  html, body {{ margin: 0; padding: 0; background: #ffffff; font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif; }}
  .hero {{ position: relative; height: 560px; overflow: hidden; border-radius: 22px 22px 0 0; cursor: crosshair;
          background: {navy}; }}
  canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; display: block; }}
  .shade {{ position: absolute; inset: 0; pointer-events: none;
           background: linear-gradient(100deg, rgba(20,26,70,0.92) 0%, rgba(41,51,127,0.78) 38%,
                                       rgba(41,51,127,0.25) 68%, rgba(41,51,127,0.05) 100%); }}
  .copy {{ position: absolute; left: 6%; top: 50%; transform: translateY(-56%); max-width: 600px;
          color: #ffffff; pointer-events: none; }}
  .kicker {{ display: flex; align-items: center; gap: 10px; font-size: 15px; color: rgba(255,255,255,0.85); }}
  .kicker:before {{ content: ""; width: 34px; height: 3px; background: {red}; border-radius: 2px; }}
  h1 {{ font-size: 52px; line-height: 1.06; margin: 18px 0 18px 0; font-weight: 700; letter-spacing: -0.015em; }}
  h1 span {{ display: block; font-weight: 400; color: rgba(255,255,255,0.88); }}
  p {{ font-size: 18px; line-height: 1.6; color: rgba(255,255,255,0.86); margin: 0; max-width: 52ch; }}
  .hint {{ position: absolute; right: 26px; bottom: 74px; color: rgba(255,255,255,0.8); font-size: 13px;
          pointer-events: none; }}
  .wave {{ position: absolute; left: 0; bottom: -2px; width: 200%; height: 70px; pointer-events: none;
          animation: drift 16s linear infinite; }}
  .wave.back {{ opacity: 0.45; animation-duration: 24s; animation-direction: reverse; bottom: 4px; }}
  @keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-50%); }} }}
  @media (max-width: 760px) {{
    .hero {{ height: 520px; }} h1 {{ font-size: 36px; }} p {{ font-size: 16px; }}
    .copy {{ left: 7%; right: 7%; }} .hint {{ display: none; }}
  }}
  @media (prefers-reduced-motion: reduce) {{ .wave {{ animation: none; }} }}
</style></head>
<body>
<div class="hero" id="hero">
  <canvas id="water" aria-label="Campus photo with an interactive water effect"></canvas>
  <div class="shade"></div>
  <div class="copy">
    <div class="kicker">{kicker}</div>
    <h1>{title}</h1>
    <p>{lead}</p>
  </div>
  <div class="hint">{hint}</div>
  <svg class="wave back" viewBox="0 0 2880 70" preserveAspectRatio="none"><path fill="#ffffff"
    d="M0 38 C240 8 480 8 720 38 C960 68 1200 68 1440 38 C1680 8 1920 8 2160 38 C2400 68 2640 68 2880 38 L2880 70 L0 70 Z"/></svg>
  <svg class="wave" viewBox="0 0 2880 70" preserveAspectRatio="none"><path fill="#ffffff"
    d="M0 44 C360 14 720 14 1080 44 C1260 59 1350 59 1440 44 C1800 14 2160 14 2520 44 C2700 59 2790 59 2880 44 L2880 70 L0 70 Z"/></svg>
</div>
<script>
(function () {{
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hero = document.getElementById('hero');
  const canvas = document.getElementById('water');
  const ctx = canvas.getContext('2d');
  const img = new Image();
  let W, H, src, out, buf1, buf2, scale;

  function setup() {{
    const r = hero.getBoundingClientRect();
    scale = r.width > 900 ? 2 : 1.5;                   // simulate at reduced resolution for speed
    W = Math.max(120, Math.round(r.width / scale));
    H = Math.max(120, Math.round(r.height / scale));
    canvas.width = W; canvas.height = H;
    const off = document.createElement('canvas'); off.width = W; off.height = H;
    const o = off.getContext('2d');
    const s = Math.max(W / img.width, H / img.height); // "cover" the hero area
    const dw = img.width * s, dh = img.height * s;
    o.drawImage(img, (W - dw) / 2, (H - dh) / 2, dw, dh);
    src = o.getImageData(0, 0, W, H).data;
    out = ctx.createImageData(W, H);
    buf1 = new Int16Array(W * H); buf2 = new Int16Array(W * H);
    ctx.putImageData(new ImageData(new Uint8ClampedArray(src), W, H), 0, 0);
  }}

  function drop(x, y, radius, strength) {{
    for (let j = -radius; j <= radius; j++) {{
      for (let i = -radius; i <= radius; i++) {{
        const xx = x + i, yy = y + j;
        if (xx < 1 || yy < 1 || xx >= W - 1 || yy >= H - 1) continue;
        if (i * i + j * j <= radius * radius) buf1[yy * W + xx] += strength;
      }}
    }}
  }}

  function step() {{
    for (let y = 1; y < H - 1; y++) {{
      for (let x = 1, i = y * W + 1; x < W - 1; x++, i++) {{
        let v = ((buf1[i - 1] + buf1[i + 1] + buf1[i - W] + buf1[i + W]) >> 1) - buf2[i];
        v -= v >> 5;                                   // damping: ripples fade out
        buf2[i] = v;
      }}
    }}
    const t = buf1; buf1 = buf2; buf2 = t;
    const d = out.data;
    for (let y = 1; y < H - 1; y++) {{
      for (let x = 1, i = y * W + 1; x < W - 1; x++, i++) {{
        const dx = buf1[i - 1] - buf1[i + 1], dy = buf1[i - W] - buf1[i + W];
        let sx = x + (dx >> 4), sy = y + (dy >> 4);   // refraction: bend the photo
        if (sx < 0) sx = 0; else if (sx >= W) sx = W - 1;
        if (sy < 0) sy = 0; else if (sy >= H) sy = H - 1;
        const s = (sy * W + sx) * 4, p = i * 4, light = dx >> 2;  // light catches the wave crests
        d[p] = src[s] + light; d[p + 1] = src[s + 1] + light; d[p + 2] = src[s + 2] + light; d[p + 3] = 255;
      }}
    }}
    ctx.putImageData(out, 0, 0);
  }}

  let last = 0;
  function loop(ts) {{
    if (!reduce && ts - last > 1300) {{                 // an occasional gentle drop
      drop(Math.floor(W * (0.45 + Math.random() * 0.5)), Math.floor(H * (0.15 + Math.random() * 0.6)), 3, 380);
      last = ts;
    }}
    step();
    requestAnimationFrame(loop);
  }}

  function pointer(e) {{
    const r = canvas.getBoundingClientRect();
    const p = e.touches ? e.touches[0] : e;
    drop(Math.floor((p.clientX - r.left) / scale), Math.floor((p.clientY - r.top) / scale), 3, 260);
  }}

  img.onload = function () {{
    setup();
    if (reduce) return;                                // still photo only
    hero.addEventListener('mousemove', pointer);
    hero.addEventListener('touchmove', pointer, {{ passive: true }});
    hero.addEventListener('click', function (e) {{
      const r = canvas.getBoundingClientRect();
      drop(Math.floor((e.clientX - r.left) / scale), Math.floor((e.clientY - r.top) / scale), 6, 900);
    }});
    let timer; window.addEventListener('resize', function () {{ clearTimeout(timer); timer = setTimeout(setup, 200); }});
    requestAnimationFrame(loop);
  }};
  img.src = "data:image/jpeg;base64,{img64}";
}})();
</script>
</body></html>
"""
