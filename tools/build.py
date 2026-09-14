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
        samples = ",".join(str(x) for x in g["grain_samples_mm"][:5])
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
    }

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
        out = ROOT / g["page"]
        out.write_text(render(tpl, ctx), encoding="utf-8")
        written.append(out.name)

    # Other pages carry their own title/description in a leading JSON front
    # matter comment so the data stays with the page.
    for name in ("index", "wholesale", "about", "404"):
        src = (TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
        m = re.match(r"\s*<!--\s*meta\s*(\{.*?\})\s*-->\s*", src, re.S)
        if not m:
            raise RuntimeError(f"templates/{name}.html is missing its <!-- meta {{...}} --> header")
        meta = json.loads(m.group(1))
        body = src[m.end():]
        ctx = dict(common)
        ctx.update(meta)
        ctx.setdefault("canonical", "" if name == "index" else f"{name}.html")
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
