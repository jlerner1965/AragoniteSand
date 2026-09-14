#!/usr/bin/env python3
"""Render studio pack shots of the bagged line.

    python3 tools/make-packshots.py      # writes the SVG sources
    node tools/render-packshots.mjs      # rasterises them to assets/photos/

These are renders, not photographs. The pack they show has not been produced.

The artwork follows AragoCor's own packaging language, from photographs of the
real 50 lb bag and 2 tonne sack: a white woven sack with blue side gussets, the
product name set large over a rule, a row of round icons, an ocean wave filling
the foot, the net weight in a dark badge and a code block in the corner. It is
not a copy of that artwork. The type is this site's, the wave is drawn here,
the icons carry specification rather than benefit claims, and the code block
points at this site's lot lookup.

Lighting is a single soft key from the upper left with a weaker fill from the
right, which is how a pack shot is usually lit and what the shot brief in
data/images.json asks for. The cylindrical falloff, the specular band, the
occlusion along the silhouette and the contact shadow all follow from it.

Generated from data/grades.json and data/products.json, so the print cannot
disagree with the catalogue. Standard library only; deterministic.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "photos" / "src"

W, H = 1600, 1200

# The site's palette, extended down into the water for the wave.
NAVY = "#0B2C3A"
ABYSS = "#061C26"
TEAL = "#17707E"
AQUA = "#3E9FB0"
AQUA_LT = "#6FC3CE"
PALE = "#AFDCE2"
SAND = "#D9BE86"
SAND_DEEP = "#B8975A"
TIDE = "#4E6B74"
GUSSET_BLUE = "#2F6E86"

SANS = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

SEEDS = {"fine": 101, "medium": 202, "coarse": 303}

WEAVE = (
    '<pattern id="weave" width="9" height="9" patternUnits="userSpaceOnUse">'
    '<path d="M0 4.5 H9" stroke="#8C8577" stroke-opacity="0.10" stroke-width="2.6"/>'
    '<path d="M0 2.2 H9" stroke="#FFFFFF" stroke-opacity="0.16" stroke-width="1.4"/>'
    '<path d="M4.5 0 V9" stroke="#6F6A5E" stroke-opacity="0.05" stroke-width="2.4"/>'
    '</pattern>'
)
PALLET = (
    '<linearGradient id="pallet" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#D9B87A"/><stop offset="0.5" stop-color="#C4A265"/>'
    '<stop offset="1" stop-color="#A5854D"/></linearGradient>'
)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def text(x, y, s, size=14, fill=NAVY, family=SANS, weight="400",
         anchor="start", spacing=None, opacity=None):
    a = (f'x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size:.1f}" '
         f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"')
    if spacing is not None:
        a += f' letter-spacing="{spacing}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return f'<text {a}>{esc(s)}</text>'


def zoom(k, cx, cy):
    """Scale the subject about a point, to size it to the frame."""
    return f'<g transform="translate({cx * (1 - k):.1f} {cy * (1 - k):.1f}) scale({k})">'


def studio_defs(extra=""):
    return f'''
<defs>
  <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFFFFF"/>
    <stop offset="0.52" stop-color="#FBFAF8"/>
    <stop offset="0.70" stop-color="#EFEDE8"/>
    <stop offset="1" stop-color="#E4E1DA"/>
  </linearGradient>
  <radialGradient id="vignette" cx="0.44" cy="0.40" r="0.78">
    <stop offset="0.45" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="1" stop-color="#9A958C" stop-opacity="0.28"/>
  </radialGradient>
  <!-- Key upper left: the face brightens off-centre left and falls to both edges. -->
  <linearGradient id="face" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#BDB7AB"/>
    <stop offset="0.07" stop-color="#E2DDD3"/>
    <stop offset="0.22" stop-color="#FAF8F3"/>
    <stop offset="0.36" stop-color="#FFFFFF"/>
    <stop offset="0.58" stop-color="#F6F3EC"/>
    <stop offset="0.82" stop-color="#E0DAD0"/>
    <stop offset="1" stop-color="#B4AEA2"/>
  </linearGradient>
  <linearGradient id="faceV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#8E877A" stop-opacity="0.20"/>
    <stop offset="0.14" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="0.84" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="1" stop-color="#7E776B" stop-opacity="0.26"/>
  </linearGradient>
  <linearGradient id="gusset" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#1D4E61"/>
    <stop offset="0.42" stop-color="#37788F"/>
    <stop offset="1" stop-color="#173D4C"/>
  </linearGradient>
  <radialGradient id="ooid" cx="0.38" cy="0.34" r="0.86">
    <stop offset="0" stop-color="#F6EDDA"/>
    <stop offset="0.38" stop-color="#EADCBD"/>
    <stop offset="0.72" stop-color="#D8C49A"/>
    <stop offset="0.92" stop-color="#C0A877"/>
    <stop offset="1" stop-color="#AD9566"/>
  </radialGradient>
  <filter id="filmgrain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="4" result="n"/>
    <feColorMatrix in="n" type="saturate" values="0"/>
  </filter>
  <filter id="soft40"><feGaussianBlur stdDeviation="40"/></filter>
  <filter id="soft22"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="soft12"><feGaussianBlur stdDeviation="12"/></filter>
  <filter id="soft6"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="soft3"><feGaussianBlur stdDeviation="3"/></filter>
  {WEAVE}{PALLET}{extra}
</defs>'''


def set_dressing():
    return (f'<rect width="{W}" height="{H}" fill="url(#sweep)"/>'
            f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>')


# ------------------------------------------------------------------ artwork

def wave(x, y, w, h):
    """The ocean band across the foot of the pack.

    Four crests, palest at the back, stepping down to the navy the type sits
    on. Drawn here rather than traced: same idea as the real pack, different
    curve and a palette taken from this site's tokens.
    """
    def crest(depth, amp, phase):
        """One band: a crest across the width, filled to the bottom."""
        top = y + h * depth
        pts = [f'M{x} {top + amp * math.sin(phase):.1f}']
        n = 6
        for i in range(n):
            x0 = x + w * i / n
            x1 = x + w * (i + 1) / n
            y0 = top + amp * math.sin(phase + i * 1.15)
            y1 = top + amp * math.sin(phase + (i + 1) * 1.15)
            cx0 = x0 + (x1 - x0) * 0.42
            cx1 = x0 + (x1 - x0) * 0.58
            pts.append(f'C{cx0:.1f} {y0 - amp * 0.75:.1f} {cx1:.1f} {y1 + amp * 0.75:.1f} '
                       f'{x1:.1f} {y1:.1f}')
        pts.append(f'L{x + w} {y + h} L{x} {y + h} Z')
        return " ".join(pts)

    o = [f'<path d="{crest(0.00, h * 0.055, 0.6)}" fill="{PALE}"/>',
         f'<path d="{crest(0.16, h * 0.060, 2.1)}" fill="{AQUA_LT}"/>',
         f'<path d="{crest(0.34, h * 0.055, 3.6)}" fill="{AQUA}"/>',
         f'<path d="{crest(0.52, h * 0.050, 5.0)}" fill="{TEAL}"/>',
         f'<path d="{crest(0.70, h * 0.040, 0.3)}" fill="{NAVY}"/>']
    # Foam: a few light strokes riding the second crest.
    for i, (fx, fy, fw) in enumerate(((0.12, 0.23, 0.10), (0.44, 0.20, 0.14),
                                      (0.74, 0.26, 0.09))):
        o.append(f'<path d="M{x + w * fx:.0f} {y + h * fy:.0f} q{w * fw / 2:.0f} '
                 f'{-h * 0.035:.0f} {w * fw:.0f} 0" stroke="#FFFFFF" stroke-opacity="0.45" '
                 f'stroke-width="{h * 0.012:.1f}" fill="none" stroke-linecap="round"/>')
    return "".join(o)


def omri_badge(cx, cy, r):
    """The organic-input badge, carrying the same hedge the real pack carries:
    products available OMRI listed, not this product is OMRI listed."""
    return (
        f'<g>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="{NAVY}" '
        f'stroke-width="{r * 0.055:.1f}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.86:.1f}" fill="none" stroke="{TEAL}" '
        f'stroke-width="{r * 0.03:.1f}"/>'
        f'{text(cx, cy - r * 0.44, "Products available", r * 0.145, TIDE, SANS, "600", "middle")}'
        f'{text(cx, cy + r * 0.12, "OMRI", r * 0.46, NAVY, SANS, "700", "middle", spacing="0.02em")}'
        f'{text(cx, cy + r * 0.48, "L I S T E D", r * 0.19, NAVY, SANS, "600", "middle")}'
        f'<path d="M{cx - r * 0.5} {cy + r * 0.62} H{cx + r * 0.5}" stroke="{SAND_DEEP}" '
        f'stroke-width="{r * 0.05:.1f}"/>'
        f'</g>'
    )


def spec_icon(cx, cy, r, kind):
    """A round spec mark. Specification, not a benefit claim: what the material
    is and what has been done to it, which is what a trade buyer reads for."""
    s = r * 0.52
    g = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{NAVY}"/>']
    if kind == "ooid":                       # three grains on a line
        g.append(f'<g fill="#FFFFFF"><circle cx="{cx - s * 0.62}" cy="{cy + s * 0.12}" '
                 f'r="{s * 0.2:.1f}"/><circle cx="{cx - s * 0.06}" cy="{cy}" r="{s * 0.3:.1f}"/>'
                 f'<circle cx="{cx + s * 0.62}" cy="{cy - s * 0.12}" r="{s * 0.42:.1f}"/></g>')
        g.append(f'<path d="M{cx - s} {cy + s * 0.66} H{cx + s}" stroke="{AQUA_LT}" '
                 f'stroke-width="{s * 0.16:.1f}" stroke-linecap="round"/>')
    elif kind == "screen":                   # a sieve mesh
        g.append(f'<g stroke="#FFFFFF" stroke-width="{s * 0.13:.1f}" fill="none">')
        for i in range(-1, 2):
            g.append(f'<path d="M{cx - s} {cy + i * s * 0.55} H{cx + s}"/>')
            g.append(f'<path d="M{cx + i * s * 0.55} {cy - s} V{cy + s}"/>')
        g.append('</g>')
    elif kind == "nokiln":                   # a flame, struck through
        g.append(f'<path d="M{cx} {cy - s} c{s * 0.55} {s * 0.5} {s * 0.42} {s * 0.9} 0 {s * 1.5} '
                 f'c{-s * 0.42} {-s * 0.6} {-s * 0.55} {-s} 0 {-s * 1.5} z" fill="#FFFFFF"/>')
        g.append(f'<path d="M{cx - s * 0.95} {cy + s * 0.95} L{cx + s * 0.95} {cy - s * 0.95}" '
                 f'stroke="{AQUA_LT}" stroke-width="{s * 0.2:.1f}" stroke-linecap="round"/>')
    elif kind == "lot":                      # a tag
        g.append(f'<path d="M{cx - s * 0.85} {cy - s * 0.6} H{cx + s * 0.2} L{cx + s * 0.9} {cy} '
                 f'L{cx + s * 0.2} {cy + s * 0.6} H{cx - s * 0.85} Z" fill="#FFFFFF"/>')
        g.append(f'<circle cx="{cx + s * 0.28}" cy="{cy}" r="{s * 0.16:.1f}" fill="{NAVY}"/>')
    return "".join(g)


def qr_block(x, y, size, seed):
    """A code block in the corner, the way the real pack carries one.

    The pattern is a placeholder: finder squares and a plausible field, not an
    encoded URL. It is a render of a pack that has not been printed, so there is
    nothing yet for it to encode.
    """
    rnd = random.Random(seed)
    n = 21
    c = size / n
    o = [f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="#FFFFFF"/>']
    def finder(fx, fy):
        return (f'<rect x="{x + fx * c}" y="{y + fy * c}" width="{c * 7}" height="{c * 7}" fill="{NAVY}"/>'
                f'<rect x="{x + (fx + 1) * c}" y="{y + (fy + 1) * c}" width="{c * 5}" '
                f'height="{c * 5}" fill="#FFFFFF"/>'
                f'<rect x="{x + (fx + 2) * c}" y="{y + (fy + 2) * c}" width="{c * 3}" '
                f'height="{c * 3}" fill="{NAVY}"/>')
    cells = []
    for gy in range(n):
        for gx in range(n):
            in_finder = ((gx < 8 and gy < 8) or (gx > n - 9 and gy < 8)
                         or (gx < 8 and gy > n - 9))
            if in_finder or rnd.random() > 0.48:
                continue
            cells.append(f'<rect x="{x + gx * c:.2f}" y="{y + gy * c:.2f}" '
                         f'width="{c:.2f}" height="{c:.2f}"/>')
    o.append(f'<g fill="{NAVY}">' + "".join(cells) + '</g>')
    o.append(finder(0, 0) + finder(n - 7, 0) + finder(0, n - 7))
    return "".join(o)


def grain_bed(x, y, w, h, lo_mm, hi_mm, px_per_mm, seed, target):
    """Ooids under the same key light as the pack."""
    rnd = random.Random(seed)
    placed, tries = [], 0
    while tries < 40000 and len(placed) < target:
        tries += 1
        d = (rnd.uniform(lo_mm, hi_mm) + rnd.uniform(lo_mm, hi_mm)) / 2 * px_per_mm
        r = d / 2
        cx = rnd.uniform(x + r * 0.4, x + w - r * 0.4)
        cy = rnd.uniform(y + r * 0.4, y + h - r * 0.4)
        if any((cx - a) ** 2 + (cy - b) ** 2 < (r + c + 0.4) ** 2 for a, b, c in placed):
            continue
        placed.append((cx, cy, r))
    out = []
    rnd2 = random.Random(seed + 1)
    for cx, cy, r in sorted(placed, key=lambda g: -g[2]):
        out.append(f'<ellipse cx="{cx + r * 0.2:.1f}" cy="{cy + r * 0.24:.1f}" '
                   f'rx="{r * 1.02:.2f}" ry="{r * 0.9:.2f}" fill="#8E7448" opacity="0.32"/>')
        sq = 1 + rnd2.uniform(-0.09, 0.09)
        rot = rnd2.uniform(0, 180)
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.2f}" ry="{r * sq:.2f}" '
                   f'transform="rotate({rot:.0f} {cx:.1f} {cy:.1f})" fill="url(#ooid)"/>')
    return "".join(out)


def heap(cx, base, w, h, grade, seed):
    """A small cone of the grade poured beside the pack, so the frame carries
    the product as well as the bag it ships in."""
    o = [f'<g filter="url(#soft12)" opacity="0.32">'
         f'<ellipse cx="{cx + 14}" cy="{base + 6}" rx="{w * 0.56:.0f}" ry="{h * 0.16:.0f}" '
         f'fill="#6F6A61"/></g>']
    o.append(f'<clipPath id="hp{seed}"><path d="M{cx - w / 2} {base} '
             f'Q{cx - w * 0.22:.0f} {base - h * 0.86:.0f} {cx:.0f} {base - h:.0f} '
             f'Q{cx + w * 0.24:.0f} {base - h * 0.84:.0f} {cx + w / 2:.0f} {base} '
             f'A{w / 2:.0f} {h * 0.17:.0f} 0 0 1 {cx - w / 2} {base} Z"/></clipPath>')
    o.append(f'<g clip-path="url(#hp{seed})">')
    o.append(f'<rect x="{cx - w / 2 - 10}" y="{base - h - 10}" width="{w + 20}" '
             f'height="{h + 30}" fill="#E3D2AE"/>')
    o.append(f'<g opacity="0.75">')
    o.append(grain_bed(cx - w / 2 - 10, base - h - 10, w + 20, h + 30,
                       grade["grain_min_mm"], grade["grain_max_mm"], 3.8, seed,
                       {"fine": 4200, "medium": 2400, "coarse": 1000}[grade["slug"]]))
    o.append("</g>")
    o.append(f'<g filter="url(#soft22)" opacity="0.3">'
             f'<path d="M{cx + w * 0.04:.0f} {base - h} L{cx + w / 2 + 30:.0f} {base + 30} '
             f'L{cx + w * 0.04:.0f} {base + 30} Z" fill="#8E7448"/></g>')
    o.append(f'<g filter="url(#soft22)" opacity="0.3">'
             f'<ellipse cx="{cx - w * 0.16:.0f}" cy="{base - h * 0.45:.0f}" '
             f'rx="{w * 0.15:.0f}" ry="{h * 0.3:.0f}" fill="#FFFFFF"/></g>')
    o.append("</g>")
    return "".join(o)


# ------------------------------------------------------------- the printed face

def pack_face(x, y, w, h, *, headline, grade=None, net_big, net_small, lot,
              marks, domain="ARAGONITESAND.COM", qr_seed=1, band=0.0):
    """The artwork, laid out against the face it is printed on.

    Everything is a fraction of the face, so the same design serves the 20 lb
    bag, the 50 lb bag and the bulk sack from one layout. `band` is the printed
    side band each edge carries: the water runs under it, but nothing set in
    type may cross it, so the type works to an inset width.
    """
    o = []
    xi, wi = x + band, w - 2 * band          # the printable width
    cx = x + w / 2
    pad = wi * 0.06

    # Organic-input badge, top left. The wording is the hedge the real pack
    # carries: products available OMRI listed, not this product is listed.
    o.append(omri_badge(xi + pad + wi * 0.085, y + h * 0.055 + wi * 0.085, wi * 0.085))

    # Brand line. The mark is drawn in a 45-unit box; the scale is the share of
    # the face width it should occupy, divided by that box.
    ms = (wi * 0.15) / 45
    o.append(f'<g transform="translate({cx - wi * 0.052:.1f} {y + h * 0.108:.1f}) '
             f'scale({ms:.3f})" fill="{NAVY}">'
             f'<circle cx="0" cy="0" r="3.4"/><circle cx="12" cy="-2" r="5.6"/>'
             f'<circle cx="29.5" cy="-5" r="8.6"/>'
             f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{SAND_DEEP}"/></g>')
    o.append(text(cx, y + h * 0.163, "Aragonite sand", wi * 0.068, NAVY, SANS, "700", "middle"))
    o.append(text(cx, y + h * 0.189, "by AragoCor Minerals", wi * 0.029, TIDE, MONO, "400",
                  "middle", spacing="0.06em"))

    # The product name over the rule, as the pack does it. Sized to the
    # printable width so it can never run under a band.
    o.append(text(cx, y + h * 0.268, headline, min(wi * 0.128, wi / (0.70 * len(headline))),
                  NAVY, SANS, "700", "middle", spacing="0.005em"))
    o.append(f'<path d="M{xi + pad} {y + h * 0.292} H{xi + wi - pad}" '
             f'stroke="{NAVY}" stroke-opacity="0.22" stroke-width="{wi * 0.005:.1f}"/>')
    o.append(text(cx, y + h * 0.318, "Calcium carbonate (CaCO\u2083)", wi * 0.044, TIDE,
                  SANS, "500", "middle", spacing="0.03em"))

    # Grade block, where the pack carries one.
    top_icons = 0.40
    if grade:
        by_ = y + h * 0.345
        gwid = wi * 0.90
        o.append(f'<rect x="{cx - gwid / 2:.0f}" y="{by_:.0f}" width="{gwid:.0f}" '
                 f'height="{h * 0.074:.0f}" rx="{h * 0.012:.0f}" fill="{NAVY}"/>')
        o.append(text(cx - gwid / 2 + wi * 0.045, by_ + h * 0.053, grade["name"],
                      wi * 0.050, "#FFFFFF", SANS, "700"))
        o.append(text(cx + gwid / 2 - wi * 0.045, by_ + h * 0.051,
                      f'{grade["grain_mm"]} \u00b7 {grade["mesh"]} mesh',
                      wi * 0.027, PALE, MONO, "500", "end"))
        top_icons = 0.455

    # Icon row.
    ir = wi * 0.063
    iy = y + h * top_icons + ir
    step = (wi - 2 * pad - wi * 0.23) / 3
    for i, (kind, l1, l2) in enumerate(marks):
        ix = xi + pad + wi * 0.115 + i * step
        o.append(spec_icon(ix, iy, ir, kind))
        o.append(text(ix, iy + ir + h * 0.026, l1, wi * 0.026, NAVY, SANS, "600", "middle"))
        if l2:
            o.append(text(ix, iy + ir + h * 0.047, l2, wi * 0.026, NAVY, SANS, "600", "middle"))
        if i < len(marks) - 1:
            o.append(f'<path d="M{ix + step / 2:.0f} {iy - ir * 0.7:.0f} '
                     f'V{iy + ir * 0.7:.0f}" stroke="{NAVY}" stroke-opacity="0.16" '
                     f'stroke-width="1.6"/>')

    # The water, filling the foot. It runs the full face, under the bands.
    wy = y + h * 0.60
    o.append(f'<g>{wave(x, wy, w, h - (wy - y))}</g>')

    # Net weight badge, sitting in the water.
    bw, bh = wi * 0.52, h * 0.115
    bx_, by_ = cx - bw / 2, y + h * 0.745
    o.append(f'<rect x="{bx_:.0f}" y="{by_:.0f}" width="{bw:.0f}" height="{bh:.0f}" '
             f'rx="{bh * 0.22:.0f}" fill="{ABYSS}" fill-opacity="0.88" stroke="#FFFFFF" '
             f'stroke-opacity="0.35" stroke-width="{wi * 0.004:.1f}"/>')
    o.append(text(cx, by_ + bh * 0.58, net_big, min(wi * 0.115, bw / (0.62 * len(net_big))),
                  "#FFFFFF", SANS, "700", "middle"))
    o.append(text(cx, by_ + bh * 0.87, net_small, wi * 0.031, PALE, MONO, "400", "middle"))

    # Code block and the domain line.
    qs = wi * 0.145
    qy = y + h * 0.788
    o.append(qr_block(xi + pad, qy, qs, qr_seed))
    o.append(text(xi + pad, qy + qs + h * 0.028, "Scan for lot analysis",
                  wi * 0.025, "#FFFFFF", SANS, "600"))
    o.append(text(xi + pad, qy + qs + h * 0.050, f'Lot {lot}', wi * 0.025, PALE, MONO, "500"))
    o.append(text(cx, y + h * 0.955, domain, wi * 0.033, "#FFFFFF", SANS, "600",
                  "middle", spacing="0.09em"))
    return "".join(o)


# --------------------------------------------------------------- sewn sack

def sack(face_w, face_h, cx, cy, artwork, seed=1):
    """A filled open-mouth woven sack: white face, blue side gussets, sewn top."""
    x0, x1 = cx - face_w / 2, cx + face_w / 2
    top, bot = cy - face_h / 2, cy + face_h / 2
    gw = face_w * 0.115                      # the blue gusset turned to each side

    o = []
    o.append(f'<g filter="url(#soft22)">'
             f'<ellipse cx="{cx + 34}" cy="{bot + 16}" rx="{face_w * 0.66:.0f}" ry="30" '
             f'fill="#6F6A61" opacity="0.5"/></g>')
    o.append(f'<g filter="url(#soft40)">'
             f'<ellipse cx="{cx + 90}" cy="{bot + 30}" rx="{face_w * 0.9:.0f}" ry="44" '
             f'fill="#7C776D" opacity="0.24"/></g>')

    face = (f'M{x0 + face_w * 0.04} {top} H{x1 - face_w * 0.04} '
            f'C{x1 + face_w * 0.03} {top + face_h * 0.16} {x1 + face_w * 0.03} '
            f'{bot - face_h * 0.16} {x1 - face_w * 0.04} {bot} '
            f'H{x0 + face_w * 0.04} '
            f'C{x0 - face_w * 0.03} {bot - face_h * 0.16} {x0 - face_w * 0.03} '
            f'{top + face_h * 0.16} {x0 + face_w * 0.04} {top} Z')

    o.append(f'<clipPath id="sk{seed}"><path d="{face}"/></clipPath>')
    o.append(f'<path d="{face}" fill="url(#face)"/>')
    o.append(f'<g clip-path="url(#sk{seed})">')
    o.append(f'<rect x="{x0 - 60}" y="{top - 20}" width="{face_w + 120}" '
             f'height="{face_h + 50}" fill="url(#weave)" opacity="0.6"/>')
    # Printed side bands, with the stitch line running through them.
    for sgn in (-1, 1):
        bxx = (x1 - gw) if sgn > 0 else x0
        o.append(f'<rect x="{bxx:.0f}" y="{top - 20}" width="{gw:.0f}" '
                 f'height="{face_h + 50}" fill="url(#gusset)"/>')
        o.append(f'<path d="M{bxx + gw / 2:.0f} {top + face_h * 0.04:.0f} '
                 f'V{bot - face_h * 0.03:.0f}" stroke="#FFFFFF" stroke-opacity="0.45" '
                 f'stroke-width="3" stroke-dasharray="11 9"/>')
    o.append(artwork)
    # The light rides over the print as well as the film.
    o.append(f'<path d="{face}" fill="url(#face)" style="mix-blend-mode:multiply" opacity="0.42"/>')
    o.append(f'<rect x="{x0 - 60}" y="{top - 20}" width="{face_w + 120}" '
             f'height="{face_h + 50}" fill="url(#faceV)"/>')
    o.append(f'<g filter="url(#soft22)" opacity="0.4">'
             f'<ellipse cx="{x0 + face_w * 0.22}" cy="{cy}" rx="{face_w * 0.09:.0f}" '
             f'ry="{face_h * 0.36:.0f}" fill="#FFFFFF"/></g>')
    o.append(f'<g filter="url(#soft12)" opacity="0.5">'
             f'<path d="M{x0 + 10} {top} V{bot}" stroke="#7A7367" stroke-width="30" fill="none"/>'
             f'<path d="M{x1 - 10} {top} V{bot}" stroke="#6E6759" stroke-width="34" fill="none"/>'
             f'<path d="M{x0} {top + face_h * 0.05} H{x1}" stroke="#7A7367" stroke-width="26" fill="none"/>'
             f'<path d="M{x0} {bot - face_h * 0.04} H{x1}" stroke="#7A7367" stroke-width="26" fill="none"/>'
             f'</g>')
    o.append(f'<g opacity="0.06" style="mix-blend-mode:multiply">'
             f'<rect x="{x0 - 60}" y="{top - 20}" width="{face_w + 120}" '
             f'height="{face_h + 50}" filter="url(#filmgrain)"/></g>')
    o.append("</g>")

    # Sewn seams at the head and the foot.
    for sy in (top + face_h * 0.035, bot - face_h * 0.03):
        o.append(f'<path d="M{x0 + face_w * 0.06} {sy:.0f} H{x1 - face_w * 0.06}" '
                 f'stroke="#6F6A5E" stroke-width="5" stroke-dasharray="16 13" opacity="0.5"/>')
    return "".join(o)


# ------------------------------------------------------------------- shots

MARKS = [("ooid", "Oolitic", "aragonite"), ("screen", "Washed and", "screened"),
         ("nokiln", "Not", "calcined"), ("lot", "Analysed", "by lot")]


def bag20(grade):
    face_w, face_h = 560, 900
    cx, cy = 620, 600
    art = pack_face(cx - face_w / 2, cy - face_h / 2, face_w, face_h,
                    band=face_w * 0.115, headline="ARAGONITE", grade=grade,
                    net_big="20 lb", net_small="9.07 kg",
                    lot="AC-2608-" + grade["name"][0] + "01", marks=MARKS,
                    qr_seed=SEEDS[grade["slug"]])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">{esc(grade["name"])} grade aragonite, 20 lb bag</title>'
         f'<desc id="d">Studio render of the 20 lb bag of {esc(grade["name"].lower())} grade '
         f'oolitic aragonite, {esc(grade["grain_mm"])}, standing on a white sweep beside a '
         f'poured cone of the grade. A render of proposed packaging, not a photograph of a '
         f'produced bag.</desc>',
         studio_defs(), set_dressing(), zoom(1.22, 890, 610)]
    o.append(sack(face_w, face_h, cx, cy, art, seed=SEEDS[grade["slug"]]))
    o.append(heap(1240, cy + face_h / 2 + 4, 400, 200, grade, SEEDS[grade["slug"]]))
    o.append("</g></svg>")
    return "".join(o)


def bag50(grade):
    face_w, face_h = 620, 960
    cx, cy = 650, 600
    art = pack_face(cx - face_w / 2, cy - face_h / 2, face_w, face_h,
                    band=face_w * 0.115, headline="ARAGONITE", grade=None,
                    net_big="50 lb", net_small="22.68 kg", lot="AC-2608-M01",
                    marks=MARKS, qr_seed=77)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">Aragonite, 50 lb woven polypropylene bag</title>'
         f'<desc id="d">Studio render of the 50 lb woven polypropylene bag, sewn at the head '
         f'and foot, standing on a white sweep beside a poured cone of the material. A render '
         f'of proposed packaging, not a photograph of a produced bag.</desc>',
         studio_defs(), set_dressing(), zoom(1.14, 905, 600)]
    o.append(sack(face_w, face_h, cx, cy, art, seed=77))
    o.append(heap(1280, cy + face_h / 2 + 4, 380, 190, grade, 77))
    o.append("</g></svg>")
    return "".join(o)


def tote():
    """The bulk sack: a filled FIBC with four lift loops, standing on a pallet.

    Its panel is close to square, where the tall-bag layout collides with
    itself, so the sack carries its own arrangement of the same parts: badge,
    brand, product name, the four marks, and the water running to the foot of
    the sack rather than to the foot of a panel drawn on it.
    """
    bw, bh = 760, 660
    cx, cy = 800, 520
    x0, x1 = cx - bw / 2, cx + bw / 2
    top, bot = cy - bh / 2, cy + bh / 2

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">Aragonite, bulk sack on a pallet</title>'
         f'<desc id="d">Studio render of a filled bulk sack with four blue lift loops and a '
         f'tied fill spout, standing on a wooden pallet. A render of proposed packaging, not '
         f'a photograph of a produced sack.</desc>',
         studio_defs(), set_dressing(), zoom(1.04, 800, 600)]

    py = bot + 6
    o.append(f'<g filter="url(#soft22)"><ellipse cx="{cx + 26}" cy="{py + 118}" rx="480" '
             f'ry="24" fill="#6F6A61" opacity="0.42"/></g>')

    # Four lift loops in the pack's blue, the back pair dimmer and shorter.
    for i, lx in enumerate((x0 + 86, x0 + 238, x1 - 238, x1 - 86)):
        back = i in (1, 2)
        hh = 104 if back else 124
        col = "#2A6076" if back else GUSSET_BLUE
        o.append(f'<path d="M{lx - 27} {top + 26} V{top - hh + 27} a27 27 0 0 1 54 0 '
                 f'V{top + 26}" fill="none" stroke="{col}" stroke-width="24" '
                 f'stroke-linecap="round"/>')
        o.append(f'<path d="M{lx - 31} {top + 26} V{top - hh + 27}" stroke="#FFFFFF" '
                 f'stroke-opacity="0.28" stroke-width="6" stroke-linecap="round"/>')
    # Tied fill spout.
    o.append(f'<path d="M{cx - 54} {top + 14} q8 -70 54 -78 q46 8 54 78 z" fill="#F2EFE7" '
             f'stroke="#A9A294" stroke-width="2"/>')
    o.append(f'<path d="M{cx - 28} {top - 46} q28 -14 56 0" stroke="{NAVY}" stroke-width="5" '
             f'fill="none"/>')

    body = (f'M{x0 + 44} {top} H{x1 - 44} C{x1 + 8} {top + 26} {x1 + 26} {top + 170} '
            f'{x1 + 22} {cy} C{x1 + 18} {bot - 130} {x1 - 4} {bot - 22} {x1 - 50} {bot} '
            f'H{x0 + 50} C{x0 + 4} {bot - 22} {x0 - 18} {bot - 130} {x0 - 22} {cy} '
            f'C{x0 - 26} {top + 170} {x0 - 8} {top + 26} {x0 + 44} {top} Z')
    o.append(f'<clipPath id="tt"><path d="{body}"/></clipPath>')
    o.append(f'<path d="{body}" fill="url(#face)"/>')
    o.append('<g clip-path="url(#tt)">')
    o.append(f'<rect x="{x0 - 40}" y="{top - 20}" width="{bw + 80}" height="{bh + 60}" '
             f'fill="url(#weave)" opacity="0.55"/>')

    # ---- the sack's own arrangement -------------------------------------
    a = []
    a.append(omri_badge(x0 + 112, top + 92, 50))
    ms = (bw * 0.13) / 45
    a.append(f'<g transform="translate({cx - bw * 0.045:.1f} {top + 62:.1f}) scale({ms:.3f})" '
             f'fill="{NAVY}"><circle cx="0" cy="0" r="3.4"/><circle cx="12" cy="-2" r="5.6"/>'
             f'<circle cx="29.5" cy="-5" r="8.6"/>'
             f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{SAND_DEEP}"/></g>')
    a.append(text(cx, top + 112, "Aragonite sand", 44, NAVY, SANS, "700", "middle"))
    a.append(text(cx, top + 136, "by AragoCor Minerals", 18, TIDE, MONO, "400", "middle",
                  spacing="0.06em"))
    a.append(text(cx, top + 214, "ARAGONITE", 86, NAVY, SANS, "700", "middle",
                  spacing="0.005em"))
    a.append(f'<path d="M{x0 + 130} {top + 238} H{x1 - 130}" stroke="{NAVY}" '
             f'stroke-opacity="0.22" stroke-width="3"/>')
    a.append(text(cx, top + 272, "Calcium carbonate (CaCO\u2083)", 28, TIDE, SANS, "500",
                  "middle", spacing="0.03em"))
    ir, iy = 42, top + 348
    step = (bw - 300) / 3
    for i, (kind, l1, l2) in enumerate(MARKS):
        ix = x0 + 150 + i * step
        a.append(spec_icon(ix, iy, ir, kind))
        a.append(text(ix, iy + ir + 26, l1, 17, NAVY, SANS, "600", "middle"))
        a.append(text(ix, iy + ir + 44, l2, 17, NAVY, SANS, "600", "middle"))
        if i < len(MARKS) - 1:
            a.append(f'<path d="M{ix + step / 2:.0f} {iy - 30} V{iy + 30}" stroke="{NAVY}" '
                     f'stroke-opacity="0.16" stroke-width="1.6"/>')
    # The water runs to the foot of the sack, not to the foot of a panel.
    wy = top + 424
    a.append(wave(x0 - 40, wy, bw + 80, bot - wy + 40))
    bwid, bhi = 300, 88
    a.append(f'<rect x="{cx - bwid / 2:.0f}" y="{wy + 58:.0f}" width="{bwid}" height="{bhi}" '
             f'rx="20" fill="{ABYSS}" fill-opacity="0.88" stroke="#FFFFFF" '
             f'stroke-opacity="0.35" stroke-width="3"/>')
    a.append(text(cx, wy + 58 + bhi * 0.58, "2.0 t", 58, "#FFFFFF", SANS, "700", "middle"))
    a.append(text(cx, wy + 58 + bhi * 0.87, "2,000 kg \u00b7 4,409 lb", 19, PALE, MONO,
                  "400", "middle"))
    a.append(qr_block(x0 + 74, wy + 50, 88, 91))
    a.append(text(x0 + 74, wy + 50 + 88 + 22, "Scan for lot analysis", 18, "#FFFFFF",
                  SANS, "600"))
    a.append(text(x0 + 74, wy + 50 + 88 + 42, "Lot AC-2608-M01", 18, PALE, MONO, "500"))
    a.append(text(cx, bot - 22, "ARAGONITESAND.COM", 25, "#FFFFFF", SANS, "600", "middle",
                  spacing="0.09em"))
    o.append("".join(a))

    o.append(f'<path d="{body}" fill="url(#face)" style="mix-blend-mode:multiply" opacity="0.34"/>')
    o.append(f'<rect x="{x0 - 40}" y="{top - 20}" width="{bw + 80}" height="{bh + 60}" '
             f'fill="url(#faceV)"/>')
    for sx in (x0 + 52, x1 - 52):
        o.append(f'<g filter="url(#soft12)" opacity="0.38">'
                 f'<path d="M{sx} {top} V{bot}" stroke="#867F72" stroke-width="30" fill="none"/></g>')
    o.append(f'<g filter="url(#soft22)" opacity="0.3">'
             f'<ellipse cx="{x0 + 200}" cy="{cy}" rx="80" ry="{bh * 0.34:.0f}" fill="#FFFFFF"/></g>')
    o.append(f'<g opacity="0.06" style="mix-blend-mode:multiply">'
             f'<rect x="{x0 - 40}" y="{top - 20}" width="{bw + 80}" height="{bh + 60}" '
             f'filter="url(#filmgrain)"/></g>')
    o.append("</g>")

    # Pallet, sitting directly under the sack.
    pw = bw + 130
    px = cx - pw / 2
    o.append(f'<rect x="{px}" y="{py}" width="{pw}" height="24" rx="3" fill="url(#pallet)"/>')
    for i in range(3):
        o.append(f'<rect x="{px + 20 + i * (pw - 118) / 2:.0f}" y="{py + 24}" width="98" '
                 f'height="50" fill="#B08E56"/>')
    o.append(f'<rect x="{px}" y="{py + 74}" width="{pw}" height="22" rx="3" fill="url(#pallet)"/>')
    o.append(f'<g filter="url(#soft6)" opacity="0.32">'
             f'<rect x="{px}" y="{py}" width="{pw}" height="12" fill="#5E5850"/></g>')
    o.append("</g></svg>")
    return "".join(o)



def family(grades):
    """The three grades together, which is the one shot a buyer wants first.

    Centre bag forward and full size, the other two set back and smaller, with
    a cone of each grade along the front so the difference the grades are sold
    on is visible in the same frame as the pack.
    """
    W2, H2 = 1600, 1067
    order = ["coarse", "medium", "fine"]
    by = {g["slug"]: g for g in grades}
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H2}" width="{W2}" '
         f'height="{H2}" role="img" aria-labelledby="t d">'
         f'<title id="t">Aragonite sand, the three grades</title>'
         f'<desc id="d">Studio render of the 20 lb bags of fine, medium and coarse grade '
         f'aragonite standing together on a white sweep, with a poured cone of each grade '
         f'in front. A render of proposed packaging, not a photograph of produced bags.</desc>',
         studio_defs(),
         f'<rect width="{W2}" height="{H2}" fill="url(#sweep)"/>'
         f'<rect width="{W2}" height="{H2}" fill="url(#vignette)"/>',
         zoom(0.92, 800, 600)]

    # Back pair first, dimmed into the sweep so the centre bag reads forward.
    for slug, cx, k in (("coarse", 470, 0.80), ("fine", 1145, 0.80)):
        g = by[slug]
        art = pack_face(cx - 280, 560 - 450, 560, 900, band=560 * 0.115,
                        headline="ARAGONITE", grade=g, net_big="20 lb",
                        net_small="9.07 kg", lot="AC-2608-" + g["name"][0] + "01",
                        marks=MARKS, qr_seed=SEEDS[slug])
        o.append(f'<g transform="translate({cx * (1 - k):.1f} {560 * (1 - k):.1f}) scale({k})" '
                 f'opacity="0.93">')
        o.append(sack(560, 900, cx, 560, art, seed=SEEDS[slug]))
        o.append("</g>")
    g = by["medium"]
    art = pack_face(800 - 280, 600 - 450, 560, 900, band=560 * 0.115,
                    headline="ARAGONITE", grade=g, net_big="20 lb", net_small="9.07 kg",
                    lot="AC-2608-M01", marks=MARKS, qr_seed=SEEDS["medium"])
    o.append(sack(560, 900, 800, 600, art, seed=SEEDS["medium"]))

    # A cone of each grade along the front edge, smallest grain to largest.
    for i, slug in enumerate(("fine", "medium", "coarse")):
        o.append(heap(430 + i * 370, 1040, 260, 116, by[slug], SEEDS[slug] + 500))
    o.append("</g></svg>")
    return "".join(o)


def main():
    grades = json.loads((ROOT / "data" / "grades.json").read_text())["grades"]
    OUT.mkdir(parents=True, exist_ok=True)
    for g in grades:
        (OUT / f'bag20-{g["slug"]}.svg').write_text(bag20(g), encoding="utf-8")
        print("wrote", f'bag20-{g["slug"]}.svg')
    medium = next(g for g in grades if g["slug"] == "medium")
    (OUT / "bag50.svg").write_text(bag50(medium), encoding="utf-8")
    print("wrote bag50.svg")
    (OUT / "tote.svg").write_text(tote(), encoding="utf-8")
    print("wrote tote.svg")
    (OUT / "family.svg").write_text(family(grades), encoding="utf-8")
    print("wrote family.svg")


if __name__ == "__main__":
    main()
