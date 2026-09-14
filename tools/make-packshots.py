#!/usr/bin/env python3
"""Render studio pack shots of the bagged line.

    python3 tools/make-packshots.py      # writes the SVG sources
    node tools/render-packshots.mjs      # rasterises them to assets/photos/

These are renders, not photographs. The product has never been photographed,
so the packaging here is a proposal: the artwork, the print positions and the
lot-code block are what the site says the pack carries, drawn onto a lit and
shaded bag so a distributor can see the pack rather than a placeholder.

Lighting is a single soft key from the upper left with a weaker fill from the
right, which is how a pack shot is usually lit and what the shot brief in
data/images.json asks for. Everything else follows from that: the cylindrical
falloff across the face, the specular band left of centre, the occlusion along
the silhouette, and the contact shadow the bag sits in.

Generated from data/grades.json and data/products.json, so the print cannot
disagree with the catalogue. Standard library only; deterministic.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "photos" / "src"

W, H = 1600, 1200

INK = "#0B2C3A"
TIDE = "#4E6B74"
SAND = "#D9BE86"
SAND_DEEP = "#B8975A"
SURF = "#17707E"

SANS = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

SEEDS = {"fine": 101, "medium": 202, "coarse": 303}

# Woven polypropylene, at the scale a 1600 px render sees it.
WEAVE = (
    '<pattern id="weave" width="9" height="9" patternUnits="userSpaceOnUse">'
    '<path d="M0 4.5 H9" stroke="#8C8577" stroke-opacity="0.11" stroke-width="2.6"/>'
    '<path d="M0 2.2 H9" stroke="#FFFFFF" stroke-opacity="0.16" stroke-width="1.4"/>'
    '<path d="M4.5 0 V9" stroke="#6F6A5E" stroke-opacity="0.055" stroke-width="2.4"/>'
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


def text(x, y, s, size=14, fill=INK, family=SANS, weight="400",
         anchor="start", spacing=None, opacity=None):
    a = (f'x="{x:.0f}" y="{y:.0f}" font-family="{family}" font-size="{size:.1f}" '
         f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"')
    if spacing is not None:
        a += f' letter-spacing="{spacing}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return f'<text {a}>{esc(s)}</text>'


def zoom(k, cx, cy):
    """Open a group that scales the subject about a point in the frame.

    The bags are drawn at whatever size keeps their own geometry readable; this
    then sizes them to the frame. A pack shot wants the product filling most of
    the picture, and these slots are seen at card width more often than at full
    size, so the subject is pushed close to the edges.
    """
    return f'<g transform="translate({cx * (1 - k):.1f} {cy * (1 - k):.1f}) scale({k})">'


def studio_defs():
    """The set: sweep, contact shadow, material noise, and the light on the bag."""
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
    <stop offset="1" stop-color="#9A958C" stop-opacity="0.30"/>
  </radialGradient>

  <!-- The key is upper left, so the face brightens off-centre to the left and
       falls away to both edges. -->
  <linearGradient id="face" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#B9B2A4"/>
    <stop offset="0.06" stop-color="#DCD6C9"/>
    <stop offset="0.20" stop-color="#F7F4EC"/>
    <stop offset="0.34" stop-color="#FFFFFF"/>
    <stop offset="0.55" stop-color="#F4F1E8"/>
    <stop offset="0.80" stop-color="#DED8CB"/>
    <stop offset="0.94" stop-color="#C3BCAD"/>
    <stop offset="1" stop-color="#ADA697"/>
  </linearGradient>
  <linearGradient id="faceV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#8E877A" stop-opacity="0.22"/>
    <stop offset="0.14" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="0.82" stop-color="#FFFFFF" stop-opacity="0"/>
    <stop offset="1" stop-color="#7E776B" stop-opacity="0.30"/>
  </linearGradient>
  <linearGradient id="gusset" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#8F8779" stop-opacity="0.55"/>
    <stop offset="0.45" stop-color="#B5AE9F" stop-opacity="0.34"/>
    <stop offset="1" stop-color="#6E675B" stop-opacity="0.52"/>
  </linearGradient>
  <linearGradient id="seal" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#05202B"/>
    <stop offset="0.28" stop-color="#14465A"/>
    <stop offset="0.44" stop-color="#1B5468"/>
    <stop offset="0.72" stop-color="#0C3040"/>
    <stop offset="1" stop-color="#04191F"/>
  </linearGradient>

  <!-- Matte polyethylene: a fine isotropic grain, barely there. -->
  <filter id="filmgrain" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="4" result="n"/>
    <feColorMatrix in="n" type="saturate" values="0"/>
  </filter>
  <filter id="soft40"><feGaussianBlur stdDeviation="40"/></filter>
  <filter id="soft22"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="soft12"><feGaussianBlur stdDeviation="12"/></filter>
  <filter id="soft6"><feGaussianBlur stdDeviation="6"/></filter>
  <filter id="soft3"><feGaussianBlur stdDeviation="3"/></filter>
</defs>'''


def set_dressing():
    return (
        f'<rect width="{W}" height="{H}" fill="url(#sweep)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#vignette)"/>'
    )


def grain_bed(x, y, w, h, lo_mm, hi_mm, px_per_mm, seed, target):
    """Ooids under the same key light as the pack: lit top-left, shadowed below."""
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
        # Each grain sits in its own occlusion, offset away from the key.
        out.append(f'<ellipse cx="{cx + r * 0.2:.1f}" cy="{cy + r * 0.24:.1f}" '
                   f'rx="{r * 1.02:.2f}" ry="{r * 0.9:.2f}" fill="#8E7448" opacity="0.34"/>')
        sq = 1 + rnd2.uniform(-0.09, 0.09)
        rot = rnd2.uniform(0, 180)
        out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r:.2f}" ry="{r * sq:.2f}" '
                   f'transform="rotate({rot:.0f} {cx:.1f} {cy:.1f})" fill="url(#ooid)"/>')
    return "".join(out)


def ooid_gradient():
    """An ooid is a dull carbonate pellet, not a glass bead: the terminator is
    soft, the highlight is broad and low, and the shadow side stays warm."""
    return ('<radialGradient id="ooid" cx="0.38" cy="0.34" r="0.86">'
            '<stop offset="0" stop-color="#F6EDDA"/>'
            '<stop offset="0.38" stop-color="#EADCBD"/>'
            '<stop offset="0.72" stop-color="#D8C49A"/>'
            '<stop offset="0.92" stop-color="#C0A877"/>'
            '<stop offset="1" stop-color="#AD9566"/></radialGradient>')


# --------------------------------------------------------------- 20 lb bag

def bag20(grade):
    """The printed retail bag, three-quarter front, standing on the sweep."""
    fx0, fx1 = 540, 1010          # front face at the waist
    top, bot = 236, 1006
    sh = 30                       # how far the shoulders draw in from the waist
    gus = 78                      # the gusset turned away from the key
    cxm = (fx0 + fx1) / 2
    hgt = bot - top

    # A filled pouch has no straight sides: the face bulges at the waist and
    # draws in at the shoulder and at the base gusset.
    face = (
        f'M{fx0 + sh} {top} '
        f'C{fx0 - 10} {top + 96} {fx0 - 12} {bot - 210} {fx0 + 14} {bot - 46} '
        f'C{fx0 + 30} {bot + 8} {fx1 - 32} {bot + 12} {fx1 - 14} {bot - 44} '
        f'C{fx1 + 12} {bot - 220} {fx1 + 10} {top + 94} {fx1 - sh} {top} Z'
    )
    side = (
        f'M{fx1 - sh} {top} C{fx1 + 10} {top + 94} {fx1 + 12} {bot - 220} '
        f'{fx1 - 14} {bot - 44} '
        f'L{fx1 + gus - 30} {bot - 104} '
        f'C{fx1 + gus + 2} {bot - 250} {fx1 + gus} {top + 120} {fx1 + gus - 44} {top + 26} Z'
    )

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">{esc(grade["name"])} grade aragonite, 20 lb retail bag</title>'
         f'<desc id="d">Studio render of the 20 lb printed retail bag of '
         f'{esc(grade["name"].lower())} grade oolitic aragonite, {esc(grade["grain_mm"])}, '
         f'standing three-quarter front on a white sweep. A render of proposed '
         f'packaging, not a photograph of a produced bag.</desc>',
         studio_defs().replace("</defs>", ooid_gradient() + "</defs>"),
         set_dressing(), zoom(1.24, 775, 590)]

    # Contact shadow: tight and dark at the base, opening out away from the key.
    o.append(f'<g filter="url(#soft22)">'
             f'<ellipse cx="{cxm + 40}" cy="{bot + 14}" rx="318" ry="30" fill="#6F6A61" opacity="0.52"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft40)">'
             f'<ellipse cx="{cxm + 92}" cy="{bot + 28}" rx="424" ry="44" fill="#7C776D" opacity="0.26"/>'
             f'</g>')

    # Gusset behind the face.
    o.append(f'<path d="{side}" fill="#E6E1D6"/>')
    o.append(f'<path d="{side}" fill="url(#gusset)"/>')
    o.append(f'<g filter="url(#soft12)" opacity="0.4">'
             f'<path d="M{fx1 + gus - 40} {top + 40} C{fx1 + gus - 6} {top + 240} '
             f'{fx1 + gus - 4} {bot - 260} {fx1 + gus - 32} {bot - 110}" '
             f'stroke="#5F594E" stroke-width="22" fill="none"/></g>')

    o.append(f'<clipPath id="cf"><path d="{face}"/></clipPath>')
    o.append(f'<path d="{face}" fill="url(#face)"/>')
    o.append('<g clip-path="url(#cf)">')
    o.append(f'<rect x="{fx0 - 40}" y="{top - 20}" width="{fx1 - fx0 + 80}" '
             f'height="{hgt + 60}" fill="url(#faceV)"/>')
    # Folds: blurred hard, so they read as material and not as drawn lines.
    o.append(f'<g filter="url(#soft12)" opacity="0.42">'
             f'<path d="M{fx0 + 92} {bot - 20} C{fx0 + 146} {bot - 200} {fx0 + 114} {bot - 330} '
             f'{fx0 + 172} {bot - 470}" stroke="#8B8476" stroke-width="15" fill="none"/>'
             f'<path d="M{fx1 - 124} {bot - 16} C{fx1 - 164} {bot - 230} {fx1 - 114} {bot - 350} '
             f'{fx1 - 162} {bot - 520}" stroke="#8B8476" stroke-width="12" fill="none"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft12)" opacity="0.5">'
             f'<path d="M{fx0 + 126} {bot - 30} C{fx0 + 182} {bot - 210} {fx0 + 148} {bot - 340} '
             f'{fx0 + 208} {bot - 480}" stroke="#FFFFFF" stroke-width="13" fill="none"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft22)" opacity="0.45">'
             f'<ellipse cx="{fx0 + 146}" cy="{top + hgt * 0.5}" rx="48" ry="{hgt * 0.4}" '
             f'fill="#FFFFFF"/></g>')
    o.append(f'<g filter="url(#soft12)" opacity="0.5">'
             f'<path d="M{fx0 + 8} {top} V{bot}" stroke="#7A7367" stroke-width="26" fill="none"/>'
             f'<path d="M{fx1 - 8} {top} V{bot}" stroke="#6E6759" stroke-width="30" fill="none"/>'
             f'<path d="M{fx0} {top + 46} H{fx1}" stroke="#7A7367" stroke-width="20" fill="none"/>'
             f'</g>')
    o.append("</g>")

    # ---- print ----------------------------------------------------------
    px = fx0 + 58
    pw = (fx1 - fx0) - 116
    o.append('<g clip-path="url(#cf)">')
    o.append(f'<g transform="translate({px + 4} {top + 176}) scale(1.45)" fill="{INK}">'
             f'<circle cx="0" cy="0" r="3.4"/><circle cx="12" cy="-2" r="5.6"/>'
             f'<circle cx="29.5" cy="-5" r="8.6"/>'
             f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{SAND_DEEP}"/></g>')
    o.append(text(px, top + 228, "Aragonite sand", 32, INK, SANS, "700"))
    o.append(text(px, top + 256, "by AragoCor Minerals", 14.5, TIDE, MONO, "400", spacing="0.06em"))
    o.append(f'<rect x="{px}" y="{top + 274}" width="{pw}" height="2.6" fill="{SAND}"/>')
    o.append(text(px, top + 348, grade["name"], 66, INK, SANS, "700"))
    o.append(text(px, top + 382, f'{grade["grain_mm"]} · {grade["mesh"]} mesh', 20, SURF,
                  MONO, "500"))

    # A window of the grade. The grains are drawn enlarged and say so: at the
    # scale this render sees the bag a 1 mm grain would be about a pixel, and a
    # window nobody can read is worse than one that admits its magnification.
    # The three grades still differ in the window the way they differ in the
    # sieve, which is what the window is for.
    wy, wh = top + 406, 186
    o.append(f'<rect x="{px}" y="{wy}" width="{pw}" height="{wh}" rx="6" fill="#FFFDF8" '
             f'stroke="{INK}" stroke-opacity="0.16" stroke-width="2"/>')
    o.append(f'<clipPath id="cw"><rect x="{px}" y="{wy}" width="{pw}" height="{wh}" rx="6"/></clipPath>')
    o.append('<g clip-path="url(#cw)">')
    o.append(grain_bed(px, wy, pw, wh, grade["grain_min_mm"], grade["grain_max_mm"],
                       26.0, SEEDS[grade["slug"]],
                       {"fine": 620, "medium": 280, "coarse": 96}[grade["slug"]]))
    o.append("</g>")
    o.append(text(px, wy + wh + 28, "Grain shown enlarged", 14.5, TIDE, MONO, "400",
                  spacing="0.05em"))

    o.append(f'<rect x="{px}" y="{top + 646}" width="{pw}" height="2" fill="{INK}" opacity="0.16"/>')
    o.append(text(px, top + 702, "Net 20 lb", 38, INK, SANS, "700"))
    o.append(text(px, top + 730, "9.07 kg", 18, TIDE, MONO, "400"))
    o.append(text(px + pw, top + 684, "Lot", 14, TIDE, MONO, "400", anchor="end", spacing="0.1em"))
    o.append(text(px + pw, top + 714, "AC-2608-" + grade["name"][0] + "01", 18, INK, MONO,
                  "500", anchor="end"))
    # The light falls across the print as well as the film.
    o.append(f'<path d="{face}" fill="url(#face)" style="mix-blend-mode:multiply" opacity="0.46"/>')
    o.append("</g>")

    # ---- sealed top and die-cut handle ----------------------------------
    o.append(f'<path d="M{fx0 + sh} {top + 4} H{fx1 - sh} L{fx1 - sh - 4} {top - 72} '
             f'H{fx0 + sh + 4} Z" fill="url(#seal)"/>')
    o.append(f'<path d="M{fx0 + sh} {top + 4} C{fx0 + sh - 8} {top + 30} {fx0 + sh - 6} {top + 40} '
             f'{fx0 + sh + 4} {top + 52} H{fx1 - sh - 4} C{fx1 - sh + 6} {top + 40} '
             f'{fx1 - sh + 8} {top + 30} {fx1 - sh} {top + 4} Z" fill="url(#seal)"/>')
    for i in range(int((fx1 - fx0 - 2 * sh - 8) / 13)):
        tx = fx0 + sh + 8 + i * 13
        o.append(f'<path d="M{tx} {top - 72} v9" stroke="#FFFFFF" stroke-width="3" opacity="0.28"/>')
    o.append(f'<g filter="url(#soft6)" opacity="0.4">'
             f'<path d="M{fx0 + sh + 26} {top - 58} H{fx1 - sh - 120}" stroke="#FFFFFF" '
             f'stroke-width="9"/></g>')
    hx = cxm
    o.append(f'<rect x="{hx - 92}" y="{top - 50}" width="184" height="28" rx="14" fill="#EFECE5"/>')
    o.append(f'<g filter="url(#soft3)" opacity="0.45">'
             f'<rect x="{hx - 92}" y="{top - 50}" width="184" height="11" rx="5.5" fill="#4A463F"/>'
             f'</g>')

    # Matte grain over the pack.
    o.append(f'<g clip-path="url(#cf)" opacity="0.05" style="mix-blend-mode:multiply">'
             f'<rect x="{fx0 - 40}" y="{top - 20}" width="{fx1 - fx0 + 80}" '
             f'height="{hgt + 60}" filter="url(#filmgrain)"/></g>')

    o.append("</g>")
    o.append("</svg>")
    return "".join(o)



# --------------------------------------------------------------- 50 lb bag

def bag50(grades):
    """The plain woven trade bag: flatter, sewn at both seams, one-colour print."""
    fx0, fx1 = 372, 1228
    top, bot = 332, 924
    cxm = (fx0 + fx1) / 2
    hgt = bot - top

    body = (
        f'M{fx0 + 30} {top + 44} C{fx0 + 210} {top - 14} {fx1 - 210} {top - 14} '
        f'{fx1 - 30} {top + 44} '
        f'C{fx1 + 14} {top + 210} {fx1 + 14} {bot - 210} {fx1 - 30} {bot - 44} '
        f'C{fx1 - 210} {bot + 14} {fx0 + 210} {bot + 14} {fx0 + 30} {bot - 44} '
        f'C{fx0 - 14} {bot - 210} {fx0 - 14} {top + 210} {fx0 + 30} {top + 44} Z'
    )

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">Aragonite, 50 lb woven polypropylene trade bag</title>'
         f'<desc id="d">Studio render of the 50 lb plain woven polypropylene trade bag, '
         f'sewn at both seams, standing on a white sweep. A render of proposed packaging, '
         f'not a photograph of a produced bag.</desc>',
         studio_defs().replace("</defs>", WEAVE + "</defs>"),
         set_dressing(), zoom(1.34, 800, 630)]

    o.append(f'<g filter="url(#soft22)">'
             f'<ellipse cx="{cxm + 34}" cy="{bot + 12}" rx="368" ry="28" fill="#6F6A61" opacity="0.5"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft40)">'
             f'<ellipse cx="{cxm + 86}" cy="{bot + 26}" rx="452" ry="42" fill="#7C776D" opacity="0.24"/>'
             f'</g>')

    o.append(f'<clipPath id="cb"><path d="{body}"/></clipPath>')
    o.append(f'<path d="{body}" fill="url(#face)"/>')
    o.append('<g clip-path="url(#cb)">')
    o.append(f'<rect x="{fx0 - 40}" y="{top - 40}" width="{fx1 - fx0 + 80}" '
             f'height="{hgt + 90}" fill="url(#faceV)"/>')
    # The weave, then the light over it.
    o.append(f'<rect x="{fx0 - 40}" y="{top - 40}" width="{fx1 - fx0 + 80}" '
             f'height="{hgt + 90}" fill="url(#weave)" opacity="0.5"/>')
    # A woven bag creases in long shallow folds running out of the seams.
    o.append(f'<g filter="url(#soft22)" opacity="0.4">'
             f'<path d="M{fx0 + 120} {top + 30} C{fx0 + 190} {top + 240} {fx0 + 150} {bot - 260} '
             f'{fx0 + 220} {bot - 30}" stroke="#8B8476" stroke-width="22" fill="none"/>'
             f'<path d="M{fx1 - 150} {top + 24} C{fx1 - 220} {top + 250} {fx1 - 170} {bot - 250} '
             f'{fx1 - 240} {bot - 26}" stroke="#8B8476" stroke-width="20" fill="none"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft22)" opacity="0.4">'
             f'<ellipse cx="{fx0 + 210}" cy="{top + hgt * 0.5}" rx="70" ry="{hgt * 0.36}" '
             f'fill="#FFFFFF"/></g>')
    o.append(f'<g filter="url(#soft12)" opacity="0.5">'
             f'<path d="M{fx0 + 14} {top} V{bot}" stroke="#7A7367" stroke-width="34" fill="none"/>'
             f'<path d="M{fx1 - 14} {top} V{bot}" stroke="#6E6759" stroke-width="38" fill="none"/>'
             f'<path d="M{fx0} {top + 40} H{fx1}" stroke="#7A7367" stroke-width="30" fill="none"/>'
             f'<path d="M{fx0} {bot - 40} H{fx1}" stroke="#7A7367" stroke-width="30" fill="none"/>'
             f'</g>')
    o.append("</g>")

    # Sewn seams, top and foot.
    o.append('<g clip-path="url(#cb)">')
    for sy, curve in ((top + 40, -16), (bot - 40, 16)):
        o.append(f'<path d="M{fx0 + 30} {sy} C{fx0 + 250} {sy + curve} {fx1 - 250} {sy + curve} '
                 f'{fx1 - 30} {sy}" stroke="#6F6A5E" stroke-width="5" stroke-dasharray="16 13" '
                 f'fill="none" opacity="0.55"/>')
        o.append(f'<path d="M{fx0 + 30} {sy + 4} C{fx0 + 250} {sy + curve + 4} '
                 f'{fx1 - 250} {sy + curve + 4} {fx1 - 30} {sy + 4}" stroke="#FFFFFF" '
                 f'stroke-width="3" stroke-dasharray="16 13" fill="none" opacity="0.4"/>')
    o.append("</g>")

    # ---- print ----------------------------------------------------------
    # Laid out against the bag's own height, so a change to the silhouette
    # cannot push the lot box off the foot seam.
    o.append('<g clip-path="url(#cb)">')
    o.append(f'<g transform="translate({cxm - 34} {top + 150}) scale(1.6)" fill="{INK}">'
             f'<circle cx="0" cy="0" r="3.4"/><circle cx="12" cy="-2" r="5.6"/>'
             f'<circle cx="29.5" cy="-5" r="8.6"/>'
             f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{SAND_DEEP}"/></g>')
    o.append(text(cxm, top + 214, "Aragonite sand", 44, INK, SANS, "700", anchor="middle"))
    o.append(text(cxm, top + 246, "Oolitic aragonite · washed and screened", 18, TIDE, MONO,
                  "400", anchor="middle"))
    o.append(f'<rect x="{cxm - 190}" y="{top + 266}" width="380" height="2.6" fill="{SAND}"/>')
    yy = top + 296
    for i, g in enumerate(grades):
        gx = cxm - 195 + i * 130
        o.append(f'<rect x="{gx}" y="{yy}" width="110" height="46" rx="5" fill="none" '
                 f'stroke="{INK}" stroke-opacity="0.45" stroke-width="2.5"/>')
        o.append(text(gx + 55, yy + 32, g["name"], 21, INK, SANS, "600", anchor="middle"))
    o.append(text(cxm, yy + 76, "Grade marked at packing", 15, TIDE, MONO, "400",
                  anchor="middle", spacing="0.05em"))
    o.append(text(cxm, top + 452, "Net 50 lb", 54, INK, SANS, "700", anchor="middle"))
    o.append(text(cxm, top + 482, "22.7 kg", 19, TIDE, MONO, "400", anchor="middle"))
    o.append(f'<rect x="{cxm - 160}" y="{top + 500}" width="320" height="46" rx="5" fill="none" '
             f'stroke="{INK}" stroke-opacity="0.3" stroke-width="2.5"/>')
    o.append(text(cxm, top + 532, "Lot AC-2608-M01", 23, INK, MONO, "500", anchor="middle"))
    o.append(f'<path d="{body}" fill="url(#face)" style="mix-blend-mode:multiply" opacity="0.36"/>')
    o.append("</g>")

    o.append(f'<g clip-path="url(#cb)" opacity="0.07" style="mix-blend-mode:multiply">'
             f'<rect x="{fx0 - 40}" y="{top - 40}" width="{fx1 - fx0 + 80}" '
             f'height="{hgt + 90}" filter="url(#filmgrain)"/></g>')
    o.append("</g>")
    o.append("</svg>")
    return "".join(o)


# ------------------------------------------------------------------- tote

def tote():
    """The filled FIBC, four loops up, standing on a pallet."""
    bx0, bx1 = 502, 1084
    top, bot = 262, 884
    cxm = (bx0 + bx1) / 2

    body = (
        f'M{bx0 + 34} {top} H{bx1 - 34} C{bx1 + 4} {top + 20} {bx1 + 30} {top + 180} '
        f'{bx1 + 26} {top + 270} C{bx1 + 22} {bot - 130} {bx1 - 2} {bot - 24} {bx1 - 40} {bot} '
        f'H{bx0 + 40} C{bx0 + 2} {bot - 24} {bx0 - 22} {bot - 130} {bx0 - 26} {top + 270} '
        f'C{bx0 - 30} {top + 180} {bx0 - 4} {top + 20} {bx0 + 34} {top} Z'
    )

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
         f'height="{H}" role="img" aria-labelledby="t d">'
         f'<title id="t">Aragonite, 2,000 lb bulk bag on a pallet</title>'
         f'<desc id="d">Studio render of a filled 2,000 lb FIBC bulk bag with four lift '
         f'loops and a discharge spout, standing on a 48 by 40 inch pallet. A render of '
         f'proposed packaging, not a photograph of a produced bag.</desc>',
         studio_defs().replace("</defs>", WEAVE + PALLET + "</defs>"),
         set_dressing(), zoom(1.22, 793, 620)]

    py = bot + 6
    o.append(f'<g filter="url(#soft22)">'
             f'<ellipse cx="{cxm + 30}" cy="{py + 112}" rx="400" ry="26" fill="#6F6A61" opacity="0.45"/>'
             f'</g>')

    # Loops: the back pair first, dimmer and slightly shorter.
    for i, lx in enumerate((bx0 + 78, bx0 + 196, bx1 - 196, bx1 - 78)):
        back = i in (1, 2)
        h = 96 if back else 112
        o.append(f'<path d="M{lx - 26} {top + 18} V{top - h + 26} a26 26 0 0 1 52 0 V{top + 18}" '
                 f'fill="none" stroke="{"#B9BFC0" if back else "#CDD2D2"}" stroke-width="17" '
                 f'stroke-linecap="round"/>')
        o.append(f'<path d="M{lx - 26} {top + 18} V{top - h + 26} a26 26 0 0 1 52 0 V{top + 18}" '
                 f'fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" '
                 f'opacity="0.35" transform="translate(-4 0)"/>')
    # Fill spout.
    o.append(f'<rect x="{cxm - 52}" y="{top - 62}" width="104" height="70" rx="8" '
             f'fill="#E9E5DA" stroke="#9E9788" stroke-width="2"/>')

    o.append(f'<clipPath id="ct"><path d="{body}"/></clipPath>')
    o.append(f'<path d="{body}" fill="url(#face)"/>')
    o.append('<g clip-path="url(#ct)">')
    o.append(f'<rect x="{bx0 - 40}" y="{top - 20}" width="{bx1 - bx0 + 80}" '
             f'height="{bot - top + 60}" fill="url(#faceV)"/>')
    o.append(f'<rect x="{bx0 - 40}" y="{top - 20}" width="{bx1 - bx0 + 80}" '
             f'height="{bot - top + 60}" fill="url(#weave)" opacity="0.45"/>')
    # A filled FIBC pulls into its corner seams and bellies at the belt line.
    for sx in (bx0 + 46, bx1 - 46):
        o.append(f'<g filter="url(#soft12)" opacity="0.45">'
                 f'<path d="M{sx} {top} V{bot}" stroke="#867F72" stroke-width="30" fill="none"/></g>')
    o.append(f'<g filter="url(#soft22)" opacity="0.4">'
             f'<ellipse cx="{bx0 + 190}" cy="{(top + bot) / 2}" rx="74" ry="{(bot - top) * 0.34}" '
             f'fill="#FFFFFF"/></g>')
    o.append(f'<g filter="url(#soft12)" opacity="0.5">'
             f'<path d="M{bx0} {top + 26} H{bx1}" stroke="#7A7367" stroke-width="30" fill="none"/>'
             f'<path d="M{bx0} {bot - 20} H{bx1}" stroke="#6E6759" stroke-width="34" fill="none"/>'
             f'</g>')
    o.append("</g>")

    # Label panel, tucked under the belt line.
    lx, ly, lw, lh = bx0 + 78, top + 150, (bx1 - bx0) - 156, 214
    o.append(f'<g filter="url(#soft6)" opacity="0.3">'
             f'<rect x="{lx + 6}" y="{ly + 8}" width="{lw}" height="{lh}" rx="6" fill="#6B6559"/></g>')
    o.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="6" fill="#FCFAF5" '
             f'stroke="#B5AE9F" stroke-width="2"/>')
    o.append(f'<g transform="translate({lx + 36} {ly + 62}) scale(1.5)" fill="{INK}">'
             f'<circle cx="0" cy="0" r="3.4"/><circle cx="12" cy="-2" r="5.6"/>'
             f'<circle cx="29.5" cy="-5" r="8.6"/>'
             f'<rect x="-7" y="5.5" width="45" height="1.8" rx="0.9" fill="{SAND_DEEP}"/></g>')
    o.append(text(lx + 34, ly + 110, "Aragonite sand", 31, INK, SANS, "700"))
    o.append(text(lx + 34, ly + 138, "Oolitic aragonite · grade at packing", 14.5, TIDE,
                  MONO, "400"))
    o.append(f'<rect x="{lx + 34}" y="{ly + 158}" width="{lw - 68}" height="2.4" fill="{SAND}"/>')
    o.append(text(lx + 34, ly + 202, "Net 2,000 lb", 36, INK, SANS, "700"))
    o.append(text(lx + lw - 34, ly + 202, "907 kg", 19, TIDE, MONO, "400", anchor="end"))
    o.append(f'<path d="{body}" fill="url(#face)" style="mix-blend-mode:multiply" opacity="0.30" '
             f'clip-path="url(#ct)"/>')

    # Discharge spout, then the pallet.
    o.append(f'<path d="M{cxm - 46} {bot - 6} h92 l-12 58 h-68 z" fill="#E2DDD2" '
             f'stroke="#9E9788" stroke-width="2"/>')
    pw = (bx1 - bx0) + 120
    px = cxm - pw / 2
    o.append(f'<g>'
             f'<rect x="{px}" y="{py}" width="{pw}" height="22" rx="2" fill="url(#pallet)"/>'
             f'<rect x="{px + 16}" y="{py + 22}" width="86" height="44" fill="#B08E56"/>'
             f'<rect x="{px + pw / 2 - 43}" y="{py + 22}" width="86" height="44" fill="#BC9A61"/>'
             f'<rect x="{px + pw - 102}" y="{py + 22}" width="86" height="44" fill="#A88650"/>'
             f'<rect x="{px}" y="{py + 66}" width="{pw}" height="18" rx="2" fill="url(#pallet)"/>'
             f'</g>')
    o.append(f'<g filter="url(#soft6)" opacity="0.35">'
             f'<rect x="{px}" y="{py}" width="{pw}" height="10" fill="#5E5850"/></g>')

    o.append(f'<g clip-path="url(#ct)" opacity="0.06" style="mix-blend-mode:multiply">'
             f'<rect x="{bx0 - 40}" y="{top - 20}" width="{bx1 - bx0 + 80}" '
             f'height="{bot - top + 60}" filter="url(#filmgrain)"/></g>')
    o.append("</g>")
    o.append("</svg>")
    return "".join(o)


def main():
    grades = json.loads((ROOT / "data" / "grades.json").read_text())["grades"]
    OUT.mkdir(parents=True, exist_ok=True)
    for g in grades:
        (OUT / f'bag20-{g["slug"]}.svg').write_text(bag20(g), encoding="utf-8")
        print("wrote", f'bag20-{g["slug"]}.svg')
    (OUT / "bag50.svg").write_text(bag50(grades), encoding="utf-8")
    print("wrote bag50.svg")
    (OUT / "tote.svg").write_text(tote(), encoding="utf-8")
    print("wrote tote.svg")


if __name__ == "__main__":
    main()
