#!/usr/bin/env python3
"""Draw the pack and grade figures into assets/figures/.

    python3 tools/make-figures.py

These are drawings, not photographs. No photograph of the product exists and
none can be invented, so the slots that can be served honestly by a technical
figure are served by one: the four pack formats, the three retail bags and the
three grain plates. The rest of data/images.json stays a photography brief.

Everything here is generated from data/grades.json and data/products.json, so
a figure cannot disagree with the catalogue: change a grain size or a net
weight and the drawing changes with it.

Standard library only. Deterministic: same input, byte-identical output.
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "figures"

INK = "#0B2C3A"
ABYSS = "#061C26"
TIDE = "#4E6B74"
SAND = "#E0C68F"
SAND_DEEP = "#C9A968"
BONE = "#F6F2E9"
PAPER = "#FFFFFF"
SURF = "#17707E"

SANS = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# The grain tones, coarse to fine. Oolitic aragonite is an off-white ooid with
# a warmer core, so each grain is drawn as a light body with a deeper rim.
GRAIN_BODY = ["#EFE4CC", "#E8D9BA", "#E0CDA8"]
GRAIN_RIM = ["#CBB183", "#C0A373", "#B59565"]


def head(w, h, title, desc):
    """Open the file, carrying its own label.

    The label used to be a printed footer rail. At product-card width that rail
    renders at about five pixels and is unreadable, so it is noise where it
    matters most. It lives here instead, where a screen reader and anyone
    opening the file on its own will find it, and the page repeats it in a
    caption that is legible at any size.
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title>'
        f'<desc id="d">{esc(desc)} Drawn from the catalogue data, not a photograph.</desc>'
    )


def text(x, y, s, size=14, fill=INK, family=SANS, weight="400",
         anchor="start", spacing=None, opacity=None):
    attrs = (
        f'x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"'
    )
    if spacing is not None:
        attrs += f' letter-spacing="{spacing}"'
    if opacity is not None:
        attrs += f' opacity="{opacity}"'
    return f'<text {attrs}>{esc(s)}</text>'


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def mark(x, y, scale=1.0, fill=INK, rule=SAND_DEEP):
    """The site's own mark: three grades on a screen line."""
    g = (
        f'<g transform="translate({x} {y}) scale({scale})">'
        f'<circle cx="0" cy="0" r="3.4" fill="{fill}"/>'
        f'<circle cx="12" cy="-2" r="5.6" fill="{fill}"/>'
        f'<circle cx="29.5" cy="-5" r="8.6" fill="{fill}"/>'
        f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{rule}"/>'
        f'</g>'
    )
    return g


def shadow(cx, cy, rx, ry, opacity=0.13):
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{INK}" '
            f'opacity="{opacity}"/>')


def grain_window(x, y, w, h, grade, px_per_mm, seed, bg=PAPER, tone=1):
    """A window of grains drawn at true scale, for the bag print."""
    rnd = random.Random(seed)
    lo, hi = grade["grain_min_mm"], grade["grain_max_mm"]
    body, rim = GRAIN_BODY[tone], GRAIN_RIM[tone]
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{bg}"/>']
    placed = []
    tries = 0
    while tries < 4000 and len(placed) < 70:
        tries += 1
        d = rnd.uniform(lo, hi) * px_per_mm
        r = d / 2
        cx = rnd.uniform(x + r + 1, x + w - r - 1)
        cy = rnd.uniform(y + r + 1, y + h - r - 1)
        if any((cx - a) ** 2 + (cy - b) ** 2 < (r + c + 0.6) ** 2 for a, b, c in placed):
            continue
        placed.append((cx, cy, r))
        sq = 1 + rnd.uniform(-0.09, 0.09)
        rot = rnd.uniform(0, 180)
        parts.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.2f}" ry="{r * sq:.2f}" '
            f'transform="rotate({rot:.0f} {cx:.1f} {cy:.1f})" fill="{body}" '
            f'stroke="{rim}" stroke-width="{min(2.2, max(0.4, r * 0.12)):.2f}"/>'
        )
    return "".join(parts)


# ---------------------------------------------------------------- 20 lb bag

SEEDS = {"fine": 101, "medium": 202, "coarse": 303}


def grains(x, y, w, h, lo_mm, hi_mm, px_per_mm, seed, tone, target, highlight=6.0):
    """A field of grains packed at true scale.

    Oolitic aragonite is a near-spherical ooid, so the grain is an ellipse a
    few percent off round rather than a crushed angular particle. Sizes are
    drawn from the middle of the screened band, which is where a sieved cut
    actually sits. Small grains are emitted as circles: the rotation is
    invisible below a few pixels and the file is a third of the size without it.
    """
    rnd = random.Random(seed)
    body, rim = GRAIN_BODY[tone], GRAIN_RIM[tone]
    placed = []
    tries = 0
    while tries < 90000 and len(placed) < target:
        tries += 1
        d = (rnd.uniform(lo_mm, hi_mm) + rnd.uniform(lo_mm, hi_mm)) / 2 * px_per_mm
        r = d / 2
        cx = rnd.uniform(x + r * 0.35, x + w - r * 0.35)
        cy = rnd.uniform(y + r * 0.35, y + h - r * 0.35)
        if any((cx - a) ** 2 + (cy - b) ** 2 < (r + c + 0.5) ** 2 for a, b, c in placed):
            continue
        placed.append((cx, cy, r))
    out = []
    # Largest first, so the small grains read as sitting in the gaps.
    for cx, cy, r in sorted(placed, key=lambda g: -g[2]):
        sw = f"{min(2.2, max(0.35, r * 0.1)):.2f}"
        if r < 3.5:
            out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="{body}" '
                       f'stroke="{rim}" stroke-width="{sw}"/>')
            continue
        sq = 1 + rnd.uniform(-0.1, 0.1)
        rot = rnd.uniform(0, 180)
        out.append(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.2f}" ry="{r * sq:.2f}" '
            f'transform="rotate({rot:.0f} {cx:.1f} {cy:.1f})" fill="{body}" '
            f'stroke="{rim}" stroke-width="{sw}"/>'
        )
        if r > highlight:
            out.append(f'<ellipse cx="{cx - r * 0.26:.1f}" cy="{cy - r * 0.28:.1f}" '
                       f'rx="{r * 0.26:.2f}" ry="{r * 0.2:.2f}" fill="{PAPER}" opacity="0.32"/>')
    return "".join(out)


def weave(pid, step=4.5, opacity=0.07):
    """Woven polypropylene: a fine cross weave, not graph paper."""
    return (
        f'<defs><pattern id="{pid}" width="{step}" height="{step}" '
        f'patternUnits="userSpaceOnUse">'
        f'<path d="M0 {step / 2} H{step} M{step / 2} 0 V{step}" stroke="{INK}" '
        f'stroke-opacity="{opacity}" stroke-width="0.8"/></pattern></defs>'
    )


# ---------------------------------------------------------------- 20 lb bag

def bag20(grade, tone):
    w, h = 800, 600
    bx, by, bw, bh = 262, 40, 276, 516
    out = [head(w, h, f'{grade["name"]} grade, 20 lb printed retail bag',
                f'The {grade["name"].lower()} grade retail bag: {grade["grain_mm"]}, {grade["mesh"]} mesh, net 20 lb, with a window of grain drawn at actual size.'),
           f'<rect width="{w}" height="{h}" fill="{PAPER}"/>']
    out.append(shadow(bx + bw / 2, by + bh + 10, bw * 0.54, 12))

    # A stand-up pouch: square shoulders, a base a little wider than the top.
    body = (
        f'M{bx + 18} {by} H{bx + bw - 18} Q{bx + bw} {by} {bx + bw + 2} {by + 20} '
        f'L{bx + bw + 8} {by + bh - 18} Q{bx + bw + 10} {by + bh} {bx + bw - 10} {by + bh} '
        f'H{bx + 10} Q{bx - 10} {by + bh} {bx - 8} {by + bh - 18} '
        f'L{bx - 2} {by + 20} Q{bx} {by} {bx + 18} {by} Z'
    )
    out.append(f'<path d="{body}" fill="{BONE}" stroke="{INK}" stroke-width="1.6" '
               f'stroke-opacity="0.32"/>')
    # The light and shade down each gusset.
    out.append(f'<path d="M{bx + 16} {by + 62} L{bx + 10} {by + bh - 14}" stroke="{INK}" '
               f'stroke-width="1" stroke-opacity="0.12" fill="none"/>')
    out.append(f'<path d="M{bx + bw - 16} {by + 62} L{bx + bw - 10} {by + bh - 14}" '
               f'stroke="{INK}" stroke-width="1" stroke-opacity="0.12" fill="none"/>')

    # Sealed top band, with the handle cut through it.
    out.append(
        f'<path d="M{bx + 18} {by} H{bx + bw - 18} Q{bx + bw} {by} {bx + bw + 2} {by + 20} '
        f'L{bx + bw + 3} {by + 58} H{bx - 3} L{bx - 2} {by + 20} '
        f'Q{bx} {by} {bx + 18} {by} Z" fill="{INK}"/>'
    )
    out.append(f'<rect x="{bx + bw / 2 - 44}" y="{by + 22}" width="88" height="14" '
               f'rx="7" fill="{PAPER}"/>')

    # Print.
    px = bx + 28
    out.append(mark(px + 2, by + 100, 0.9, INK, SAND_DEEP))
    out.append(text(px, by + 130, "Aragonite sand", 17, INK, SANS, "700"))
    out.append(text(px, by + 148, "by AragoCor Minerals", 8.5, TIDE, MONO, "400",
                    spacing="0.06em"))
    out.append(f'<rect x="{px}" y="{by + 160}" width="{bw - 56}" height="1.4" fill="{SAND}"/>')

    out.append(text(px, by + 208, grade["name"], 40, INK, SANS, "700"))
    out.append(text(px, by + 230, f'{grade["grain_mm"]} · {grade["mesh"]} mesh',
                    11.5, SURF, MONO, "500"))

    # A window of the grade at true scale, so the three bags differ the way
    # the product does rather than by a colour swatch.
    wy, wh = by + 246, 140
    out.append(f'<rect x="{px}" y="{wy}" width="{bw - 56}" height="{wh}" rx="3" '
               f'fill="{PAPER}" stroke="{INK}" stroke-opacity="0.18"/>')
    out.append(f'<clipPath id="win"><rect x="{px}" y="{wy}" width="{bw - 56}" '
               f'height="{wh}" rx="3"/></clipPath>')
    out.append(f'<g clip-path="url(#win)">')
    out.append(grains(px, wy, bw - 56, wh, grade["grain_min_mm"], grade["grain_max_mm"],
                      15.0, SEEDS[grade["slug"]], tone,
                      {"fine": 260, "medium": 120, "coarse": 40}[grade["slug"]]))
    out.append("</g>")
    out.append(text(px, by + 404, "Grain shown at actual size", 8.5, TIDE, MONO, "400",
                    spacing="0.05em"))

    out.append(f'<rect x="{px - 10}" y="{by + 420}" width="{bw - 36}" height="1.2" '
               f'fill="{INK}" opacity="0.16"/>')
    out.append(text(px, by + 452, "Net 20 lb", 22, INK, SANS, "700"))
    out.append(text(px, by + 470, "9.07 kg", 10.5, TIDE, MONO, "400"))
    out.append(text(bx + bw - 28, by + 452, "Lot", 9, TIDE, MONO, "400", anchor="end",
                    spacing="0.08em"))
    out.append(text(bx + bw - 28, by + 470, "AC-____-" + grade["name"][0] + "__", 11,
                    INK, MONO, "500", anchor="end"))

    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- 50 lb bag

def bag50(grades):
    w, h = 800, 600
    bx, by, bw, bh = 222, 56, 356, 484
    out = [head(w, h, '50 lb woven polypropylene trade bag',
                'The 50 lb trade bag: plain woven polypropylene, sewn top and foot, net 50 lb, grade marked at packing.'),
           f'<rect width="{w}" height="{h}" fill="{PAPER}"/>', weave("weave50")]
    out.append(shadow(bx + bw / 2, by + bh + 8, bw * 0.5, 11))

    # A sewn pillow bag: the ends pinch at the seams, the middle bellies out.
    body = (
        f'M{bx + 6} {by + 30} Q{bx + bw / 2} {by + 2} {bx + bw - 6} {by + 30} '
        f'Q{bx + bw + 13} {by + bh / 2} {bx + bw - 6} {by + bh - 30} '
        f'Q{bx + bw / 2} {by + bh - 2} {bx + 6} {by + bh - 30} '
        f'Q{bx - 13} {by + bh / 2} {bx + 6} {by + 30} Z'
    )
    out.append(f'<path d="{body}" fill="{BONE}" stroke="{INK}" stroke-width="1.6" '
               f'stroke-opacity="0.3"/>')
    out.append(f'<path d="{body}" fill="url(#weave50)"/>')
    # Stitching at both seams.
    out.append(f'<path d="M{bx + 14} {by + 22} Q{bx + bw / 2} {by - 4} {bx + bw - 14} {by + 22}" '
               f'stroke="{TIDE}" stroke-width="1.5" stroke-dasharray="7 6" fill="none" '
               f'opacity="0.7"/>')
    out.append(f'<path d="M{bx + 14} {by + bh - 22} Q{bx + bw / 2} {by + bh + 4} '
               f'{bx + bw - 14} {by + bh - 22}" stroke="{TIDE}" stroke-width="1.5" '
               f'stroke-dasharray="7 6" fill="none" opacity="0.7"/>')

    cx = bx + bw / 2
    out.append(mark(cx - 22, by + 112, 1.05, INK, SAND_DEEP))
    out.append(text(cx, by + 152, "Aragonite sand", 25, INK, SANS, "700", anchor="middle"))
    out.append(text(cx, by + 172, "Oolitic aragonite · washed and screened", 10, TIDE,
                    MONO, "400", anchor="middle"))
    out.append(f'<rect x="{cx - 104}" y="{by + 192}" width="208" height="1.4" fill="{SAND}"/>')

    # Every grade ships in this bag, so the grade is marked at packing rather
    # than printed into the artwork.
    yy = by + 220
    for i, g in enumerate(grades):
        gx = cx - 105 + i * 71
        out.append(f'<rect x="{gx}" y="{yy}" width="59" height="26" rx="3" fill="none" '
                   f'stroke="{INK}" stroke-opacity="0.4"/>')
        out.append(text(gx + 29.5, yy + 18, g["name"], 12, INK, SANS, "600", anchor="middle"))
    out.append(text(cx, yy + 46, "Grade marked at packing", 9, TIDE, MONO, "400",
                    anchor="middle", spacing="0.05em"))

    out.append(text(cx, by + 356, "Net 50 lb", 29, INK, SANS, "700", anchor="middle"))
    out.append(text(cx, by + 376, "22.7 kg", 10.5, TIDE, MONO, "400", anchor="middle"))
    out.append(f'<rect x="{cx - 90}" y="{by + 394}" width="180" height="30" rx="3" '
               f'fill="{PAPER}" fill-opacity="0.75" stroke="{INK}" stroke-opacity="0.28"/>')
    out.append(text(cx, by + 414, "Lot AC-____-___", 12.5, INK, MONO, "500", anchor="middle"))

    out.append("</svg>")
    return "".join(out)


# -------------------------------------------------------------------- tote

def tote():
    w, h = 800, 600
    bx, by, bw, bh = 250, 122, 300, 296
    out = [head(w, h, '2,000 lb FIBC bulk bag on a GMA pallet',
                'A filled bulk bag with four lift loops, a fill spout at the top and a discharge spout below, standing on a 48 by 40 inch pallet.'),
           f'<rect width="{w}" height="{h}" fill="{PAPER}"/>', weave("weaveT", 5, 0.06)]
    out.append(shadow(bx + bw / 2, 502, 190, 13))

    # Four lift loops, the pair at the back drawn first and dimmer.
    for i, lx in enumerate((bx + 30, bx + 92, bx + bw - 92, bx + bw - 30)):
        back = i in (1, 2)
        out.append(
            f'<path d="M{lx - 11} {by + 6} V{by - 30} a11 11 0 0 1 22 0 V{by + 6}" '
            f'fill="none" stroke="{TIDE}" stroke-width="7" stroke-linecap="round" '
            f'opacity="{0.4 if back else 0.62}"/>'
        )
    # Fill spout, behind the front loops.
    out.append(f'<rect x="{bx + bw / 2 - 24}" y="{by - 22}" width="48" height="28" rx="4" '
               f'fill="{BONE}" stroke="{INK}" stroke-width="1.3" stroke-opacity="0.28"/>')

    # Body. A filled FIBC bellies out at the belt line and pinches at the seams.
    body = (
        f'M{bx + 8} {by} H{bx + bw - 8} Q{bx + bw} {by} {bx + bw} {by + 10} '
        f'Q{bx + bw + 12} {by + bh / 2} {bx + bw} {by + bh - 10} '
        f'Q{bx + bw} {by + bh} {bx + bw - 8} {by + bh} H{bx + 8} '
        f'Q{bx} {by + bh} {bx} {by + bh - 10} '
        f'Q{bx - 12} {by + bh / 2} {bx} {by + 10} Q{bx} {by} {bx + 8} {by} Z'
    )
    out.append(f'<path d="{body}" fill="{BONE}" stroke="{INK}" stroke-width="1.6" '
               f'stroke-opacity="0.3"/>')
    out.append(f'<path d="{body}" fill="url(#weaveT)"/>')
    # Corner seams.
    for sx in (bx + 16, bx + bw - 16):
        out.append(f'<path d="M{sx} {by + 4} V{by + bh - 4}" stroke="{INK}" '
                   f'stroke-width="1" stroke-opacity="0.1"/>')

    # Label panel.
    lx, ly, lw, lh = bx + 32, by + 72, bw - 64, 148
    out.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="4" fill="{PAPER}" '
               f'stroke="{INK}" stroke-opacity="0.2"/>')
    out.append(mark(lx + 18, ly + 38, 0.78, INK, SAND_DEEP))
    out.append(text(lx + 18, ly + 68, "Aragonite sand", 15, INK, SANS, "700"))
    out.append(text(lx + 18, ly + 88, "Oolitic aragonite · grade at packing", 8.5, TIDE,
                    MONO, "400"))
    out.append(f'<rect x="{lx + 18}" y="{ly + 100}" width="{lw - 36}" height="1.2" fill="{SAND}"/>')
    out.append(text(lx + 18, ly + 130, "Net 2,000 lb", 19, INK, SANS, "700"))
    out.append(text(lx + lw - 18, ly + 130, "907 kg", 10.5, TIDE, MONO, "400", anchor="end"))

    # Discharge spout, then the pallet the bag stands on.
    out.append(f'<path d="M{bx + bw / 2 - 19} {by + bh - 2} h38 l-5 18 h-28 z" fill="{BONE}" '
               f'stroke="{INK}" stroke-width="1.2" stroke-opacity="0.26"/>')
    py, pw = by + bh + 16, bw + 40
    px = bx + bw / 2 - pw / 2
    out.append(f'<rect x="{px}" y="{py}" width="{pw}" height="11" fill="{SAND}" '
               f'stroke="{INK}" stroke-opacity="0.3"/>')
    for i in range(3):
        out.append(f'<rect x="{px + 10 + i * (pw - 56) / 2}" y="{py + 11}" width="36" '
                   f'height="21" fill="{SAND_DEEP}" stroke="{INK}" stroke-opacity="0.3"/>')
    out.append(f'<rect x="{px}" y="{py + 32}" width="{pw}" height="9" fill="{SAND}" '
               f'stroke="{INK}" stroke-opacity="0.3"/>')
    out.append(text(px + pw + 16, py + 26, "48 × 40 in", 10, TIDE, MONO, "400"))

    out.append("</svg>")
    return "".join(out)


# -------------------------------------------------------------------- bulk

def bulk():
    w, h = 800, 600
    ground = 470
    out = [head(w, h, 'Bulk aragonite, loaded by the ton',
                'A screened stockpile standing at its angle of repose beside a walking-floor trailer carrying a 24 ton load.'),
           f'<rect width="{w}" height="{h}" fill="{PAPER}"/>']

    # Walking-floor trailer, drawn in proportion: body on a chassis rail, the
    # tandem tucked under the rear, landing gear forward of it.
    tx, tw = 428, 328
    ty, th = 208, 218
    chassis_y = ty + th
    out.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="3" fill="{BONE}" '
               f'stroke="{INK}" stroke-width="1.5" stroke-opacity="0.28"/>')
    for i in range(1, 8):
        out.append(f'<path d="M{tx + i * tw / 8:.0f} {ty + 8} V{chassis_y - 8}" stroke="{INK}" '
                   f'stroke-opacity="0.1" stroke-width="1.1"/>')
    out.append(f'<rect x="{tx - 5}" y="{ty - 11}" width="{tw + 10}" height="12" rx="3" '
               f'fill="{TIDE}" opacity="0.45"/>')
    out.append(f'<rect x="{tx + 4}" y="{chassis_y}" width="{tw - 8}" height="10" rx="2" '
               f'fill="{INK}" opacity="0.3"/>')
    out.append(text(tx + tw / 2, ty + th / 2 + 6, "24 ton load", 17, TIDE, SANS, "600",
                    anchor="middle"))

    # Tandem, tucked under the rear.
    axle_y = ground - 20
    out.append(f'<rect x="{tx + tw - 132}" y="{chassis_y + 8}" width="116" height="6" '
               f'fill="{INK}" opacity="0.28"/>')
    for wx in (tx + tw - 108, tx + tw - 44):
        out.append(f'<circle cx="{wx}" cy="{axle_y}" r="20" fill="{INK}" opacity="0.72"/>')
        out.append(f'<circle cx="{wx}" cy="{axle_y}" r="7" fill="{BONE}"/>')
    # Landing gear, with a foot pad on the ground.
    for gx in (tx + 46, tx + 66):
        out.append(f'<rect x="{gx}" y="{chassis_y + 8}" width="6" height="{ground - chassis_y - 12}" '
                   f'fill="{INK}" opacity="0.38"/>')
    out.append(f'<rect x="{tx + 40}" y="{ground - 5}" width="38" height="5" fill="{INK}" '
               f'opacity="0.38"/>')

    # The stockpile. Screened carbonate sand stands at about 34 degrees, so the
    # flanks are drawn to that rather than to a decorative cone.
    px, pw, ph = 48, 366, 134
    apex_l, apex_r = px + pw * 0.40, px + pw * 0.60
    out.append(shadow(px + pw / 2, ground + 5, pw * 0.55, 11, 0.09))
    pile = (f'M{px} {ground} L{apex_l:.0f} {ground - ph} '
            f'Q{px + pw / 2:.0f} {ground - ph - 13} {apex_r:.0f} {ground - ph} '
            f'L{px + pw} {ground} Z')
    out.append(f'<path d="{pile}" fill="{GRAIN_BODY[1]}" stroke="{SAND_DEEP}" stroke-width="1.5"/>')
    out.append(f'<path d="M{apex_r:.0f} {ground - ph} L{px + pw} {ground} '
               f'L{px + pw * 0.56:.0f} {ground} Z" fill="{SAND_DEEP}" opacity="0.2"/>')
    rnd = random.Random(7)
    for _ in range(120):
        t = rnd.random()
        sx = px + pw * t
        if t < 0.40:
            top = ground - ph * (t / 0.40)
        elif t > 0.60:
            top = ground - ph * ((1 - t) / 0.40)
        else:
            top = ground - ph
        sy = rnd.uniform(top + 7, ground - 3)
        out.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{rnd.uniform(1.0, 2.2):.1f}" '
                   f'fill="{GRAIN_RIM[2]}" opacity="0.45"/>')

    out.append(f'<path d="M30 {ground} H772" stroke="{INK}" stroke-width="1.5" '
               f'stroke-opacity="0.42"/>')
    out.append(text(px + pw / 2, ground + 32, "Screened, stockpiled under cover", 11.5, TIDE,
                    SANS, "500", anchor="middle"))
    out.append(text(tx + tw / 2, ground + 32, "Walking-floor or end-dump", 11.5, TIDE, SANS,
                    "500", anchor="middle"))
    out.append(text(400, ground + 60, "One load is 24 ton. Grades are not mixed in a bulk load.",
                    11, TIDE, SANS, "400", anchor="middle"))

    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------- grain plates

def grain_plate(grade, tone):
    """A field of grains at true scale against a millimetre rule.

    All three plates are drawn at one scale across one field width, so the
    grades can be read against the rule and against each other.
    """
    w, h = 900, 600
    field_mm = 30.0
    fx, fy, fh = 46, 78, 396
    fw = w - 92
    px_per_mm = fw / field_mm
    out = [head(w, h, f'{grade["name"]} grade at scale',
                f'A field of {grade["name"].lower()} grade aragonite grains, {grade["grain_mm"]}, drawn at true size against a thirty millimetre rule.'),
           f'<rect width="{w}" height="{h}" fill="{PAPER}"/>']

    out.append(text(fx, 46, f'{grade["name"]} grade', 21, INK, SANS, "700"))
    out.append(text(w - fx, 46, f'{grade["grain_mm"]} · {grade["mesh"]} mesh', 12.5, SURF,
                    MONO, "500", anchor="end"))

    out.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="4" fill="{BONE}" '
               f'stroke="{INK}" stroke-opacity="0.2"/>')
    out.append(f'<clipPath id="fld"><rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="4"/></clipPath>')
    out.append('<g clip-path="url(#fld)">')
    out.append(grains(fx, fy, fw, fh, grade["grain_min_mm"], grade["grain_max_mm"],
                      px_per_mm, SEEDS[grade["slug"]] + 7, tone,
                      {"fine": 760, "medium": 390, "coarse": 132}[grade["slug"]],
                      highlight=7.0))
    out.append("</g>")

    # The rule, in millimetres, directly under the field.
    ry = fy + fh + 40
    out.append(text(w - fx, ry - 10, "millimetres", 10, TIDE, MONO, "400", anchor="end",
                    spacing="0.06em"))
    out.append(f'<rect x="{fx}" y="{ry}" width="{fw}" height="28" rx="3" fill="{BONE}" '
               f'stroke="{INK}" stroke-opacity="0.22"/>')
    for mm in range(int(field_mm) + 1):
        x = fx + mm * px_per_mm
        major = mm % 5 == 0
        out.append(f'<path d="M{x:.1f} {ry} V{ry + (14 if major else 7)}" stroke="{INK}" '
                   f'stroke-width="{1.3 if major else 0.8}" '
                   f'stroke-opacity="{0.7 if major else 0.38}"/>')
        if major:
            anchor = "start" if mm == 0 else ("end" if mm == int(field_mm) else "middle")
            dx = 3 if mm == 0 else (-3 if mm == int(field_mm) else 0)
            out.append(text(x + dx, ry + 25, str(mm), 10, INK, MONO, "500", anchor=anchor))

    out.append("</svg>")
    return "".join(out)


def main():
    grades = json.loads((ROOT / "data" / "grades.json").read_text())["grades"]
    tones = {"fine": 0, "medium": 1, "coarse": 2}
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    for g in grades:
        for name, svg in (
            (f'bag20-{g["slug"]}.svg', bag20(g, tones[g["slug"]])),
            (f'grain-{g["slug"]}.svg', grain_plate(g, tones[g["slug"]])),
        ):
            (OUT / name).write_text(svg, encoding="utf-8")
            written.append(name)

    for name, svg in (("bag50.svg", bag50(grades)), ("tote.svg", tote()), ("bulk.svg", bulk())):
        (OUT / name).write_text(svg, encoding="utf-8")
        written.append(name)

    for n in written:
        print("wrote assets/figures/" + n)


if __name__ == "__main__":
    main()
