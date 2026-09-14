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
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
PARTIALS = TEMPLATES / "partials"
DATA = ROOT / "data"

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
            f'            <tr><th scope="row">CaCO₃, typical</th><td class="num">{esc(g["caco3_pct"])}%</td></tr>\n'
            f'            <tr><th scope="row">Bulk density</th><td class="num">{esc(g["bulk_density_lb_ft3"])} lb/ft³</td></tr>\n'
            f'            <tr><th scope="row">Moisture at packaging</th><td class="num">≤ {esc(g["moisture_max_pct"])}%</td></tr>\n'
            f'            <tr><th scope="row">Fines below 0.25 mm</th><td class="num">≤ {esc(g["fines_max_pct"])}%</td></tr>\n'
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


# ------------------------------------------------------- links to the parent

def ac_url(links, path_key="contact", interest=None, note=None, content=None, industry=True):
    """A deep link into aragocorminerals.com.

    Buying happens there, so every sample, pricing and quote action on this
    site ends up at this URL. The query string is not decoration: the parent's
    lead form reads `interest` to pick the journey, `industry` to preselect the
    select, and `document` as free text it writes into the details field, so
    the visitor arrives at a form that already knows what they want. The utm_*
    trio is captured onto the lead record, which is what makes traffic sent
    from here measurable at the other end.
    """
    from urllib.parse import quote as urlq

    url = links["base"] + links["paths"][path_key]
    q = []
    if interest:
        q.append("interest=" + urlq(links["interest"][interest]))
    if interest and industry:
        q.append("industry=" + urlq(links["industry"]))
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
        'Samples, pricing and orders are handled by '
        f'<a class="prose-link" href="{esc(ac_url(links, "home", content="inline"))}">'
        f'{esc(links["parent_name"])}</a>, the company that makes this sand.'
    )


# ---------------------------------------------------------------- commerce

def money(n, cents=True):
    """Format a USD figure. Prices carry cents; pallet totals usually do not."""
    if cents:
        return "${:,.2f}".format(n)
    return "${:,.0f}".format(n)


def tier_price(list_per_bag, tier):
    return list_per_bag * (1 - tier.get("discount", 0))


def price_status_banner(products):
    """The amber banner that sits over every price while they are invented."""
    if products.get("price_status") == "live":
        return ""
    return (
        '<div class="price-banner" role="note">\n'
        '      <span class="placeholder-flag" data-placeholder>Placeholder</span>\n'
        '      <p><strong>These prices are not real.</strong> Every figure on this page is invented so the '
        'price list, the volume breaks and the quote builder can be seen working. Replace them in '
        '<code>data/products.json</code>, set <code>price_status</code> to <code>live</code>, and this banner '
        'disappears on the next build.</p>\n'
        '    </div>'
    )


def grade_by_slug(grades):
    return {g["slug"]: g for g in grades}


def product_cards(products, grades, links):
    by_slug = grade_by_slug(grades)
    tiers = products["tiers"]
    best = tiers[-1]
    out = []
    for s in products["skus"]:
        g = by_slug[s["grade"]]
        pallet = s["list_per_bag"] * s["bags_per_pallet"]
        per_lb = s["list_per_bag"] / s["bag_lb"]
        best_bag = tier_price(s["list_per_bag"], best)
        # Three, not five: the card is narrower than the hero plate and a
        # 5 mm grain draws 75px across, so five coarse dots clip on a phone.
        samples = ",".join(str(x) for x in g["grain_samples_mm"][:3])
        sample = ac_url(links, "contact", "sample",
                        f'{g["name"]} grade aragonite aquarium sand, {s["bag_lb"]} lb bag '
                        f'({s["sku"]}), sample',
                        f'card-{s["sku"]}')
        tone = {"fine": "1", "medium": "2", "coarse": "3"}.get(s["grade"], "1")
        # Every card carries this block, so the six line up in a grid. A retail
        # bag shows the margin a shelf price would earn; a trade bag shows what
        # the bigger bag saves per pound, which is the reason to stock it.
        margin = ""
        if s.get("suggested_shelf"):
            pct = (s["suggested_shelf"] - s["list_per_bag"]) / s["suggested_shelf"] * 100
            margin = (
                f'<div class="product__margin">Suggested shelf {money(s["suggested_shelf"])} · '
                f'<b>{pct:.0f}% margin</b> at single-pallet cost. A suggestion for your own pricing, '
                f'not a condition of sale.</div>\n        '
            )
        else:
            retail = next((x for x in products["skus"]
                           if x["grade"] == s["grade"] and x.get("suggested_shelf")), None)
            if retail:
                saving = retail["list_per_bag"] / retail["bag_lb"] - per_lb
                pct = saving / (retail["list_per_bag"] / retail["bag_lb"]) * 100
                margin = (
                    f'<div class="product__margin"><b>{money(saving)} less per pound</b> than the '
                    f'{retail["bag_lb"]} lb bag, {pct:.0f}% down. For volume, refills and '
                    f'back-of-house.</div>\n        '
                )
        out.append(
            f'<article class="product product--{esc(s["grade"])}" data-sku="{esc(s["sku"])}" '
            f'data-name="{esc(g["name"])} {esc(s["bag_lb"])} lb" data-per-bag="{s["list_per_bag"]}" '
            f'data-bags-per-pallet="{s["bags_per_pallet"]}" data-bag-lb="{s["bag_lb"]}">\n'
            f'        <div class="product__band" aria-hidden="true"></div>\n'
            f'        <div class="product__head"><span class="sku">{esc(s["sku"])}</span>'
            f'<span class="product__type">{esc(s["bag_type"])}</span></div>\n'
            f'        <div class="product__sample" data-grains="{samples}" data-tone="{tone}" '
            f'role="img" aria-label="{esc(g["name"])} grain, {esc(g["grain_mm"])}, drawn at true scale"></div>\n'
            f'        <div class="product__title">\n'
            f'          <h3><a href="{esc(g["page"])}">{esc(g["name"])} · {esc(s["bag_lb"])} lb</a></h3>\n'
            f'          <div class="product__mm num">{esc(g["grain_mm"])} · {esc(g["mesh"])} mesh · '
            f'{esc(g["bulk_density_lb_ft3"])} lb/ft³</div>\n'
            f'        </div>\n'
            f'        <div class="product__price">\n'
            f'          <div class="price">{money(s["list_per_bag"])} <small>per bag</small></div>\n'
            f'          <div class="price__sub num">{money(pallet, cents=False)} per pallet · '
            f'{s["bags_per_pallet"]} bags · {s["bags_per_pallet"] * s["bag_lb"]:,} lb</div>\n'
            f'          <div class="price__rows">\n'
            f'            <div class="price__row"><span>Per pound</span><b>{money(per_lb)}</b></div>\n'
            f'            <div class="price__row"><span>At {esc(best["label"])}</span><b>{money(best_bag)} per bag</b></div>\n'
            f'          </div>\n'
            f'        </div>\n'
            f'        {margin}<div class="product__foot">\n'
            f'          <div class="qty">\n'
            f'            <button type="button" data-qty-down aria-label="One pallet fewer of {esc(s["sku"])}" disabled>&minus;</button>\n'
            f'            <label class="visually-hidden" for="q-{esc(s["sku"])}">Pallets of {esc(s["sku"])}</label>\n'
            f'            <input id="q-{esc(s["sku"])}" type="number" inputmode="numeric" value="0" min="0" max="999" step="1">\n'
            f'            <button type="button" data-qty-up aria-label="One pallet more of {esc(s["sku"])}">+</button>\n'
            f'          </div>\n'
            f'          <span class="qty__label">pallets</span>\n'
            f'          <a class="ext-link" href="{esc(sample)}">Sample{EXT_ICON}</a>\n'
            f'        </div>\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def tier_cells(products):
    out = []
    for t in products["tiers"]:
        off = "List price" if not t["discount"] else f'{t["discount"] * 100:.0f}% off'
        out.append(
            f'<div class="tier" data-tier="{esc(t["id"])}" data-active="false">\n'
            f'        <div class="tier__label">{esc(t["label"])}</div>\n'
            f'        <div class="tier__off">{esc(off)}</div>\n'
            f'        <p class="tier__note">{esc(t["note"])}</p>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


def tier_headers(products):
    return "".join(
        f'<th scope="col">{esc(t["label"])}</th>' for t in products["tiers"]
    )


def price_rows(products, grades, links):
    by_slug = grade_by_slug(grades)
    tiers = products["tiers"]
    out = []
    last_grade = None
    for s in products["skus"]:
        g = by_slug[s["grade"]]
        brk = ' class="is-grade-break"' if last_grade and last_grade != s["grade"] else ""
        last_grade = s["grade"]
        cells = "".join(
            f'<td class="{"t-price" if i == 0 else ""}">{money(tier_price(s["list_per_bag"], t))}</td>'
            for i, t in enumerate(tiers)
        )
        note = (f'{g["name"]} grade aragonite aquarium sand, {s["bag_lb"]} lb bag '
                f'({s["sku"]}), sample')
        sample = ac_url(links, "contact", "sample", note, f'pricelist-{s["sku"]}')
        out.append(
            f'<tr{brk}>\n'
            f'            <th scope="row"><span class="sku">{esc(s["sku"])}</span></th>\n'
            f'            <td class="t-left"><a class="prose-link" href="{esc(g["page"])}">{esc(g["name"])}</a> '
            f'· {esc(s["bag_lb"])} lb {esc(s["bag_type"].lower())} · {esc(g["grain_mm"])}</td>\n'
            f'            {cells}\n'
            f'            <td>{money(s["list_per_bag"] * s["bags_per_pallet"], cents=False)}</td>\n'
            f'            <td>{money(s["list_per_bag"] / s["bag_lb"])}</td>\n'
            f'            <td><a class="ext-link" href="{esc(sample)}">Sample{EXT_ICON}</a></td>\n'
            f'          </tr>'
        )
    return "\n          ".join(out)


def spec_rows(grades):
    rows = [
        ("Grain size", "grain_mm"),
        ("Mesh, U.S. sieve", "mesh"),
        ("Bulk density", None),
        ("Calcium carbonate, typical", None),
        ("Moisture at packaging", None),
        ("Fines below 0.25 mm", None),
        ("Primary use", "primary_use"),
    ]
    out = []
    for label, key in rows:
        if key:
            cells = "".join(f'<td class="val">{esc(g[key])}</td>' for g in grades)
        elif label.startswith("Bulk"):
            cells = "".join(f'<td class="val num">{esc(g["bulk_density_lb_ft3"])} lb/ft³</td>' for g in grades)
        elif label.startswith("Calcium"):
            cells = "".join(f'<td class="val num">{esc(g["caco3_pct"])}%</td>' for g in grades)
        elif label.startswith("Moisture"):
            cells = "".join(f'<td class="val num">≤ {esc(g["moisture_max_pct"])}%</td>' for g in grades)
        else:
            cells = "".join(f'<td class="val num">≤ {esc(g["fines_max_pct"])}%</td>' for g in grades)
        out.append(f'<tr><th scope="row">{esc(label)}</th>{cells}</tr>')
    return "\n          ".join(out)


def tiers_attr(products):
    """The tier table as a JSON attribute for the quote builder."""
    data = [
        {"id": t["id"], "label": t["label"], "min_pallets": t["min_pallets"],
         "max_pallets": t["max_pallets"], "discount": t["discount"]}
        for t in products["tiers"]
    ]
    return json.dumps(data, ensure_ascii=False).replace("'", "&#39;")


def catalogue_attr(products, grades):
    """Everything wholesale.html needs to re-price a quote handed to it."""
    by_slug = grade_by_slug(grades)
    data = {
        "skus": {
            s["sku"]: {
                "name": f'{by_slug[s["grade"]]["name"]} {s["bag_lb"]} lb',
                "perBag": s["list_per_bag"],
                "bags": s["bags_per_pallet"],
            }
            for s in products["skus"]
        },
        "tiers": [
            {"id": t["id"], "label": t["label"], "min_pallets": t["min_pallets"],
             "max_pallets": t["max_pallets"], "discount": t["discount"]}
            for t in products["tiers"]
        ],
    }
    return json.dumps(data, ensure_ascii=False).replace("'", "&#39;")


def sku_block(products, grades, slug, links):
    """The two bag sizes of one grade, priced, for that grade's own page."""
    by_slug = grade_by_slug(grades)
    g = by_slug[slug]
    out = []
    for s in products["skus"]:
        if s["grade"] != slug:
            continue
        pallet = s["list_per_bag"] * s["bags_per_pallet"]
        sample = ac_url(links, "contact", "sample",
                        f'{g["name"]} grade aragonite aquarium sand, {s["bag_lb"]} lb bag '
                        f'({s["sku"]}), sample', f'grade-{slug}-{s["sku"]}-sample')
        pricing = ac_url(links, "contact", "pricing",
                         f'{g["name"]} grade aragonite aquarium sand, {s["bag_lb"]} lb bag '
                         f'({s["sku"]}), pricing by the pallet', f'grade-{slug}-{s["sku"]}-pricing')
        shelf = ""
        if s.get("suggested_shelf"):
            pct = (s["suggested_shelf"] - s["list_per_bag"]) / s["suggested_shelf"] * 100
            shelf = (f'<div class="price__row"><span>Suggested shelf</span>'
                     f'<b>{money(s["suggested_shelf"])} · {pct:.0f}% margin</b></div>')
        out.append(
            f'<article class="product product--{esc(slug)}">\n'
            f'        <div class="product__band" aria-hidden="true"></div>\n'
            f'        <div class="product__head"><span class="sku">{esc(s["sku"])}</span>'
            f'<span class="product__type">{esc(s["bag_type"])}</span></div>\n'
            f'        <div class="product__title"><h3>{esc(g["name"])} · {esc(s["bag_lb"])} lb</h3>\n'
            f'          <div class="product__mm">{esc(s["bag_note"])}</div>\n'
            f'        </div>\n'
            f'        <div class="product__price">\n'
            f'          <div class="price">{money(s["list_per_bag"])} <small>per bag</small></div>\n'
            f'          <div class="price__sub num">{money(pallet, cents=False)} per pallet · '
            f'{s["bags_per_pallet"]} bags · {s["bags_per_pallet"] * s["bag_lb"]:,} lb</div>\n'
            f'          <div class="price__rows">\n'
            f'            <div class="price__row"><span>Per pound</span><b>{money(s["list_per_bag"] / s["bag_lb"])}</b></div>\n'
            f'            {shelf}\n'
            f'          </div>\n'
            f'        </div>\n'
            f'        <div class="product__foot">\n'
            f'          <a class="btn btn-ink btn-sm" href="{esc(pricing)}">Request pricing{EXT_ICON}</a>\n'
            f'          <a class="ext-link" href="{esc(sample)}">Sample{EXT_ICON}</a>\n'
            f'        </div>\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def jsonld_catalogue(products, grades):
    by_slug = grade_by_slug(grades)
    offers = []
    for s in products["skus"]:
        g = by_slug[s["grade"]]
        offers.append({
            "@type": "Product",
            "sku": s["sku"],
            "name": f'AragoCor Aragonite, {g["name"]} grade, {s["bag_lb"]} lb',
            "description": f'{g["grain_mm"]} ({g["mesh"]} mesh) Bahamian aragonite aquarium substrate, '
                           f'{s["bag_lb"]} lb {s["bag_type"].lower()}, {s["bags_per_pallet"]} bags per pallet.',
            "brand": {"@type": "Brand", "name": "AragoCor"},
            "offers": {
                "@type": "Offer",
                "priceCurrency": products["currency"],
                "price": "{:.2f}".format(s["list_per_bag"]),
                "eligibleQuantity": {"@type": "QuantitativeValue", "value": s["bags_per_pallet"],
                                     "unitText": "bags per pallet"},
                "availability": "https://schema.org/InStock",
                "url": "https://aragonitesand.com/products.html",
            },
        })
    return json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                       "name": "AragoCor Aragonite wholesale price list",
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": o}
                                           for i, o in enumerate(offers)]},
                      ensure_ascii=False).replace("</", "<\\/")


def jsonld_product(g, pack):
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"AragoCor Aragonite, {g['name']} grade",
        "description": g["description"],
        "brand": {"@type": "Brand", "name": "AragoCor"},
        "manufacturer": {"@type": "Organization", "name": "AragoCor Minerals LLC", "url": "https://www.aragocorminerals.com/"},
        "url": f"https://aragonitesand.com/{g['page']}",
        "material": "Aragonite (calcium carbonate)",
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "Grain size", "value": g["grain_mm"]},
            {"@type": "PropertyValue", "name": "Mesh", "value": g["mesh"]},
            {"@type": "PropertyValue", "name": "Bulk density", "value": f"{g['bulk_density_lb_ft3']} lb/ft³"},
            {"@type": "PropertyValue", "name": "Retail bag", "value": f"{pack['retail_bag_lb']} lb"},
            {"@type": "PropertyValue", "name": "Trade bag", "value": f"{pack['trade_bag_lb']} lb"},
        ],
    }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build():
    grades_doc = load_json("grades.json")
    pack = load_json("packaging.json")
    products = load_json("products.json")
    links = load_json("links.json")
    grades = grades_doc["grades"]
    tones = {"fine": "1", "medium": "2", "coarse": "3"}

    common = {
        "retail_bag_lb": pack["retail_bag_lb"],
        "trade_bag_lb": pack["trade_bag_lb"],
        "retail_bags_per_pallet": pack["retail_bags_per_pallet"],
        "trade_bags_per_pallet": pack["trade_bags_per_pallet"],
        "pallet_net_lb": f"{pack['pallet_net_lb']:,}",
        "pallet_footprint": pack["pallet_footprint"],
        "dealer_email": pack["dealer_contact_email"],
        "dealer_phone": pack["dealer_contact_phone"],
        "dealer_phone_href": "+" + re.sub(r"\D", "", pack["dealer_contact_phone"]),
        "opening_minimum": pack["opening_order"]["minimum"],
        "opening_mixed": pack["opening_order"]["mixed_pallet"],
        "opening_terms": pack["opening_order"]["terms"],
        "opening_lead_time": pack["opening_order"]["lead_time"],
        "opening_ships_from": pack["opening_order"]["ships_from"],
        "opening_freight": pack["opening_order"]["freight"],
        "case_pack_retail": pack["case_pack"]["retail"],
        "case_pack_layers": pack["case_pack"]["layers"],
        "pallet_height_in": pack["pallet_height_in"],
        "pallet_gross_lb": pack["pallet_gross_lb"],
        # commerce
        "currency": products["currency"],
        "effective_date": products["effective_date"],
        "price_note": products["price_note"],
        "distributor_note": products["distributor_note"],
        "price_banner_html": price_status_banner(products),
        "tiers_json_html": tiers_attr(products),
        "catalogue_json_html": catalogue_attr(products, grades),
        "product_cards_html": product_cards(products, grades, links),
        "tier_cells_html": tier_cells(products),
        "tier_headers_html": tier_headers(products),
        "price_rows_html": price_rows(products, grades, links),
        "spec_rows_html": spec_rows(grades),
        "tier2_label": products["tiers"][1]["label"],
        "tier2_pct": "{:.0f}".format(products["tiers"][1]["discount"] * 100),
        "truckload_pallets": products["truckload_pallets"],
        # outbound to the parent, where buying actually happens
        "ac_name": links["parent_name"],
        "ac_host": links["parent_host"],
        "ac_home": ac_url(links, "home", content="body"),
        "ac_contact": ac_url(links, "contact", content="body"),
        "ac_sample": ac_url(links, "contact", "sample",
                            "Aragonite aquarium sand sample, all three grades",
                            "sample"),
        "ac_pricing": ac_url(links, "contact", "pricing",
                             "Aragonite aquarium sand, wholesale pricing by the pallet",
                             "pricing"),
        "ac_distribution": ac_url(links, "contact", "distribution",
                                  "Aragonite aquarium sand, distributor schedule",
                                  "distribution"),
        "ac_technical": ac_url(links, "contact", "technical",
                               "Aragonite aquarium sand technical data package",
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
            'data-ac-industry="' + esc(links["industry"]) + '" '
            'data-ac-utm="' + esc("{source}|{medium}|{campaign}".format(**links["utm"])) + '"'
        ),
        "ext_icon_html": EXT_ICON,
        "ac_note_html": ac_note(links),
    }
    for s_ in products["skus"]:
        common[f'{s_["sku"].lower().replace("-", "_")}_price'] = money(s_["list_per_bag"])
    cheapest = min(products["skus"], key=lambda x: x["list_per_bag"] / x["bag_lb"])
    common["from_per_lb"] = money(cheapest["list_per_bag"] / cheapest["bag_lb"])
    common["from_per_bag"] = money(min(x["list_per_bag"] for x in products["skus"]))

    written = []

    # Grade pages: one template, three instances.
    tpl = (TEMPLATES / "grade.html").read_text(encoding="utf-8")
    for g in grades:
        ctx = dict(common)
        ctx.update(g)
        ctx["canonical"] = g["page"]
        ctx["name_lower"] = g["name"].lower()
        ctx["tone"] = tones.get(g["slug"], "1")
        ctx["grain_samples"] = ",".join(str(x) for x in g["grain_samples_mm"])
        ctx["sieve_html"] = sieve_rows(g["sieve"])
        ctx["uses_html"] = uses_blocks(g["uses"])
        ctx["others_html"] = other_cards(grades, g["slug"])
        ctx["jsonld_html"] = jsonld_product(g, pack)
        ctx["sku_block_html"] = sku_block(products, grades, g["slug"], links)
        ctx["ac_grade_sample"] = ac_url(
            links, "contact", "sample",
            f'{g["name"]} grade aragonite aquarium sand, {g["grain_mm"]}, sample',
            f'sample-{g["slug"]}')
        ctx["ac_grade_pricing"] = ac_url(
            links, "contact", "pricing",
            f'{g["name"]} grade aragonite aquarium sand, {g["grain_mm"]}, pricing by the pallet',
            f'pricing-{g["slug"]}')
        ctx["grade_from_price"] = money(min(
            x["list_per_bag"] for x in products["skus"]
            if x["grade"] == g["slug"] and x["bag_lb"] == pack["retail_bag_lb"]))
        out = ROOT / g["page"]
        out.write_text(render(tpl, ctx), encoding="utf-8")
        written.append(out.name)

    # Other pages carry their own title/description in a leading JSON front
    # matter comment so the data stays with the page.
    for name in ("index", "products", "wholesale", "about", "404"):
        src = (TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*meta\s*(\{.*?\})\s*-->\s*", src, re.S)
        if not m:
            raise RuntimeError(f"templates/{name}.html is missing its <!-- meta {{...}} --> header")
        meta = json.loads(m.group(1))
        body = src[m.end():]
        ctx = dict(common)
        ctx.update(meta)
        ctx.setdefault("canonical", "" if name == "index" else f"{name}.html")
        ctx["jsonld_html"] = jsonld_catalogue(products, grades)
        ctx["grade_cards_html"] = grade_cards(grades)
        ctx["home_grains_html"] = home_grains(grades)
        ctx["calc_grade_options_html"] = calc_grade_options(grades)
        ctx["medium_density"] = next(g["bulk_density_lb_ft3"] for g in grades if g["slug"] == "medium")
        for g in grades:
            for k in ("grain_mm", "mesh", "bulk_density_lb_ft3", "caco3_pct", "primary_use", "page", "name"):
                ctx[f"{g['slug']}_{k}"] = g[k]
        out = ROOT / f"{name}.html"
        out.write_text(render(body, ctx), encoding="utf-8")
        written.append(out.name)

    return written


if __name__ == "__main__":
    try:
        for name in build():
            print("wrote", name)
    except (KeyError, RuntimeError) as e:
        print("build failed:", e, file=sys.stderr)
        sys.exit(1)
