#!/usr/bin/env python3
"""Render the site's pages from templates/ and data/.

    python3 tools/build.py

Writes index.html, grade-fine.html, grade-medium.html, grade-coarse.html,
wholesale.html, about.html and 404.html at the repository root. The rendered
HTML is committed, so hosting needs nothing but static files; this script is
an authoring step, run after editing a template or a data file.

Template syntax is deliberately tiny:
  {{> name}}      inserts templates/partials/name.html (recursively rendered)
  {{key}}         inserts context[key], HTML-escaped
  {{key_html}}    inserts context[key_html] verbatim (pre-rendered HTML)
Unknown keys are an error, so a typo cannot ship as literal braces.

Standard library only.
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
PARTIALS = TEMPLATES / "partials"
DATA = ROOT / "data"

class LaunchBlocked(RuntimeError):
    """Raised when status is 'live' and something unverified would reach a visitor."""


TOKEN = re.compile(r"\{\{\s*(>?)\s*([A-Za-z0-9_.-]+)\s*\}\}")


def load_json(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def render(text, ctx, depth=0):
    if depth > 10:
        raise RuntimeError("partial recursion too deep")

    def sub(m):
        is_partial, key = m.group(1), m.group(2)
        if is_partial:
            partial = (PARTIALS / f"{key}.html").read_text(encoding="utf-8")
            return render(partial, ctx, depth + 1)
        if key not in ctx:
            raise KeyError(f"template key not in context: {key}")
        val = ctx[key]
        if key.endswith("_html"):
            return str(val)
        return html.escape(str(val), quote=True)

    return TOKEN.sub(sub, text)


def esc(s):
    return html.escape(str(s), quote=True)


# Bound here because several functions below take a parameter named `html`,
# which shadows the module inside them.
html_unescape = html.unescape


def sieve_rows(sieve):
    out = []
    for row in sieve:
        band, pct = (row["band"], row["pct"]) if isinstance(row, dict) else row
        pct = max(0, min(100, float(pct)))
        pct_s = f"{pct:g}"
        out.append(
            '<div class="bar-row"><span class="bar-row__k">{b}</span>'
            '<span class="bar-track"><span class="bar-fill" style="width:{p}%"></span></span>'
            '<span class="bar-row__v num">{p}%</span></div>'.format(b=esc(band), p=pct_s)
        )
    return "\n        ".join(out)


def uses_blocks(uses):
    out = []
    for i, u in enumerate(uses, 1):
        cls = "feature" + ("" if u["fit"] else " feature--no")
        out.append(
            f'<div class="{cls}">\n'
            f'        <div class="feature__n num">{i:02d}</div>\n'
            f'        <h3>{esc(u["title"])}</h3>\n'
            f'        <p>{esc(u["body"])}</p>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


def other_cards(grades, current):
    out = []
    for g in grades:
        if g["slug"] == current:
            continue
        out.append(
            f'<a class="other" href="{esc(g["page"])}">\n'
            f'        <h3>{esc(g["name"])} grade</h3>\n'
            f'        <div class="other__mm num">{esc(g["grain_mm"])} · {esc(g["mesh"])} mesh · {esc(g["bulk_density_lb_ft3"])} lb/ft³</div>\n'
            f'        <p>{esc(g["other_blurb"])}</p>\n'
            f'      </a>'
        )
    return "\n      ".join(out)


def grade_cards(grades):
    out = []
    for g in grades:
        out.append(
            f'<article class="grade-card grade-card--{esc(g["slug"])}">\n'
            f'        <div class="grade-card__band" aria-hidden="true"></div>\n'
            f'        <div class="grade-card__top">\n'
            f'          <h3><a href="{esc(g["page"])}">{esc(g["name"])}</a></h3>\n'
            f'          <div class="grade-card__mm num">{esc(g["grain_mm"])} · {esc(g["mesh"])} mesh</div>\n'
            f'        </div>\n'
            f'        <div class="grade-card__use">{esc(g["card_use"])}</div>\n'
            f'        <table class="spec" aria-label="{esc(g["name"])} grade typical values">\n'
            f'          <tbody>\n'
            f'            <tr><th scope="row">CaCO₃, representative</th><td class="num">{esc(g["caco3_pct"])}%</td></tr>\n'
            f'            <tr><th scope="row">Bulk density</th><td class="num">{esc(g["bulk_density_lb_ft3"])} lb/ft³</td></tr>\n'
            f'            <tr><th scope="row">Moisture at packaging</th><td class="num">≤ {esc(g["moisture_max_pct"])}%</td></tr>\n'
            f'          </tbody>\n'
            f'        </table>\n'
            f'        <div class="grade-card__foot"><span class="tide-link">{esc(g["name"])} grade in detail <span class="arrow-move"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M5 12h14m-5-6 6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/></svg></span></span></div>\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def home_grains(grades):
    tones = {"fine": "1", "medium": "2", "coarse": "3"}
    out = []
    for g in grades:
        # Three, not five: the card is narrower than the hero plate and a
        # 5 mm grain draws 75px across, so five coarse dots clip on a phone.
        samples = ",".join(str(x) for x in g["grain_samples_mm"][:3])
        out.append(
            f'<div class="grain">\n'
            f'          <div class="grain__dots" data-grains="{samples}" data-tone="{tones.get(g["slug"], "1")}"></div>\n'
            f'          <div class="grain__name"><a href="{esc(g["page"])}">{esc(g["name"])}</a></div>\n'
            f'          <div class="grain__mm num">{esc(g["grain_mm"])}</div>\n'
            f'        </div>'
        )
    return "\n        ".join(out)


def calc_grade_options(grades):
    out = []
    for g in grades:
        sel = ' selected' if g["slug"] == "medium" else ""
        out.append(
            f'<option value="{esc(g["slug"])}" data-density="{esc(g["bulk_density_lb_ft3"])}"{sel}>'
            f'{esc(g["name"])} · {esc(g["grain_mm"])} · {esc(g["bulk_density_lb_ft3"])} lb/ft³</option>'
        )
    return "\n            ".join(out)


# ------------------------------------------------------------------- images

def shot(images, key, caption=None, cls=""):
    """A photograph, the drawing standing in for it, or the slot reserved for it.

    Three states, in order of preference. A photograph wins. Failing that, a
    figure from tools/make-figures.py renders as an image and says on its face
    that it is a drawing, so a distributor is never left guessing whether they
    are looking at the product or at an illustration of it. Failing both, the
    slot holds the exact aspect ratio the photograph will occupy and prints its
    own brief, so the layout does not move when the image lands and the shot
    list is the site rather than a separate document.
    """
    img = images["images"].get(key)
    if img is None:
        raise KeyError(f"no image defined: {key}")
    classes = ("shot " + cls).strip()
    cap = f'<figcaption class="shot__cap">{esc(caption)}</figcaption>' if caption else ""
    if img["file"]:
        # A render is captioned as one. The pack it shows has not been made, so
        # a buyer looking at it is looking at a proposal, and the page says so
        # in the one place they are looking.
        if img.get("source") == "render":
            note = "Packaging render"
            cap = (f'<figcaption class="shot__cap">{esc(caption)} · {note}</figcaption>'
                   if caption else f'<figcaption class="shot__cap">{note}</figcaption>')
        # A cut-out on transparency is fitted, not cropped: cover would slice
        # straight through the pack it is there to show.
        fit = ' shot--contain' if img.get("fit") == "contain" else ""
        return (
            f'<figure class="{classes}{fit}">\n'
            f'        <img src="{esc(img["file"])}" alt="{esc(img["alt"])}" '
            f'style="aspect-ratio:{esc(img["ratio"])}" loading="lazy" decoding="async">\n'
            f'        {cap}\n'
            f'      </figure>'
        )
    if img.get("figure"):
        # The drawing carries its own footer rail, but that rail is unreadable
        # at product-card size, so the caption names the artwork too.
        #
        # It used to read "Drawing; photograph to follow", which describes the
        # photography schedule rather than the picture: on a trade page it
        # reads as a placeholder nobody cleared, and it is the first thing a
        # distributor sees on all three grade cards. `figure_label` in
        # images.json says what the drawing is instead. The launch gate still
        # counts these slots as carrying a drawing, so relabelling them does
        # not hide that real photography is outstanding.
        note = img.get("figure_label") or "Illustration"
        cap = (f'<figcaption class="shot__cap">{esc(caption)} · {note}</figcaption>'
               if caption else f'<figcaption class="shot__cap">{note}</figcaption>')
        return (
            f'<figure class="{classes} shot--figure">\n'
            f'        <img src="{esc(img["figure"])}" alt="{esc(img["figure_alt"])}" '
            f'style="aspect-ratio:{esc(img["ratio"])}" loading="lazy" decoding="async">\n'
            f'        {cap}\n'
            f'      </figure>'
        )
    return (
        f'<figure class="{classes}">\n'
        f'        <div class="shot__slot" style="aspect-ratio:{esc(img["ratio"])}" '
        f'role="img" aria-label="Photograph pending: {esc(img["alt"])}">\n'
        f'          <svg class="shot__icon" width="22" height="22" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.4" aria-hidden="true">'
        f'<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.6"/>'
        f'<path d="m4 17 5-4.5 3.5 3 3-2.5L20 17" stroke-linecap="round" stroke-linejoin="round"/></svg>\n'
        f'          <p class="shot__brief">{esc(img["brief"])}</p>\n'
        f'          <p class="shot__meta">{esc(img["ratio"].replace("/", ":"))} · '
        f'{img["min"]} px long edge · {esc(key)}</p>\n'
        f'        </div>\n'
        f'        {cap}\n'
        f'      </figure>'
    )


# ------------------------------------------------------- links to the parent

def ac_url(links, path_key="contact", interest=None, note=None, content=None, market=None):
    """A deep link into aragocorminerals.com.

    Buying happens there, so every sample, pricing and quote action on this
    site ends up at this URL. The query string is not decoration: the parent's
    lead form reads `interest` to pick the journey, `industry` to preselect the
    select, and `document` as free text it writes into the details field, so
    the visitor arrives at a form that already knows what they want. The utm_*
    trio is captured onto the lead record, which is what makes traffic sent
    from here measurable at the other end.

    `market` is the market on this site the action came from, and it is the
    only thing that sets `industry`. Every link used to send one hard-coded
    industry, left over from when this site sold to aquarium only, so an
    agriculture or feed buyer arrived at the parent's form filed under
    aquarium. An industry is now sent only when the market is known AND its
    option string has been confirmed against the live form: a wrong industry is
    worse than none, because nobody downstream can tell it was wrong.
    """
    from urllib.parse import quote as urlq

    url = links["base"] + links["paths"][path_key]
    q = []
    if interest:
        q.append("interest=" + urlq(links["interest"][interest]))
    ind = links["industry"].get(market) if market else None
    if interest and ind and ind.get("confirmed"):
        q.append("industry=" + urlq(ind["value"]))
    if note:
        q.append("document=" + urlq(note))
    utm = links["utm"]
    q.append("utm_source=" + urlq(utm["source"]))
    q.append("utm_medium=" + urlq(utm["medium"]))
    q.append("utm_campaign=" + urlq(utm["campaign"]))
    if content:
        q.append("utm_content=" + urlq(content))
    return url + ("?" + "&".join(q) if q else "")


EXT_ICON = (
    '<svg class="ext-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
    '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" '
    'stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def ac_note(links):
    """The sentence that says where a link goes, used under outbound buttons."""
    return (
        'Pricing, samples and orders are handled by '
        f'<a class="prose-link" href="{esc(ac_url(links, "home", content="inline"))}">'
        f'{esc(links["parent_name"])}</a>.'
    )


# --------------------------------------------------------------- literature

def literature(lit, links, audience="all"):
    """The document library, grouped.

    A row whose `file` is null is not hidden and not a dead link. It says the
    document is available on request and points at AragoCor's contact form with
    the document named, which is both the honest state and the behaviour a
    trade buyer expects: someone sends it to them.
    """
    out = []
    for group in lit["groups"]:
        rows = [i for i in lit["items"]
                if i["group"] == group["id"]
                and (audience == "all" or i["audience"] == "public")]
        if not rows:
            continue
        cells = []
        for i in rows:
            meta = " · ".join(x for x in [
                i["format"],
                (f'{i["pages"]} page' + ("s" if i["pages"] != 1 else "")) if i.get("pages") else None,
            ] if x)
            if i["file"]:
                action = (f'<a class="lit-dl" href="{esc(i["file"])}">'
                          f'{"Open" if i["format"] == "Web" else "Download"}'
                          f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                          f'stroke-width="1.6" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4M4 21h16" '
                          f'stroke-linecap="round" stroke-linejoin="round"/></svg></a>')
                cls = ""
            else:
                url = ac_url(links, "contact", "technical",
                             f'{i["title"]} — aragonite aquarium sand',
                             f'lit-{i["title"][:40].lower().replace(" ", "-")}')
                action = f'<a class="ext-link" href="{esc(url)}">Request it{EXT_ICON}</a>'
                cls = " lit-row--pending"
            cells.append(
                f'<li class="lit-row{cls}">\n'
                f'          <div class="lit-row__kind">{esc(i["kind"])}</div>\n'
                f'          <div>\n'
                f'            <div class="lit-row__title">{esc(i["title"])}</div>\n'
                f'            <div class="lit-row__note">{esc(i["note"])}</div>\n'
                f'            <div class="lit-row__meta">{esc(meta)}'
                f'{"" if i["file"] else " · available on request"}</div>\n'
                f'          </div>\n'
                f'          <div class="lit-row__action">{action}</div>\n'
                f'        </li>'
            )
        out.append(
            f'<div class="lit-group">\n'
            f'        <div class="lit-group__head">\n'
            f'          <h3>{esc(group["title"])}</h3>\n'
            f'          <p>{esc(group["intro"])}</p>\n'
            f'        </div>\n'
            f'        <ul class="lit-list">\n          ' + "\n          ".join(cells) + '\n        </ul>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


# ---------------------------------------------------------------- commerce
#
# Three grades in four pack formats, sold into five markets. `skus` in
# products.json is the list of combinations actually offered; everything here
# is rendered from it, and per-pallet, per-pound and per-ton figures are
# derived rather than stored so they cannot disagree with the list price.

# Set from data/products.json at the top of build(). "on_request" means no
# figure is published anywhere: not in the tables, not in the cards, and not in
# the data attributes the estimate builder reads, because a price in the DOM is
# a published price whether or not anything draws it.
PRICING_MODE = "published"


def published():
    return PRICING_MODE == "published"


def money(n, cents=True):
    if not published():
        return "On request"
    if cents:
        return "${:,.2f}".format(n)
    return "${:,.0f}".format(n)


def tier_price(list_price, tier):
    return list_price * (1 - tier.get("discount", 0))


def by_id(rows, key="id"):
    return {r[key]: r for r in rows}


def grade_by_slug(grades):
    return {g["slug"]: g for g in grades}


def sku_rows(products, grades):
    """Flatten skus into rows carrying their grade and pack, in catalogue order."""
    gs, ps = grade_by_slug(grades), by_id(products["packs"])
    out = []
    for s in products["skus"]:
        g, pk = gs[s["grade"]], ps[s["pack"]]
        per_lb = s["list"] / pk["lb"]
        out.append({
            "sku": s["sku"], "grade": g, "pack": pk, "list": s["list"],
            "shelf": s.get("suggested_shelf"), "per_lb": per_lb,
            "per_ton": per_lb * 2000,
            "pallet": s["list"] * pk["per_pallet"] if pk["per_pallet"] else None,
            "palletable": bool(pk["per_pallet"]),
        })
    return out


def check_pallets(products, packaging):
    """Derive each pallet net weight, and refuse a build where the two files disagree.

    Bags per pallet times bag weight is arithmetic, so it is derived here
    rather than stored. It used to be stored, as one `pallet_net_lb` in
    packaging.json, which the ordering page then printed in both the retail
    and the trade column: 40 × 50 lb bags were reported as a 1,200 lb pallet.

    packaging.json and products.json each carry the bag weight and the bags
    per pallet, so the same figure exists twice and can drift. Both are
    derived and compared; a mismatch stops the build rather than picking one.

    Returns (retail_pallet_lb, trade_pallet_lb).
    """
    packs = by_id(products["packs"])
    out = []
    for kind, pack_id in (("retail", "bag20"), ("trade", "bag50")):
        bag_lb = packaging[f"{kind}_bag_lb"]
        per_pallet = packaging[f"{kind}_bags_per_pallet"]
        derived = bag_lb * per_pallet
        p = packs.get(pack_id)
        if p is None:
            raise RuntimeError(f"products.json: no pack {pack_id!r} to check the {kind} pallet against")
        if p["lb"] != bag_lb or p["per_pallet"] != per_pallet:
            raise RuntimeError(
                f"packaging.json says the {kind} bag is {bag_lb} lb, {per_pallet} per pallet; "
                f"products.json pack {pack_id} says {p['lb']} lb, {p['per_pallet']} per pallet. "
                f"They describe the same pallet and must agree")
        if p["pallet_lb"] != derived:
            raise RuntimeError(
                f"products.json: pack {pack_id} stores pallet_lb {p['pallet_lb']:,} but "
                f"{per_pallet} × {bag_lb} lb is {derived:,} lb")
        out.append(derived)
    return tuple(out)


def check_prices(products, grades):
    """Refuse to build a price list that is inconsistent or half-filled.

    The price list is the one part of this site a distributor acts on, so a
    typo here is worse than a broken layout. Everything below is checked on
    every build; the `live` block is checked only once the list stops being
    marked as placeholder, so an unfinished list cannot be published by
    flipping one flag.
    """
    status = products.get("price_status")
    if status not in ("placeholder", "indicative", "live"):
        raise RuntimeError(
            f"products.json: price_status is {status!r}, expected 'placeholder', "
            f"'indicative' or 'live'")
    if status == "indicative" and not products.get("price_basis", {}).get("observed"):
        raise RuntimeError(
            "products.json: price_status is 'indicative' but price_basis.observed is "
            "empty. An indicative figure without a recorded source is an invented one")

    packs = by_id(products["packs"])
    slugs = {g["slug"] for g in grades}
    seen = set()

    for s in products["skus"]:
        sku = s["sku"]
        if sku in seen:
            raise RuntimeError(f"products.json: duplicate SKU {sku}")
        seen.add(sku)
        if s["grade"] not in slugs:
            raise RuntimeError(f"products.json: {sku} names grade {s['grade']!r}, which is not in grades.json")
        if s["pack"] not in packs:
            raise RuntimeError(f"products.json: {sku} names pack {s['pack']!r}, which is not in packs")
        if not isinstance(s["list"], (int, float)) or s["list"] <= 0:
            raise RuntimeError(f"products.json: {sku} has list price {s['list']!r}; expected a number above zero")
        shelf = s.get("suggested_shelf")
        if shelf is not None and shelf <= s["list"]:
            raise RuntimeError(
                f"products.json: {sku} has a suggested shelf price of {shelf} at or below its "
                f"trade price of {s['list']}, which leaves the dealer no margin")

    # A larger pack that costs more per pound than a smaller one is a
    # transposed figure, not a pricing strategy. Checked within a grade,
    # since the grades are priced independently.
    order = ["bag20", "bag50", "tote", "bulk"]
    for slug in sorted(slugs):
        rows = [s for s in products["skus"] if s["grade"] == slug]
        rows.sort(key=lambda s: order.index(s["pack"]) if s["pack"] in order else len(order))
        prev = None
        for s in rows:
            per_lb = s["list"] / packs[s["pack"]]["lb"]
            if prev and per_lb > prev[1] + 1e-9:
                raise RuntimeError(
                    f"products.json: {s['sku']} works out at ${per_lb:.4f} per lb, above "
                    f"{prev[0]} at ${prev[1]:.4f} per lb in the same grade. The larger pack "
                    f"must not cost more per pound than the smaller one")
            prev = (s["sku"], per_lb)

    tiers = products["tiers"]
    if not tiers or tiers[0]["min_pallets"] != 1:
        raise RuntimeError("products.json: the first volume tier must start at 1 pallet")
    if tiers[0]["discount"] != 0:
        raise RuntimeError("products.json: the first volume tier is list price and must be at 0 discount")
    for a, b in zip(tiers, tiers[1:]):
        if a["max_pallets"] is None:
            raise RuntimeError(f"products.json: tier {a['id']} is open-ended but is not the last tier")
        if b["min_pallets"] != a["max_pallets"] + 1:
            raise RuntimeError(
                f"products.json: tier {b['id']} starts at {b['min_pallets']} pallets but "
                f"{a['id']} ends at {a['max_pallets']}, which leaves a gap or an overlap")
        if b["discount"] <= a["discount"]:
            raise RuntimeError(
                f"products.json: tier {b['id']} discounts {b['discount']}, which is not more "
                f"than {a['id']} at {a['discount']}")
    if tiers[-1]["max_pallets"] is not None:
        raise RuntimeError("products.json: the last volume tier must be open-ended (max_pallets null)")
    if tiers[-1]["discount"] >= 1:
        raise RuntimeError("products.json: the deepest tier discounts the whole price or more")

    if status != "live":
        return

    # From here down: the list claims to be real, so nothing may be a stub.
    date = str(products.get("effective_date", ""))
    if not re.fullmatch(r"\d{1,2} [A-Z][a-z]+ \d{4}", date):
        raise RuntimeError(
            f"products.json: price_status is 'live' but effective_date is {date!r}; "
            f"expected a real date such as '1 October 2026'")
    for s in products["skus"]:
        for field in ("upc",):
            val = s.get(field)
            if isinstance(val, str) and val.strip().upper().startswith("TODO"):
                raise RuntimeError(
                    f"products.json: price_status is 'live' but {s['sku']} still has "
                    f"{field} set to {val!r}")
    for key in ("price_note", "distributor_note"):
        if "TODO" in str(products.get(key, "")):
            raise RuntimeError(f"products.json: price_status is 'live' but {key} still carries a TODO")


def price_status_banner(products):
    """Shown once per page carrying prices, until the list is AragoCor's own.

    An indicative list is the harder case to word. The numbers are real, in
    that they are worked from published market prices rather than invented,
    and a distributor can size an order against them. They are still not
    AragoCor's list, so the banner has to say so without reading as an excuse.
    """
    if not published():
        return (
            '<p class="notice" role="note"><strong>Pricing on request.</strong> '
            'Trade pricing is issued against a named account and a delivery point, '
            'so it is not published here. Ask and it comes back the same business day.</p>'
        )
    status = products.get("price_status")
    if status == "live":
        return ""
    if status == "indicative":
        return (
            '<p class="notice" role="note"><strong>Indicative pricing.</strong> '
            'The figures below are worked from published market prices for '
            'aragonite, not from an AragoCor price list, and are not quotable. '
            'Current pricing is issued on request.</p>'
        )
    return (
        '<p class="notice" role="note"><strong>Pre-launch price list.</strong> '
        'The figures below are placeholders for layout and are not quotable. '
        'Current pricing is issued on request.</p>'
    )


def price_effective(products):
    """The tail of the price-list table caption.

    A table captioned "effective <date>" is a commitment, so only a live list
    gets one; the other two states say what the figures are instead.
    """
    if not published():
        return "pricing issued on request"
    status = products.get("price_status")
    if status == "live":
        return f'effective {esc(products["effective_date"])}'
    if status == "indicative":
        return "indicative, not quotable"
    return "placeholder figures, not quotable"


# ---------- market cards ----------

def market_cards(markets, products, grades, links):
    gs, ps = grade_by_slug(grades), by_id(products["packs"])
    out = []
    for m in markets["markets"]:
        grade_names = ", ".join(gs[x]["name"] for x in m["grades"])
        pack_names = ", ".join(ps[x]["short"] for x in m["packs"])
        tag = "" if m["status"] == "served" else (
            '<span class="tag tag--quiet">Quoted per application</span>')
        cta = ac_url(links, "contact", "pricing",
                     f'{m["name"]} — aragonite, pricing and availability',
                     f'card-{m["id"]}', market=m["id"])
        out.append(
            f'<article class="market">\n'
            f'        <h3>{esc(m["name"])}</h3>\n'
            f'        <p class="market__summary">{esc(m["summary"])}</p>\n'
            f'        <dl class="market__spec">\n'
            f'          <div><dt>Grades</dt><dd>{esc(grade_names)}</dd></div>\n'
            f'          <div><dt>Formats</dt><dd>{esc(pack_names)}</dd></div>\n'
            f'          <div><dt>Buyers</dt><dd>{esc(m["buyers"])}</dd></div>\n'
            f'        </dl>\n'
            f'        {tag}\n'
            f'        <a class="ext-link market__cta" href="{esc(cta)}">Pricing for {esc(m["name"].lower())}{EXT_ICON}</a>\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def market_sections(markets, products, grades, links, images):
    gs, ps = grade_by_slug(grades), by_id(products["packs"])
    rows = None
    out = []
    for m in markets["markets"]:
        lead = gs[m["lead_grade"]]
        packs = "".join(
            f'<div><dt>{esc(ps[x]["name"])}</dt><dd>{esc(ps[x]["spec"])}</dd></div>'
            for x in m["packs"]
        )
        grade_links = " · ".join(
            f'<a class="prose-link" href="{esc(gs[x]["page"])}">{esc(gs[x]["name"])}</a> '
            f'({esc(gs[x]["grain_mm"])})' for x in m["grades"]
        )
        enquire = ac_url(links, "contact", "pricing",
                         f'{m["name"]} — aragonite, pricing and availability',
                         f'market-{m["id"]}', market=m["id"])
        sample = ac_url(links, "contact", "sample",
                        f'{m["name"]} — aragonite sample',
                        f'market-{m["id"]}-sample', market=m["id"])
        out.append(
            f'<section class="section{" band-paper" if len(out) % 2 else ""}" id="{esc(m["id"])}" '
            f'aria-labelledby="{esc(m["id"])}-title">\n'
            f'  <div class="wrap">\n'
            f'    <div class="split split--wide">\n'
            f'      <div>\n'
            f'        <p class="eyebrow">{esc(m["short"])}</p>\n'
            f'        <h2 class="display-3" id="{esc(m["id"])}-title" style="margin-top:10px">{esc(m["name"])}</h2>\n'
            f'        <p class="copy-2" style="margin-top:14px">{esc(m["function"])}</p>\n'
            f'        <p class="copy-2">Sold to {esc(m["buyers"].lower())}.</p>\n'
            f'        <div class="actions">\n'
            f'          <a class="btn btn-ink btn-sm" href="{esc(enquire)}">Pricing{EXT_ICON}</a>\n'
            f'          <a class="btn btn-inkline btn-sm" href="{esc(sample)}">Sample{EXT_ICON}</a>\n'
            f'        </div>\n'
            f'      </div>\n'
            f'      <div>\n'
            f'      {shot(images, "market-" + m["id"])}\n'
            f'      <dl class="facts" style="margin-top:18px">\n'
            f'        <div class="facts__row"><dt>Grades</dt><dd>{esc(", ".join(gs[x]["name"] for x in m["grades"]))}</dd></div>\n'
            f'        <div class="facts__row"><dt>Most specified</dt><dd>{esc(lead["name"])}, {esc(lead["grain_mm"])}</dd></div>\n'
            f'        <div class="facts__row"><dt>Formats</dt><dd>{esc(", ".join(ps[x]["name"] for x in m["packs"]))}</dd></div>\n'
            f'        <div class="facts__row"><dt>Supply</dt><dd>{"Stock item" if m["status"] == "served" else "Quoted per application"}</dd></div>\n'
            f'      </dl>\n'
            f'      </div>\n'
            f'    </div>\n'
            f'    <p class="note" style="margin-top:22px">Grade pages: {grade_links}</p>\n'
            f'  </div>\n'
            f'</section>'
        )
    return "\n\n".join(out)


# ---------- catalogue ----------

def product_cards(products, grades, links, images):
    """One card per grade, listing the formats that grade ships in."""
    rows = sku_rows(products, grades)
    out = []
    for g in grades:
        mine = [r for r in rows if r["grade"]["slug"] == g["slug"]]
        if not mine:
            continue
        samples = ",".join(str(x) for x in g["grain_samples_mm"][:3])
        tone = {"fine": "1", "medium": "2", "coarse": "3"}.get(g["slug"], "1")
        fmt = []
        for r in mine:
            # The secondary figure is whichever unit the buyer converts to:
            # a pallet total for bagged goods, a per-pound rate for bulk. Never
            # a restatement of the price already in the row.
            # How the buyer receives it, which is a fact in either mode.
            sub = (f'{r["pack"]["per_pallet"]} per pallet'
                   if r["palletable"] and r["pack"]["per_pallet"] > 1
                   else f'{r["pack"]["lb"]:,} lb')
            price = (f'{money(r["list"])}<span class="per"> / {esc(r["pack"]["unit"])}</span>'
                     if published() else '<span class="t-quiet">On request</span>')
            fmt.append(
                f'<tr>\n'
                f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span>'
                f'<span class="fmt__name">{esc(r["pack"]["short"])}</span></th>\n'
                f'            <td class="t-price">{price}</td>\n'
                f'            <td class="t-sub">{esc(sub)}</td>\n'
                f'          </tr>'
            )
        pricing = ac_url(links, "contact", "pricing",
                         f'{g["name"]} grade aragonite, {g["grain_mm"]} — pricing',
                         f'card-{g["slug"]}')
        out.append(
            f'<article class="product product--{esc(g["slug"])}">\n'
            f'        <div class="product__band" aria-hidden="true"></div>\n'
            f'        <div class="product__head">\n'
            f'          <div>\n'
            f'            <h3><a href="{esc(g["page"])}">{esc(g["name"])} grade</a></h3>\n'
            f'            <div class="product__mm num">{esc(g["grain_mm"])} · {esc(g["mesh"])} mesh · '
            f'{esc(g["bulk_density_lb_ft3"])} lb/ft³</div>\n'
            f'          </div>\n'
            f'        </div>\n'
            f'        {shot(images, "product-" + g["slug"] + "-bag20", cls="shot--card")}\n'
            f'        <table class="fmt">\n'
            f'          <tbody>\n          ' + "\n          ".join(fmt) + '\n'
            f'          </tbody>\n'
            f'        </table>\n'
            f'        <div class="product__foot">\n'
            f'          <a class="btn btn-inkline btn-sm" href="{esc(g["page"])}">Technical data</a>\n'
            f'          <a class="ext-link" href="{esc(pricing)}">Pricing{EXT_ICON}</a>\n'
            f'        </div>\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def tier_cells(products):
    """The volume schedule. With published prices each break carries its
    discount; without them it carries only the break point and what it is for,
    because four cards all reading "volume break" say nothing at all."""
    out = []
    for t in products["tiers"]:
        off = ""
        if published():
            label = "List" if not t["discount"] else f'{t["discount"] * 100:.0f}% off'
            off = f'        <div class="tier__off">{esc(label)}</div>\n'
        out.append(
            f'<div class="tier" data-tier="{esc(t["id"])}" data-active="false">\n'
            f'        <div class="tier__label">{esc(t["label"])}</div>\n'
            f'{off}'
            f'        <p class="tier__note">{esc(t["note"])}</p>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


def tier_headers(products):
    return "".join(f'<th scope="col">{esc(t["label"])}</th>' for t in products["tiers"])


QUOTE_BAR = """<div class="quote-bar" id="quote-bar" hidden aria-live="polite" aria-label="Estimate summary">
  <div class="quote-bar__inner">
    <div class="quote-bar__figures">
      <div class="quote-bar__total" data-quote-total>&mdash;</div>
      <div class="quote-bar__meta" data-quote-meta></div>
    </div>
    <div class="quote-bar__actions">
      <button class="quote-bar__clear" type="button" data-quote-clear>Clear</button>
      <a class="quote-bar__alt" data-quote-local href="wholesale.html#inquiry">Send here instead</a>
      <a class="btn btn-bone" data-quote-link {ATTRS} href="{HREF}">Request a firm quote {ICON}</a>
    </div>
  </div>
</div>"""


def estimate_section(products, grades):
    """The pallets-to-total builder. Only ever rendered with published prices;
    an estimate with no prices in it is a form that cannot answer."""
    return (
        '<section class="section" id="estimate" aria-labelledby="est-title" data-quote '
        f'data-tiers=\'{tiers_attr(products)}\'>\n'
        '  <div class="wrap">\n'
        '    <div class="sec-head">\n'
        '      <p class="eyebrow">Order estimate</p>\n'
        '      <h2 class="display-2" id="est-title">Build an estimate</h2>\n'
        '      <p class="lead">Pallet counts to indicative total, with the tier applied. '
        'Bulk is quoted separately.</p>\n'
        '    </div>\n'
        '    <div class="data-wrap table-wrap">\n'
        '      <table class="data">\n'
        '        <caption>Palletised formats</caption>\n'
        '        <thead><tr><th scope="col">Item</th><th scope="col">List</th>'
        '<th scope="col">Per pallet</th><th scope="col">Pallets</th></tr></thead>\n'
        f'        <tbody>\n        {quote_units(products, grades)}\n        </tbody>\n'
        '      </table>\n'
        '    </div>\n'
        '  </div>\n'
        '</section>'
    )


def price_table(products, grades, links, caption, per_pallet_col=False):
    """The trade table, in whichever mode data/products.json is in.

    Published, it is a price per selling unit at each volume tier. On request,
    the same rows carry what is true without a figure — unit weight, pallet
    quantity — and each row offers the two things a buyer wants next: a price
    and a sample. The columns differ between the modes, so the whole table is
    rendered here rather than half here and half in the template.
    """
    rows = sku_rows(products, grades)
    tiers = products["tiers"]
    if published():
        head = ("<th scope=\"col\">SKU</th><th scope=\"col\">Grade</th>"
                "<th scope=\"col\">Format</th>"
                + "".join(f'<th scope="col">{esc(t["label"])}</th>' for t in tiers)
                + "<th scope=\"col\">Per lb</th><th scope=\"col\">Sample</th>")
    else:
        head = ("<th scope=\"col\">SKU</th><th scope=\"col\">Grade</th>"
                "<th scope=\"col\">Format</th><th scope=\"col\">Unit</th>"
                "<th scope=\"col\">Per pallet</th><th scope=\"col\">Price</th>"
                "<th scope=\"col\">Sample</th>")
    body, last = [], None
    for r in rows:
        brk = ' class="is-grade-break"' if last and last != r["grade"]["slug"] else ""
        last = r["grade"]["slug"]
        sample = ac_url(links, "contact", "sample",
                        f'{r["grade"]["name"]} grade aragonite, {r["pack"]["name"]} '
                        f'({r["sku"]}) — sample', f'pricelist-{r["sku"]}')
        if published():
            cells = "".join(
                f'<td class="{"t-price" if i == 0 else ""}">{money(tier_price(r["list"], t))}</td>'
                for i, t in enumerate(tiers)
            ) + f'<td>{money(r["per_lb"])}</td>'
        else:
            pricing = ac_url(links, "contact", "pricing",
                             f'{r["grade"]["name"]} grade aragonite, {r["pack"]["name"]} '
                             f'({r["sku"]}) — trade pricing', f'pricelist-{r["sku"]}')
            pp = (str(r["pack"]["per_pallet"])
                  if r["palletable"] and r["pack"]["per_pallet"] > 1 else "—")
            cells = (f'<td>{r["pack"]["lb"]:,} lb</td><td>{pp}</td>'
                     f'<td class="t-price"><a class="ext-link" href="{esc(pricing)}">'
                     f'Request{EXT_ICON}</a></td>')
        body.append(
            f'<tr{brk}>\n'
            f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span></th>\n'
            f'            <td class="t-left"><a class="prose-link" href="{esc(r["grade"]["page"])}">'
            f'{esc(r["grade"]["name"])}</a> · {esc(r["grade"]["grain_mm"])}</td>\n'
            f'            <td class="t-left">{esc(r["pack"]["name"])}</td>\n'
            f'            {cells}\n'
            f'            <td><a class="ext-link" href="{esc(sample)}">Sample{EXT_ICON}</a></td>\n'
            f'          </tr>'
        )
    return ('<div class="data-wrap table-wrap"><table class="price-list">\n'
            f'        <caption>{esc(caption)}</caption>\n'
            f'        <thead><tr>{head}</tr></thead>\n'
            '        <tbody>\n          ' + "\n          ".join(body) +
            '\n        </tbody>\n      </table></div>')


def price_rows(products, grades, links):
    rows = sku_rows(products, grades)
    tiers = products["tiers"]
    out, last = [], None
    for r in rows:
        brk = ' class="is-grade-break"' if last and last != r["grade"]["slug"] else ""
        last = r["grade"]["slug"]
        cells = "".join(
            f'<td class="{"t-price" if i == 0 else ""}">{money(tier_price(r["list"], t))}</td>'
            for i, t in enumerate(tiers)
        )
        sample = ac_url(links, "contact", "sample",
                        f'{r["grade"]["name"]} grade aragonite, {r["pack"]["name"]} '
                        f'({r["sku"]}) — sample', f'pricelist-{r["sku"]}')
        out.append(
            f'<tr{brk}>\n'
            f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span></th>\n'
            f'            <td class="t-left"><a class="prose-link" href="{esc(r["grade"]["page"])}">'
            f'{esc(r["grade"]["name"])}</a> · {esc(r["grade"]["grain_mm"])}</td>\n'
            f'            <td class="t-left">{esc(r["pack"]["name"])}</td>\n'
            f'            {cells}\n'
            f'            <td>{money(r["per_lb"])}</td>\n'
            f'            <td><a class="ext-link" href="{esc(sample)}">Sample{EXT_ICON}</a></td>\n'
            f'          </tr>'
        )
    return "\n          ".join(out)


def pack_rows(products):
    out = []
    for p in products["packs"]:
        pallet = (f'{p["per_pallet"]} per pallet, {p["pallet_lb"]:,} lb'
                  if p["per_pallet"] else "Bulk load, 24 ton")
        out.append(
            f'<tr>\n'
            f'            <th scope="row">{esc(p["name"])}</th>\n'
            f'            <td>{esc(p["spec"])}</td>\n'
            f'            <td class="val">{esc(pallet)}</td>\n'
            f'          </tr>'
        )
    return "\n          ".join(out)


def gradation_rows(grades_doc):
    """AragoCor's own published screen analysis, read off the printed pack.

    It is the gradation of the unscreened natural grade, not of any of the
    three cuts, so it is shown once here and labelled, rather than restated on
    each grade page where it would read as that grade's own analysis.
    """
    spec = grades_doc["natural_screen_spec"]
    return "\n          ".join(
        f'<tr><th scope="row" class="num">{esc(r["mesh"])}</th>'
        f'<td class="num">{esc(r["retained_pct"])}%</td></tr>'
        for r in spec["rows"])


def spec_rows(grades):
    rows = [
        ("Grain size", "grain_mm"), ("Mesh, U.S. sieve", "mesh"),
        ("Bulk density", None), ("Calcium carbonate, representative", None),
        ("Moisture at packaging", None), ("Primary use", "primary_use"),
    ]
    out = []
    for label, key in rows:
        if key:
            cells = "".join(f'<td class="val">{esc(g[key])}</td>' for g in grades)
        elif label.startswith("Bulk"):
            cells = "".join(f'<td class="val num">{esc(g["bulk_density_lb_ft3"])} lb/ft³</td>' for g in grades)
        elif label.startswith("Calcium"):
            cells = "".join(f'<td class="val num">{esc(g["caco3_pct"])}%</td>' for g in grades)
        else:
            cells = "".join(f'<td class="val num">≤ {esc(g["moisture_max_pct"])}%</td>' for g in grades)
        out.append(f'<tr><th scope="row">{esc(label)}</th>{cells}</tr>')
    return "\n          ".join(out)


# ---------- company furniture ----------

def company_facts(company):
    return "\n        ".join(
        f'<div class="facts__row"><dt>{esc(f["k"])}</dt><dd>{esc(f["v"])}</dd></div>'
        for f in company["facts"]
    )


def compliance_rows(company, links):
    """A credential only reads as one when it is actually held. Anything
    unconfirmed renders as a request, never as a claim."""
    out = []
    for c in company["compliance"]:
        if c["status"] == "held":
            state = '<span class="tag tag--held">Held</span>'
            detail = esc(c["detail"])
        else:
            state = '<span class="tag tag--quiet">On request</span>'
            url = ac_url(links, "contact", "technical",
                         f'{c["name"]} — aragonite, current status',
                         f'compliance-{c["name"][:30].lower().replace(" ", "-")}')
            detail = (f'Not published for these grades. '
                      f'<a class="prose-link" href="{esc(url)}">Ask for the current status</a>.')
        out.append(
            f'<tr>\n'
            f'            <th scope="row">{esc(c["name"])}</th>\n'
            f'            <td>{state}</td>\n'
            f'            <td>{detail}</td>\n'
            f'          </tr>'
        )
    return "\n          ".join(out)


def faq_list(company):
    out = []
    for i, f in enumerate(company["faq"], 1):
        out.append(
            f'<details class="faq"{" open" if i == 1 else ""}>\n'
            f'        <summary>{esc(f["q"])}</summary>\n'
            f'        <p>{esc(f["a"])}</p>\n'
            f'      </details>'
        )
    return "\n      ".join(out)


# ---------- quote builder ----------

def quote_units(products, grades):
    """Pallet-based formats only. Bulk is quoted, not added up on a web page."""
    rows = [r for r in sku_rows(products, grades) if r["palletable"]]
    out = []
    for r in rows:
        unit_per_pallet = r["pack"]["per_pallet"]
        # No figure in the DOM when pricing is on request.
        per_bag = r["list"] if published() else ""
        out.append(
            f'<tr data-sku="{esc(r["sku"])}" data-name="{esc(r["grade"]["name"])} {esc(r["pack"]["short"])}" '
            f'data-per-bag="{per_bag}" data-bags-per-pallet="{unit_per_pallet}" '
            f'data-bag-lb="{r["pack"]["lb"]}">\n'
            f'          <th scope="row"><span class="sku">{esc(r["sku"])}</span> '
            f'{esc(r["grade"]["name"])} · {esc(r["pack"]["name"])}</th>\n'
            f'          <td class="t-price">{money(r["list"])}</td>\n'
            f'          <td>{unit_per_pallet} / pallet</td>\n'
            f'          <td>\n'
            f'            <div class="qty">\n'
            f'              <button type="button" data-qty-down aria-label="One pallet fewer of {esc(r["sku"])}" disabled>&minus;</button>\n'
            f'              <label class="visually-hidden" for="q-{esc(r["sku"])}">Pallets of {esc(r["sku"])}</label>\n'
            f'              <input id="q-{esc(r["sku"])}" type="number" inputmode="numeric" value="0" min="0" max="999" step="1">\n'
            f'              <button type="button" data-qty-up aria-label="One pallet more of {esc(r["sku"])}">+</button>\n'
            f'            </div>\n'
            f'          </td>\n'
            f'        </tr>'
        )
    return "\n        ".join(out)


def tiers_attr(products):
    if not published():
        return "[]"
    data = [{"id": t["id"], "label": t["label"], "min_pallets": t["min_pallets"],
             "max_pallets": t["max_pallets"], "discount": t["discount"]}
            for t in products["tiers"]]
    return json.dumps(data, ensure_ascii=False).replace("'", "&#39;")


def catalogue_attr(products, grades):
    if not published():
        return "{}"
    rows = [r for r in sku_rows(products, grades) if r["palletable"]]
    data = {
        "skus": {r["sku"]: {"name": f'{r["grade"]["name"]} {r["pack"]["short"]}',
                            "perBag": r["list"], "bags": r["pack"]["per_pallet"]}
                 for r in rows},
        "tiers": [{"id": t["id"], "label": t["label"], "min_pallets": t["min_pallets"],
                   "max_pallets": t["max_pallets"], "discount": t["discount"]}
                  for t in products["tiers"]],
    }
    return json.dumps(data, ensure_ascii=False).replace("'", "&#39;")


def sku_block(products, grades, slug, links):
    """The formats one grade ships in, for that grade's own page."""
    rows = [r for r in sku_rows(products, grades) if r["grade"]["slug"] == slug]
    out = []
    for r in rows:
        pricing = ac_url(links, "contact", "pricing",
                         f'{r["grade"]["name"]} grade aragonite, {r["pack"]["name"]} '
                         f'({r["sku"]}) — pricing', f'grade-{slug}-{r["sku"]}')
        extra = []
        if r["palletable"] and r["pack"]["per_pallet"] > 1:
            extra.append(f'{r["pack"]["per_pallet"]} per pallet · {r["pack"]["pallet_lb"]:,} lb')
        # Derived figures only say anything when there is a figure to derive
        # from. "On request per lb · suggested shelf On request, 50% margin"
        # is three fragments of a sentence with its subject removed; the
        # margin is also a real number standing next to a withheld one, which
        # is most of the way to publishing the price it was taken from.
        if published():
            extra.append(f'{money(r["per_lb"])} per lb')
            if r["shelf"]:
                pct = (r["shelf"] - r["list"]) / r["shelf"] * 100
                extra.append(f'suggested shelf {money(r["shelf"])}, {pct:.0f}% margin')
        else:
            extra.append("Trade pricing on request")
        price_cell = (f'{money(r["list"])}<span class="per"> / {esc(r["pack"]["unit"])}</span>'
                      if published() else money(r["list"]))
        out.append(
            f'<tr>\n'
            f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span></th>\n'
            f'            <td class="t-left">{esc(r["pack"]["name"])}<div class="t-sub">{esc(r["pack"]["spec"])}</div></td>\n'
            f'            <td class="t-price">{price_cell}</td>\n'
            f'            <td class="t-left t-sub">{esc(" · ".join(extra))}</td>\n'
            f'            <td><a class="ext-link" href="{esc(pricing)}">Pricing{EXT_ICON}</a></td>\n'
            f'          </tr>'
        )
    return "\n          ".join(out)


def grade_markets(markets, slug, links):
    """Which markets specify this grade, on the grade page."""
    out = []
    for m in markets["markets"]:
        if slug not in m["grades"]:
            continue
        lead = " · most specified" if m["lead_grade"] == slug else ""
        out.append(
            f'<div class="feature">\n'
            f'        <div class="feature__n">{esc(m["short"])}{esc(lead)}</div>\n'
            f'        <h3>{esc(m["name"])}</h3>\n'
            f'        <p>{esc(m["function"])}</p>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


def jsonld_catalogue(products, grades, origin):
    """The catalogue as structured data.

    Structured data is published text: a crawler reads it whether or not a
    visitor can see it. So the price a page withholds must be withheld here
    too, or the site keeps its list private from customers and publishes it
    to Google. On `on_request` no `offers` node is emitted at all — an Offer
    without a price still asserts that the SKU is for sale at some price, and
    an `availability` of InStock asserts stock nobody has confirmed.
    """
    rows = sku_rows(products, grades)
    items = []
    for r in rows:
        item = {
            "@type": "Product",
            "sku": r["sku"],
            "name": f'Aragonite, {r["grade"]["name"]} grade, {r["pack"]["name"]}',
            "description": f'{r["grade"]["grain_mm"]} ({r["grade"]["mesh"]} mesh) oolitic aragonite, '
                           f'{r["pack"]["name"]}. {r["pack"]["spec"]}.',
            "brand": {"@type": "Brand", "name": "AragoCor"},
            "url": f"{origin}/products.html",
        }
        if published():
            item["offers"] = {
                "@type": "Offer",
                "priceCurrency": products["currency"],
                "price": "{:.2f}".format(r["list"]),
                "availability": "https://schema.org/InStock",
                "url": f"{origin}/products.html",
            }
        items.append(item)
    name = ("Aragonite wholesale price list" if published()
            else "Aragonite wholesale trade catalogue")
    return json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                       "name": name,
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": o}
                                           for i, o in enumerate(items)]},
                      ensure_ascii=False).replace("</", "<\\/")


def jsonld_product(g, pack, origin):
    """`pack` is a plain string listing the formats this grade ships in."""
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"AragoCor Aragonite, {g['name']} grade",
        "description": g["description"],
        "brand": {"@type": "Brand", "name": "AragoCor"},
        "manufacturer": {"@type": "Organization", "name": "AragoCor Minerals LLC", "url": "https://www.aragocorminerals.com/"},
        "url": f"{origin}/{g['page']}",
        "material": "Aragonite (calcium carbonate)",
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Grain size", "value": g["grain_mm"]},
            {"@type": "PropertyValue", "name": "Mesh", "value": g["mesh"]},
            {"@type": "PropertyValue", "name": "Bulk density", "value": f"{g['bulk_density_lb_ft3']} lb/ft³"},
            {"@type": "PropertyValue", "name": "Formats", "value": pack},
        ],
    }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


SLUG_RE = re.compile(r"[^a-z0-9]+")


def scrollable_tables(html, page):
    """Make every horizontally scrollable table reachable and named.

    A table wider than a phone scrolls sideways inside `.table-wrap`. That
    scroll is mouse- and touch-only unless the box is focusable, so a keyboard
    user could not reach the right-hand columns of the seven-column catalogue
    at all — and a screen reader reached a scrollable box with no name saying
    what it held.

    So each wrapper gets `tabindex="0"`, `role="group"`, and a name taken from
    the caption the table already carries. Doing it here rather than in the
    templates means a table added later cannot be forgotten: there is no
    wrapper this does not reach.

    `group` rather than `region` on purpose. A region is a landmark, and this
    runs on every table, so it would add thirteen landmarks to the landmark
    menu and bury the four that mean something. It also collided: the pallet
    table's caption and its enclosing section's heading are both "Pallet
    configuration", which is two landmarks with one name. A focusable group
    still announces its name when focus enters it.
    """
    seen = set()

    def fix(m):
        tag, cls = m.group(0), m.group(1)
        if "tabindex" in tag:                 # already done, or hand-set
            return tag
        seg = html[m.end():m.end() + 1200]
        cap = re.search(r"<caption[^>]*>(.*?)</caption>", seg, re.S)
        if not cap:                           # unnamed: focusable, but no bare region
            return tag[:-1] + ' tabindex="0">'
        inner = cap.group(1)
        text = html_unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        cid = re.search(r'<caption[^>]*\sid="([^"]+)"', cap.group(0))
        if cid:
            ref = cid.group(1)
        else:
            base = SLUG_RE.sub("-", text.lower()).strip("-")[:40] or "table"
            ref = f"cap-{base}"
            n = 2
            while ref in seen:
                ref, n = f"cap-{base}-{n}", n + 1
            seen.add(ref)
            fix.captions.append((cap.group(0), ref))
        return (tag[:-1] + f' tabindex="0" role="group" aria-labelledby="{esc(ref)}">')

    fix.captions = []
    out = re.sub(r'<div class="([^"]*\btable-wrap\b[^"]*)"[^>]*>', fix, html)
    for original, ref in fix.captions:
        if ' id="' in original:
            continue
        replaced = original.replace("<caption", f'<caption id="{esc(ref)}"', 1)
        if out.count(original) != 1:
            raise RuntimeError(
                f"{page}: caption {ref!r} is not unique, so it cannot be referenced")
        out = out.replace(original, replaced, 1)
    return out


IMPORT_RE = re.compile(r'@import\s+url\(["\']?([^"\')]+)["\']?\)')


def asset_version(rel, _seen=None):
    """A short content hash for a CSS or JS file, covering what it pulls in.

    Assets are served with a long immutable cache lifetime, which is only safe
    if the URL changes when the bytes do. These filenames are stable
    (`css/site.css`), so the version rides in a query string the HTML carries;
    the HTML itself is always revalidated, so a new hash reaches a visitor on
    their next page load.

    A stylesheet's hash covers its transitive @imports as well as itself, so
    editing css/ds/patterns/data.css changes the version of the styles.css that
    imports it. The imported files keep a short cache lifetime of their own
    (see vercel.json), because they are fetched by the stylesheet rather than
    named in the HTML and so cannot carry a query string.
    """
    seen = _seen if _seen is not None else set()
    path = (ROOT / rel).resolve()
    if path in seen or not path.exists():
        return ""
    seen.add(path)
    data = path.read_bytes()
    h = hashlib.sha256(data)
    if path.suffix == ".css":
        for m in IMPORT_RE.finditer(data.decode("utf-8", "replace")):
            target = (path.parent / m.group(1)).resolve()
            try:
                sub = target.relative_to(ROOT)
            except ValueError:
                continue                      # outside the tree; not ours to hash
            h.update(asset_version(sub, seen).encode())
    return h.hexdigest()[:10]


def jsonld_keys(node):
    """Every key appearing anywhere in a parsed JSON-LD document."""
    keys = set()
    if isinstance(node, dict):
        for k, v in node.items():
            keys.add(k)
            keys |= jsonld_keys(v)
    elif isinstance(node, list):
        for v in node:
            keys |= jsonld_keys(v)
    return keys


# How each page is advertised to a crawler. A page absent from here is absent
# from the sitemap: 404.html is reachable but must never be indexed. Keyed by
# the built filename, so a page that is hidden (site.json `hidden_pages`) or
# renamed cannot linger in the sitemap after it stops being built.
SITEMAP = {
    "index.html":        ("monthly", "1.0"),
    "products.html":     ("weekly",  "1.0"),
    "grade-fine.html":   ("monthly", "0.9"),
    "grade-medium.html": ("monthly", "0.9"),
    "grade-coarse.html": ("monthly", "0.9"),
    "wholesale.html":    ("monthly", "0.9"),
    "markets.html":      ("monthly", "0.8"),
    "dealers.html":      ("monthly", "0.7"),
    "about.html":        ("yearly",  "0.6"),
}


def write_sitemap(origin, written):
    """Write sitemap.xml and robots.txt for the pages this build produced.

    Both used to be hand-maintained with the domain typed into them, so
    changing `canonical_origin` in site.json moved every canonical link and
    left these two pointing at the old host — and the sitemap listed whatever
    set of pages was current when someone last edited it, regardless of what
    the build now writes. Generating them removes both kinds of drift: one
    value decides the origin, and the page list is the build's own output.
    """
    urls = []
    for name in sorted(written, key=lambda n: (-float(SITEMAP.get(n, ("", "0"))[1]), n)):
        if name not in SITEMAP:
            continue                          # 404 and anything not for indexing
        freq, prio = SITEMAP[name]
        loc = f"{origin}/" if name == "index.html" else f"{origin}/{name}"
        urls.append(f"  <url><loc>{esc(loc)}</loc><changefreq>{freq}</changefreq>"
                    f"<priority>{prio}</priority></url>")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {origin}/sitemap.xml\n", encoding="utf-8")
    return len(urls)


def launch_gate(site, pages, products, images, company, lit, packaging):
    """What still stands between this site and being publishable.

    Everything unverified on this site renders with a flag on it, which is the
    right behaviour for a draft and the wrong behaviour for a live trade site:
    a distributor reading "Payment terms: TODO" does not see a note to the
    author, they see a company that does not know its own terms. Worse, a
    placeholder nobody removes reads exactly like a fact.

    So the check runs on the rendered HTML, not on intentions. In `pre-launch`
    it prints the list on every build. In `live` it refuses to build while the
    list is non-empty, and names each item and where it is.

    Returns (blockers, warnings). Blockers are things that are untrue,
    unconfigured or internal. Warnings are things that are honest but
    unfinished, which a site may legitimately launch with.
    """
    blockers, warnings = [], []

    # 1. Author's notes reaching the visitor.
    for name, html in sorted(pages.items()):
        body = re.sub(r"<!--.*?-->", "", html, flags=re.S)   # comments are not shipped text
        for m in set(re.findall(r"TODO[^<\n]{0,70}", body)):
            blockers.append(f'{name}: visible author note "{m.strip()}"')
        n = len(re.findall(r'data-placeholder', body))
        if n:
            blockers.append(f"{name}: {n} placeholder flag(s) rendered to the page")

    # 1b. A reserved photograph slot that reached a visitor.
    #
    # An empty slot renders the brief written for the photographer, the shot
    # spec and the slot's own key: "Screening deck running, wide, from the
    # operator walkway. Plant lit, no faces." then "21:7 · 2800 px long edge ·
    # facility-screening". That is the right thing in a draft — it keeps the
    # shot list in the page rather than in a separate document nobody opens —
    # and it is art direction printed on a trade page in front of a
    # distributor. about.html was carrying one at 1200 × 400.
    #
    # Only a slot that is actually rendered blocks. An entry in images.json
    # that no template uses is a shot still to be taken, which is honest and
    # stays a warning below. Clear this by supplying the photograph or by
    # taking the slot out of the template — not by deleting the brief.
    for name, html in sorted(pages.items()):
        for m in re.finditer(r'<p class="shot__meta">([^<]*)</p>', html):
            key = m.group(1).split("·")[-1].strip() or "unknown"
            blockers.append(
                f"{name}: the reserved slot for {key} is printing its "
                f"photographer's brief to the page")

    # 2. Figures that are not the company's own. A list that is not published
    # at all cannot be wrong, so the check only bites when one is.
    if published():
        if products.get("price_status") != "live":
            blockers.append(
                f'data/products.json: price_status is "{products.get("price_status")}". '
                f'A published price list must be AragoCor\'s own and dated')
    else:
        leaks = []
        for name, html in sorted(pages.items()):
            body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
            for m in set(re.findall(r"\$[0-9][0-9,.]*|[0-9]{1,2}% off", body)):
                leaks.append(f"{name}: {m}")
        # A currency sign is how a price looks to a reader, not how it looks to
        # a crawler. Structured data carries the figure bare — "price": "14.00"
        # — so the check above passed an eleven-SKU price list straight into
        # products.html for anything that reads JSON-LD. Check the machine-
        # readable copy on its own terms: the offer keys that assert a price or
        # stock at all, and then the actual list figures, in any notation.
        for name, html in sorted(pages.items()):
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                                    html, re.S):
                try:
                    doc = json.loads(block)
                except ValueError:
                    blockers.append(f"{name}: a JSON-LD block is not valid JSON")
                    continue
                for key in sorted(jsonld_keys(doc) & {
                        "offers", "price", "lowPrice", "highPrice",
                        "priceSpecification", "availability"}):
                    leaks.append(f"{name}: JSON-LD {key}")
        # Only the two-decimal notations. A whole-dollar rendering of 13.50 is
        # "14", which matches "20 lb bag" and every mesh number on the page;
        # and whole-dollar figures only ever render behind a "$", which the
        # check above already catches.
        figures = set()
        for sku in products["skus"]:
            for n in (sku.get("list"), sku.get("suggested_shelf")):
                if n is None:
                    continue
                figures.update({"{:.2f}".format(n), "{:,.2f}".format(n)})
        for name, html in sorted(pages.items()):
            body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
            for f in figures:
                if re.search(rf"(?<![0-9.,]){re.escape(f)}(?![0-9])", body):
                    leaks.append(f"{name}: list figure {f}")
        if leaks:
            blockers.append(
                "pricing_mode is on_request but a figure still reaches the page: "
                + ", ".join(sorted(set(leaks))[:8]))

    # 2b. Links that land nowhere.
    #
    # Four shipped: products.html#tiers from the footer of every page,
    # index.html#grades, index.html#lot and index.html#quality. A fragment is
    # the one kind of broken link a browser hides — it silently scrolls
    # nowhere instead of showing a 404 — so nothing catches it by hand. Both
    # halves are checked here against the rendered pages and the files on
    # disk, which is where the truth is.
    ids = {n: set(re.findall(r'\sid="([^"]+)"', h)) for n, h in pages.items()}
    dead = []
    for name, html in sorted(pages.items()):
        body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
        for href in sorted(set(re.findall(r'href="([^"]+)"', body))):
            if re.match(r"(?:[a-z][a-z0-9+.-]*:|//|#$)", href):
                continue                      # external, mailto/tel, or bare "#"
            target, _, frag = href.partition("#")
            target = target.partition("?")[0]     # drop the ?v= asset version
            if target and target not in pages and not (ROOT / target).exists():
                dead.append(f"{name}: {href} (no such file)")
                continue
            page = target or name
            if frag and page in ids and frag not in ids[page]:
                dead.append(f"{name}: {href} (no #{frag} on {page})")
    if dead:
        blockers.append("link lands nowhere: " + ", ".join(dead[:8])
                        + (f" … and {len(dead) - 8} more" if len(dead) > 8 else ""))

    # 3. Demonstration data presented as a record.
    lookup = [n for n, h in sorted(pages.items())
              if 'id="lot-panel"' in h or "Demonstration records" in h]
    if lookup:
        blockers.append(
            f"{', '.join(lookup)}: a lot lookup is serving demonstration records. "
            f"Connect it to real signed analyses or take it off the page")
    demo = [n for n, h in sorted(pages.items()) if "Demo lot" in h]
    if demo:
        blockers.append(
            f"{', '.join(demo)}: a figure is attributed to a demonstration lot. "
            f"Cite a real lot or drop the attribution")

    # 4. A form that does not go anywhere.
    for name, html in sorted(pages.items()):
        for m in re.finditer(r"<form\b[^>]*>", html):
            tag = m.group(0)
            if "data-endpoint" in tag and 'data-endpoint=""' not in tag:
                continue                      # posts to a configured endpoint
            if "data-mailto=" in tag:
                warnings.append(
                    f"{name}: the inquiry form composes an email rather than posting to an "
                    f"endpoint. Nothing is captured server-side; set data-endpoint to change that")
                continue
            blockers.append(
                f"{name}: an inquiry form neither posts to an endpoint nor falls back to "
                f"email, so anything typed into it is lost")

    # 5. Packaging that has not been produced.
    renders = [k for k, v in images["images"].items() if v.get("source") == "render"]
    if renders:
        blockers.append(
            f"data/images.json: {len(renders)} slot(s) show a render of packaging that "
            f"has not been printed ({', '.join(sorted(renders)[:3])}…)")

    # ---- warnings: honest, but unfinished -------------------------------
    figs = [k for k, v in images["images"].items() if v.get("figure") and not v.get("file")]
    empty = [k for k, v in images["images"].items() if not v.get("file") and not v.get("figure")]
    if figs:
        warnings.append(f"{len(figs)} image slot(s) carry a drawing instead of a photograph")
    if empty:
        warnings.append(f"{len(empty)} image slot(s) are still an empty brief: "
                        f"{', '.join(sorted(empty))}")
    missing_lit = [i["title"] for i in lit["items"] if not i.get("file")]
    if missing_lit:
        warnings.append(f"{len(missing_lit)} literature item(s) do not exist yet and render "
                        f"as available on request")
    unconf = [c["name"] for c in company["compliance"] if c["status"] != "held"]
    if unconf:
        warnings.append(f"{len(unconf)} compliance item(s) unconfirmed: {', '.join(unconf)}")
    # A claim can be held and still be stated wrongly. `verify` carries what a
    # person has to check against the certifying body before the claim is
    # published — a registration number, a scope, a permitted use of a mark.
    # It is a warning rather than a blocker because the claim is real; what is
    # unverified is how this site describes it. Clearing the note is a human
    # signing off, so it appears on every build until someone does.
    for c in company["compliance"]:
        if c.get("verify"):
            warnings.append(f'{c["name"]}: needs sign-off before launch — {c["verify"]}')
    return blockers, warnings


def build():
    grades_doc = load_json("grades.json")
    pack = load_json("packaging.json")
    products = load_json("products.json")
    links = load_json("links.json")
    lit = load_json("literature.json")
    markets = load_json("markets.json")
    images = load_json("images.json")
    company = load_json("company.json")
    site = load_json("site.json")

    global PRICING_MODE
    PRICING_MODE = products.get("pricing_mode", "published")
    grades = grades_doc["grades"]
    check_prices(products, grades)
    retail_pallet_lb, trade_pallet_lb = check_pallets(products, pack)
    inquiry_endpoint = pack.get("dealer_inquiry_endpoint") or ""
    tones = {"fine": "1", "medium": "2", "coarse": "3"}

    common = {
        # One place decides the published origin. It is written into every
        # canonical link, every og:url and the sitemap, so a site served from a
        # different domain than it declares - which keeps it out of the index -
        # is a one-line fix rather than a search and replace.
        "origin": site["canonical_origin"].rstrip("/"),
        # Cache-busting versions for the assets the HTML names. See
        # asset_version() and the Cache-Control rules in vercel.json.
        "v_css_ds": asset_version("css/ds/styles.css"),
        "v_css_tokens": asset_version("css/tokens.css"),
        "v_css_site": asset_version("css/site.css"),
        "v_js_site": asset_version("js/site.js"),
        "retail_bag_lb": pack["retail_bag_lb"],
        "trade_bag_lb": pack["trade_bag_lb"],
        "retail_bags_per_pallet": pack["retail_bags_per_pallet"],
        "trade_bags_per_pallet": pack["trade_bags_per_pallet"],
        # Derived, not stored, and derived once per format. A single stored
        # figure reported the 50 lb trade pallet at the 20 lb retail pallet's
        # 1,200 lb; 40 × 50 lb is 2,000 lb. check_pallets() below holds these
        # against products.json, which carries the same weights a second time.
        "retail_pallet_net_lb": f"{retail_pallet_lb:,}",
        "trade_pallet_net_lb": f"{trade_pallet_lb:,}",
        "pallet_net_summary": (f"{retail_pallet_lb:,} lb for {pack['retail_bag_lb']} lb bags, "
                               f"{trade_pallet_lb:,} lb for {pack['trade_bag_lb']} lb bags"),
        "pallet_footprint": pack["pallet_footprint"],
        "dealer_email": pack["dealer_contact_email"],
        # The form's no-JavaScript fallback. Posting to "#" reloaded the page
        # and lost everything typed; a mailto action at least hands the visitor
        # their own words back.
        "dealer_mailto_action": "mailto:" + pack["dealer_contact_email"],
        "inquiry_endpoint_attr_html": (f' data-endpoint="{esc(inquiry_endpoint)}"'
                                       if inquiry_endpoint else ""),
        "dealer_phone": pack["dealer_contact_phone"],
        "dealer_phone_href": "+" + re.sub(r"\D", "", pack["dealer_contact_phone"]),
        "opening_minimum": pack["opening_order"]["minimum"],
        "opening_mixed": pack["opening_order"]["mixed_pallet"],
        "opening_terms": pack["opening_order"]["terms"],
        "opening_lead_time": pack["opening_order"]["lead_time"],
        "opening_ships_from": pack["opening_order"]["ships_from"],
        "opening_freight": pack["opening_order"]["freight"],
        # commerce
        "currency": products["currency"],
        "effective_date": products["effective_date"],
        "price_effective": price_effective(products),
        "distributor_note": products["distributor_note"],
        "price_banner_html": price_status_banner(products),
        "tiers_json_html": tiers_attr(products),
        "catalogue_json_html": catalogue_attr(products, grades),
        "product_cards_html": product_cards(products, grades, links, images),
        "gradation_rows_html": gradation_rows(grades_doc),
        "tier_cells_html": tier_cells(products),
        "price_table_html": price_table(
            products, grades, links,
            f'Trade catalogue · {products["currency"]} · FOB Stockton, California · '
            f'{price_effective(products)}'),
        "estimate_section_html": estimate_section(products, grades) if published() else "",
        "quote_bar_html": "",
        "tier_headers_html": tier_headers(products),
        "price_rows_html": price_rows(products, grades, links),
        "spec_rows_html": spec_rows(grades),
        "tier2_label": products["tiers"][1]["label"],
        # Only meaningful with published prices; kept so a published build
        # can still use it, blank otherwise so it cannot leak a schedule.
        "price_heading": "Price list" if published() else "Trade catalogue",
        "price_lead": ("Per selling unit at each volume tier. Tiers count total pallets on the order."
                       if published()
                       else "Every SKU with its pack and pallet quantity. Trade pricing is issued on request, against a named account and a delivery point."),
        "price_note": (products["price_note"] if published()
                       else "Volume breaks apply across grades and formats on one order. Bulk is quoted by the ton on a 24 ton load."),
        # Every visible string that promises a published figure. A page that
        # says "price list" while every cell reads "On request" reads as a
        # list the visitor was refused, so the wording follows the mode
        # rather than the intention. One place decides it for all seven pages.
        "catalogue_nav": "Products and price list" if published() else "Products and trade catalogue",
        "catalogue_cta": "Price list" if published() else "Trade catalogue",
        "catalogue_h1": "Products and price list" if published() else "Products and trade catalogue",
        "catalogue_lead": (
            "List price per selling unit, FOB Stockton, California, before freight. "
            "Volume tiers apply across grades and formats on one order."
            if published() else
            "Every grade and pack format we ship, FOB Stockton, California. "
            "Volume breaks apply across grades and formats on one order; "
            "trade pricing is issued on request."),
        # The quote builder is only built with published prices (see
        # estimate_section above), so the markup that feeds it and the copy
        # that promises it follow the same switch. Left in, they advertised a
        # builder that is not on the products page.
        "quote_context_html": (
            f"""        <div class="quote-context" id="quote-context" data-catalogue='{catalogue_attr(products, grades)}' hidden></div>\n"""
            if published() else ""),
        "quote_field_html": (
            '              <div class="field field--full" hidden><label for="df-quote">Quote you built</label>'
            '<input class="fld" id="df-quote" name="quote" type="text" readonly></div>\n'
            if published() else ""),
        "inquiry_form_note": (
            "The form on the right reaches the same people and carries a quote built on the products page."
            if published() else
            "The form on the right reaches the same people."),
        # It composes a message in the visitor's mail client; it does not send
        # one. "Send inquiry" over a mailto: handoff is a promise the page
        # cannot keep. With an endpoint configured it really does send.
        "inquiry_submit_label": "Send inquiry" if inquiry_endpoint else "Compose email",
        "catalogue_table_caption": "Formats and list pricing" if published() else "Formats and pack specifications",
        "catalogue_tier_link": "Full price list, every tier" if published() else "Full catalogue, every pack",
        "catalogue_tier_link_short": "Every tier, in full" if published() else "Every pack and tier, in full",
        "grade_price_lead": (
            f'List price per selling unit, FOB Stockton, before freight. '
            f'Volume tiers start at {products["tiers"][1]["label"]}.'
            if published() else
            f'Pack formats and pallet quantities, FOB Stockton, before freight. '
            f'Trade pricing on request; volume breaks start at {products["tiers"][1]["label"]}.'),
        "tier2_pct": ("{:.0f}".format(products["tiers"][1]["discount"] * 100)
                      if published() else ""),
        "truckload_pallets": products["truckload_pallets"],
        # outbound to the parent, where buying actually happens
        "ac_name": links["parent_name"],
        "ac_host": links["parent_host"],
        "ac_home": ac_url(links, "home", content="body"),
        "ac_contact": ac_url(links, "contact", content="body"),
        "ac_sample": ac_url(links, "contact", "sample",
                            "Aragonite sand sample, all three grades",
                            "sample"),
        "ac_pricing": ac_url(links, "contact", "pricing",
                             "Aragonite sand, trade pricing",
                             "pricing"),
        "ac_distribution": ac_url(links, "contact", "distribution",
                                  "Aragonite sand, distributor schedule",
                                  "distribution"),
        "ac_technical": ac_url(links, "contact", "technical",
                               "Aragonite sand, technical data package",
                               "technical"),
        # Content links carry the utm_* trio too, so the referral shows up in
        # their analytics whether the visitor converts on arrival or wanders.
        "ac_tds": ac_url(links, "technical_data_sheet", content="tds"),
        "ac_products": ac_url(links, "products", content="products"),
        "ac_industries": ac_url(links, "industries", content="industries"),
        "ac_resources": ac_url(links, "resources", content="resources"),
        "ac_about": ac_url(links, "about", content="about"),
        "ac_quote_base": links["base"] + links["paths"]["contact"],
        "ac_quote_attrs_html": (
            'data-ac-contact="' + esc(links["base"] + links["paths"]["contact"]) + '" '
            'data-ac-interest="' + esc(links["interest"]["pricing"]) + '" '
            # No industry: an estimate is a basket across grades and markets,
            # so there is no one industry it belongs to. Sending a guess would
            # file the lead under the wrong desk.

            'data-ac-utm="' + esc("{source}|{medium}|{campaign}".format(**links["utm"])) + '"'
        ),
        "ext_icon_html": EXT_ICON,
        "ac_note_html": ac_note(links),
        "literature_html": literature(lit, links, "all"),
        "literature_public_html": literature(lit, links, "public"),
        # markets, packs and company furniture
        "market_cards_html": market_cards(markets, products, grades, links),
        "shot_family_html": shot(images, "product-family", cls="shot--hero"),
        "shot_facility_html": shot(images, "facility-screening",
                                   "Screening deck, Stockton, California"),
        "shot_packing_html": shot(images, "facility-packing", "Bagging line"),
        "shot_shelf_html": shot(images, "shelf-set", "Three grades faced"),
        "shot_bag50_html": shot(images, "pack-bag50", "50 lb trade bag"),
        "shot_tote_html": shot(images, "pack-tote", "2,000 lb bulk bag"),
        "shot_bulk_html": shot(images, "pack-bulk", "Bulk load"),
        "market_sections_html": market_sections(markets, products, grades, links, images),
        "pack_rows_html": pack_rows(products),
        "quote_units_html": quote_units(products, grades),
        "company_facts_html": company_facts(company),
        "compliance_rows_html": compliance_rows(company, links),
        "faq_html": faq_list(company),
        "hours": company["hours"],
        "facility": company["facility"],
        "market_count": len(markets["markets"]),
        "sku_count": len(products["skus"]),
        "pack_count": len(products["packs"]),
        "market_list": ", ".join(m["short"].lower() for m in markets["markets"]),
    }
    _rows = sku_rows(products, grades)
    for r in _rows:
        common[f'{r["sku"].lower().replace("-", "_")}_price'] = money(r["list"])
    if published():
        common["quote_bar_html"] = (QUOTE_BAR
                                    .replace("{ATTRS}", common["ac_quote_attrs_html"])
                                    .replace("{HREF}", esc(common["ac_pricing"]))
                                    .replace("{ICON}", EXT_ICON))
    # "On request per lb · On request per ton" is a row that costs a line and
    # says nothing; with a real list it is the cheapest useful fact on the page.
    common["products_pricing_row_html"] = (
        '        <div class="facts__row"><dt>From</dt><dd>{} per lb · {} per ton</dd></div>\n'.format(
            money(min(r["per_lb"] for r in _rows)),
            money(min(r["per_ton"] for r in _rows), cents=False))
        if published() else
        '        <div class="facts__row"><dt>Pricing</dt><dd>On request, per selling unit</dd></div>\n')
    common["from_per_lb"] = money(min(r["per_lb"] for r in _rows))
    common["from_per_ton"] = money(min(r["per_ton"] for r in _rows), cents=False)
    common["from_per_bag"] = money(min(r["list"] for r in _rows if r["pack"]["unit"] == "bag"))

    written = []
    rendered = {}

    # Grade pages: one template, three instances.
    tpl = (TEMPLATES / "grade.html").read_text(encoding="utf-8")
    for g in grades:
        ctx = dict(common)
        ctx.update(g)
        ctx["canonical"] = g["page"]
        ctx["name_lower"] = g["name"].lower()
        ctx["tone"] = tones.get(g["slug"], "1")
        ctx["grain_samples"] = ",".join(str(x) for x in g["grain_samples_mm"])
        ctx["uses_html"] = uses_blocks(g["uses"])
        ctx["others_html"] = other_cards(grades, g["slug"])
        ctx["jsonld_html"] = jsonld_product(
            g, ", ".join(r["pack"]["name"] for r in sku_rows(products, grades)
                         if r["grade"]["slug"] == g["slug"]),
            common["origin"])
        ctx["sku_block_html"] = sku_block(products, grades, g["slug"], links)
        ctx["grade_markets_html"] = grade_markets(markets, g["slug"], links)
        ctx["shot_grain_html"] = shot(images, "grain-" + g["slug"],
                                      f'{g["name"]} grade, {g["grain_mm"]}')
        ctx["shot_bag_html"] = shot(images, "product-" + g["slug"] + "-bag20",
                                    f'{g["name"]} grade, 20 lb retail bag')
        ctx["ac_grade_sample"] = ac_url(
            links, "contact", "sample",
            f'{g["name"]} grade aragonite aquarium sand, {g["grain_mm"]}, sample',
            f'sample-{g["slug"]}')
        ctx["ac_grade_pricing"] = ac_url(
            links, "contact", "pricing",
            f'{g["name"]} grade aragonite aquarium sand, {g["grain_mm"]}, pricing by the pallet',
            f'pricing-{g["slug"]}')
        _mine = [r for r in sku_rows(products, grades) if r["grade"]["slug"] == g["slug"]]
        ctx["grade_from_price"] = money(min(r["per_lb"] for r in _mine))
        ctx["grade_price_line_html"] = (
            f'<p class="price" style="margin-top:20px">{ctx["grade_from_price"]}'
            f'<small> per lb, from</small></p>'
            if published() else
            '<p class="price" style="margin-top:20px">Trade pricing'
            '<small> on request</small></p>')
        out = ROOT / g["page"]
        html = scrollable_tables(render(tpl, ctx), out.name)
        out.write_text(html, encoding="utf-8")
        rendered[out.name] = html
        written.append(out.name)

    # Other pages carry their own title/description in a leading JSON front
    # matter comment so the data stays with the page.
    hidden = set(site.get("hidden_pages", []))
    for name in ("index", "markets", "products", "wholesale", "dealers", "about", "404"):
        if name in hidden:
            continue
        src = (TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*meta\s*(\{.*?\})\s*-->\s*", src, re.S)
        if not m:
            raise RuntimeError(f"templates/{name}.html is missing its <!-- meta {{...}} --> header")
        meta = json.loads(m.group(1))
        body = src[m.end():]
        ctx = dict(common)
        ctx.update(meta)
        # A page whose title or description promises a published price needs a
        # second wording for the mode that publishes none. Both live in the
        # page's own front matter, next to each other, so the pair cannot
        # drift: `title_on_request` wins whenever prices are withheld.
        if not published():
            for key in ("title", "description"):
                if f"{key}_on_request" in meta:
                    ctx[key] = meta[f"{key}_on_request"]
        ctx.setdefault("canonical", "" if name == "index" else f"{name}.html")
        ctx["jsonld_html"] = jsonld_catalogue(products, grades, common["origin"])
        ctx["grade_cards_html"] = grade_cards(grades)
        ctx["home_grains_html"] = home_grains(grades)
        ctx["calc_grade_options_html"] = calc_grade_options(grades)
        ctx["medium_density"] = next(g["bulk_density_lb_ft3"] for g in grades if g["slug"] == "medium")
        for g in grades:
            for k in ("grain_mm", "mesh", "bulk_density_lb_ft3", "caco3_pct", "primary_use", "page", "name"):
                ctx[f"{g['slug']}_{k}"] = g[k]
        out = ROOT / f"{name}.html"
        html = scrollable_tables(render(body, ctx), out.name)
        out.write_text(html, encoding="utf-8")
        rendered[out.name] = html
        written.append(out.name)

    n_urls = write_sitemap(common["origin"], written)
    written.append(f"sitemap.xml ({n_urls} urls)")
    written.append("robots.txt")

    blockers, warnings = launch_gate(site, rendered, products, images, company, lit, pack)
    if site["status"] == "live" and blockers:
        raise LaunchBlocked(blockers)
    return written, blockers, warnings, site["status"]


if __name__ == "__main__":
    try:
        names, blockers, warnings, status = build()
        for name in names:
            print("wrote", name)
    except LaunchBlocked as e:
        print("\nBUILD REFUSED. status is 'live' and this would reach a visitor:\n",
              file=sys.stderr)
        for b in e.args[0]:
            print("  x " + b, file=sys.stderr)
        print("\nResolve these, or set status back to 'pre-launch' in data/site.json.",
              file=sys.stderr)
        sys.exit(1)
    except (KeyError, RuntimeError) as e:
        print("build failed:", e, file=sys.stderr)
        sys.exit(1)

    print(f"\nstatus: {status}")
    if blockers:
        print(f"{len(blockers)} launch blocker(s) — the build will refuse these when "
              f"status is 'live':")
        for b in blockers:
            print("  x " + b)
    if warnings:
        print(f"{len(warnings)} open item(s), not blocking:")
        for w in warnings:
            print("  - " + w)
    if not blockers:
        print("no launch blockers. data/site.json may be set to 'live'.")
