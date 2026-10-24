"""
artwork.py - flat, static illustrations drawn in SVG (no photos needed).

aerial_plant()  - a top-down view of a wastewater treatment plant used as the
                  background of the page banners (screens, clarifiers,
                  aeration basins, digesters, reuse fields).
icon_*()        - small illustrations for the cards on the Home page.
Everything is plain text, so it loads instantly and stays sharp at any size.
"""
import base64

NAVY_DK, NAVY, NAVY_LT = "#151B4F", "#1E2770", "#2A357F"
LINE, WATER, WATER_LT, AQUA = "#4E5DA8", "#2F6DB5", "#4C93D1", "#7FD3E8"
GREEN, GREEN_LT = "#2E7D5B", "#4FA37C"


def data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _clarifier(cx, cy, r):
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r * k:.1f}" fill="none" stroke="{AQUA}" '
                    f'stroke-opacity="{0.10 + 0.06 * i}" stroke-width="1.2"/>'
                    for i, k in enumerate((0.82, 0.62, 0.42)))
    return (f'<circle cx="{cx}" cy="{cy}" r="{r + 7}" fill="{NAVY_LT}" stroke="{LINE}" stroke-width="2"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{WATER}"/>{rings}'
            f'<line x1="{cx - r}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="#C9D3F5" stroke-width="3" stroke-opacity="0.7"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.12:.1f}" fill="#C9D3F5" fill-opacity="0.8"/>')


def _basin(x, y, w, h, lanes=4):
    lane_h = h / lanes
    out = [f'<rect x="{x - 6}" y="{y - 6}" width="{w + 12}" height="{h + 12}" rx="4" fill="{NAVY_LT}" stroke="{LINE}" stroke-width="2"/>']
    for i in range(lanes):
        ly = y + i * lane_h
        out.append(f'<rect x="{x}" y="{ly + 3}" width="{w}" height="{lane_h - 6}" rx="2" fill="{WATER_LT}" fill-opacity="0.85"/>')
        for j in range(int(w // 26)):           # rows of diffuser bubbles
            bx = x + 14 + j * 26 + (8 if i % 2 else 0)
            out.append(f'<circle cx="{bx:.0f}" cy="{ly + lane_h / 2:.0f}" r="3.2" fill="#E6F6FB" fill-opacity="0.55"/>')
    return "".join(out)


def _digester(cx, cy, r):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r + 6}" fill="{NAVY_LT}" stroke="{LINE}" stroke-width="2"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#8C97C9"/>'
            f'<circle cx="{cx - r * 0.25:.0f}" cy="{cy - r * 0.25:.0f}" r="{r * 0.55:.0f}" fill="#B4BDE3" fill-opacity="0.6"/>')


def aerial_plant(width=1600, height=560) -> str:
    """Top-down treatment plant, flowing left (inlet) to right (reuse fields)."""
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid slice">',
             f'<rect width="{width}" height="{height}" fill="{NAVY}"/>']
    # site grid and roads
    for gx in range(0, width, 80):
        parts.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{height}" stroke="{NAVY_LT}" stroke-width="1"/>')
    for gy in range(0, height, 80):
        parts.append(f'<line x1="0" y1="{gy}" x2="{width}" y2="{gy}" stroke="{NAVY_LT}" stroke-width="1"/>')
    parts.append(f'<rect x="0" y="262" width="{width}" height="26" fill="{NAVY_DK}"/>')
    parts.append(f'<rect x="560" y="0" width="22" height="{height}" fill="{NAVY_DK}"/>')
    # main pipe
    parts.append(f'<path d="M40 200 H1180 M1180 200 V420 H1560" fill="none" stroke="{AQUA}" stroke-opacity="0.45" stroke-width="5" stroke-dasharray="14 9"/>')
    # inlet works: screens and grit channels
    for i in range(3):
        parts.append(f'<rect x="{60 + i * 34}" y="120" width="22" height="120" rx="3" fill="{WATER}" stroke="{LINE}" stroke-width="2"/>')
    # primary clarifiers
    parts += [_clarifier(330, 130, 62), _clarifier(330, 400, 62), _clarifier(470, 400, 50)]
    # aeration basins (biological stage)
    parts += [_basin(630, 80, 360, 150, 4), _basin(630, 320, 360, 150, 4)]
    # secondary clarifiers
    parts += [_clarifier(1090, 120, 58), _clarifier(1090, 400, 58)]
    # anaerobic digesters (biogas)
    parts += [_digester(1250, 90, 40), _digester(1340, 90, 40)]
    parts.append(f'<rect x="1225" y="150" width="140" height="40" rx="4" fill="#8C97C9" fill-opacity="0.7"/>')
    # reuse fields (irrigation)
    for i in range(4):
        for j in range(3):
            parts.append(f'<rect x="{1250 + i * 85}" y="{300 + j * 80}" width="72" height="66" rx="3" '
                         f'fill="{GREEN if (i + j) % 2 else GREEN_LT}" fill-opacity="0.55"/>')
    # trees
    for tx, ty in [(200, 470), (230, 500), (520, 60), (1010, 520), (1480, 60), (1530, 120), (150, 40)]:
        parts.append(f'<circle cx="{tx}" cy="{ty}" r="16" fill="{GREEN}" fill-opacity="0.6"/>')
    parts.append("</svg>")
    return "".join(parts)


def _card_svg(body: str, bg: str = "#EAF1FB") -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid slice">'
            f'<rect width="400" height="200" fill="{bg}"/>{body}</svg>')


def icon_predict() -> str:
    """Line chart with a forecast band, next to a sample bottle."""
    pts = [(40, 150), (80, 128), (120, 138), (160, 110), (200, 118), (240, 92)]
    path = "M" + " L".join(f"{x} {y}" for x, y in pts)
    band = "M240 92 L340 60 L340 110 L240 92 Z"
    grid = "".join(f'<line x1="30" y1="{y}" x2="350" y2="{y}" stroke="#C9D6EA" stroke-width="1"/>' for y in (60, 100, 140, 170))
    return data_uri(_card_svg(
        grid + f'<path d="{band}" fill="#2457C5" fill-opacity="0.15"/>'
        f'<path d="{path}" fill="none" stroke="{NAVY}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M240 92 L340 84" fill="none" stroke="#2457C5" stroke-width="4" stroke-dasharray="8 6"/>'
        f'<line x1="30" y1="76" x2="350" y2="76" stroke="#D7263D" stroke-width="2" stroke-dasharray="6 5"/>'
        '<rect x="300" y="118" width="44" height="58" rx="8" fill="#FFFFFF" stroke="#1E2770" stroke-width="3"/>'
        '<rect x="312" y="106" width="20" height="14" rx="2" fill="#1E2770"/>'
        '<rect x="303" y="146" width="38" height="27" rx="5" fill="#4C93D1" fill-opacity="0.7"/>'))


def icon_reuse() -> str:
    """Treated water irrigating crop rows."""
    rows = "".join(f'<path d="M{20 + i * 70} 200 L{150 + i * 30} 120" stroke="#2E7D5B" stroke-width="16" stroke-linecap="round" '
                   f'stroke-opacity="{0.45 + 0.1 * (i % 2)}"/>' for i in range(6))
    drops = "".join(f'<path d="M{x} {y} q7 12 0 18 q-7 -6 0 -18z" fill="#2F6DB5"/>'
                    for x, y in [(190, 48), (226, 66), (258, 44), (292, 70), (322, 52)])
    return data_uri(_card_svg(
        '<rect y="120" width="400" height="80" fill="#CFE6D8"/>' + rows +
        '<path d="M90 70 Q220 -10 350 70" fill="none" stroke="#4C93D1" stroke-width="5" stroke-dasharray="3 10" stroke-linecap="round"/>'
        '<rect x="70" y="66" width="34" height="56" rx="4" fill="#1E2770"/>' + drops, bg="#EAF4EE"))


def icon_recover() -> str:
    """Biogas digester with gas holder, a flame and a fertiliser sack."""
    return data_uri(_card_svg(
        '<rect y="160" width="400" height="40" fill="#DDE3F2"/>'
        '<path d="M70 160 V110 Q140 40 210 110 V160 Z" fill="#1E2770"/>'
        '<path d="M88 160 V116 Q140 64 192 116 V160 Z" fill="#2A357F"/>'
        '<rect x="210" y="132" width="60" height="8" fill="#1E2770"/>'
        '<path d="M290 136 q-16 -22 4 -46 q2 18 14 22 q4 -12 -2 -24 q24 16 12 48 q-10 14 -28 0z" fill="#ED8B1E"/>'
        '<path d="M300 132 q-6 -10 2 -20 q8 10 4 20z" fill="#FFD27A"/>'
        '<rect x="320" y="104" width="50" height="56" rx="8" fill="#B8873E"/>'
        '<path d="M333 132 q12 -20 24 0 q-12 14 -24 0z" fill="#2E7D5B"/>', bg="#EEF0F8"))
