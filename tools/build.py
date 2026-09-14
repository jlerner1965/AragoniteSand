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

def money(n, cents=True):
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


def price_status_banner(products):
    """Shown once per page carrying prices, while the figures are invented."""
    if products.get("price_status") == "live":
        return ""
    return (
        '<p class="notice" role="note"><strong>Pre-launch price list.</strong> '
        'The figures below are placeholders for layout and are not quotable. '
        'Current pricing is issued on request.</p>'
    )


# ---------- market cards ----------

def market_cards(markets, products, grades):
    gs, ps = grade_by_slug(grades), by_id(products["packs"])
    out = []
    for m in markets["markets"]:
        grade_names = ", ".join(gs[x]["name"] for x in m["grades"])
        pack_names = ", ".join(ps[x]["short"] for x in m["packs"])
        tag = "" if m["status"] == "served" else (
            '<span class="tag tag--quiet">Quoted per application</span>')
        out.append(
            f'<article class="market">\n'
            f'        <h3><a href="markets.html#{esc(m["id"])}">{esc(m["name"])}</a></h3>\n'
            f'        <p class="market__summary">{esc(m["summary"])}</p>\n'
            f'        <dl class="market__spec">\n'
            f'          <div><dt>Grades</dt><dd>{esc(grade_names)}</dd></div>\n'
            f'          <div><dt>Formats</dt><dd>{esc(pack_names)}</dd></div>\n'
            f'          <div><dt>Buyers</dt><dd>{esc(m["buyers"])}</dd></div>\n'
            f'        </dl>\n'
            f'        {tag}\n'
            f'      </article>'
        )
    return "\n      ".join(out)


def market_sections(markets, products, grades, links):
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
                         f'market-{m["id"]}')
        sample = ac_url(links, "contact", "sample",
                        f'{m["name"]} — aragonite sample',
                        f'market-{m["id"]}-sample')
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
            f'      <dl class="facts">\n'
            f'        <div class="facts__row"><dt>Grades</dt><dd>{esc(", ".join(gs[x]["name"] for x in m["grades"]))}</dd></div>\n'
            f'        <div class="facts__row"><dt>Most specified</dt><dd>{esc(lead["name"])}, {esc(lead["grain_mm"])}</dd></div>\n'
            f'        <div class="facts__row"><dt>Formats</dt><dd>{esc(", ".join(ps[x]["name"] for x in m["packs"]))}</dd></div>\n'
            f'        <div class="facts__row"><dt>Supply</dt><dd>{"Stock item" if m["status"] == "served" else "Quoted per application"}</dd></div>\n'
            f'      </dl>\n'
            f'    </div>\n'
            f'    <p class="note" style="margin-top:22px">Grade pages: {grade_links}</p>\n'
            f'  </div>\n'
            f'</section>'
        )
    return "\n\n".join(out)


# ---------- catalogue ----------

def product_cards(products, grades, links):
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
            sub = (f'{money(r["pallet"], cents=False)} per pallet'
                   if r["palletable"] and r["pack"]["per_pallet"] > 1
                   else f'{money(r["per_lb"])} per lb')
            fmt.append(
                f'<tr>\n'
                f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span>'
                f'<span class="fmt__name">{esc(r["pack"]["short"])}</span></th>\n'
                f'            <td class="t-price">{money(r["list"])}<span class="per"> / {esc(r["pack"]["unit"])}</span></td>\n'
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
            f'        <div class="product__sample" data-grains="{samples}" data-tone="{tone}" '
            f'role="img" aria-label="{esc(g["name"])} grain at true scale"></div>\n'
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
    out = []
    for t in products["tiers"]:
        off = "List" if not t["discount"] else f'{t["discount"] * 100:.0f}% off'
        out.append(
            f'<div class="tier" data-tier="{esc(t["id"])}" data-active="false">\n'
            f'        <div class="tier__label">{esc(t["label"])}</div>\n'
            f'        <div class="tier__off">{esc(off)}</div>\n'
            f'        <p class="tier__note">{esc(t["note"])}</p>\n'
            f'      </div>'
        )
    return "\n      ".join(out)


def tier_headers(products):
    return "".join(f'<th scope="col">{esc(t["label"])}</th>' for t in products["tiers"])


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


def spec_rows(grades):
    rows = [
        ("Grain size", "grain_mm"), ("Mesh, U.S. sieve", "mesh"),
        ("Bulk density", None), ("Calcium carbonate, typical", None),
        ("Moisture at packaging", None), ("Fines below 0.25 mm", None),
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
        out.append(
            f'<tr data-sku="{esc(r["sku"])}" data-name="{esc(r["grade"]["name"])} {esc(r["pack"]["short"])}" '
            f'data-per-bag="{r["list"]}" data-bags-per-pallet="{unit_per_pallet}" '
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
    data = [{"id": t["id"], "label": t["label"], "min_pallets": t["min_pallets"],
             "max_pallets": t["max_pallets"], "discount": t["discount"]}
            for t in products["tiers"]]
    return json.dumps(data, ensure_ascii=False).replace("'", "&#39;")


def catalogue_attr(products, grades):
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
        extra.append(f'{money(r["per_lb"])} per lb')
        if r["shelf"]:
            pct = (r["shelf"] - r["list"]) / r["shelf"] * 100
            extra.append(f'suggested shelf {money(r["shelf"])}, {pct:.0f}% margin')
        out.append(
            f'<tr>\n'
            f'            <th scope="row"><span class="sku">{esc(r["sku"])}</span></th>\n'
            f'            <td class="t-left">{esc(r["pack"]["name"])}<div class="t-sub">{esc(r["pack"]["spec"])}</div></td>\n'
            f'            <td class="t-price">{money(r["list"])}<span class="per"> / {esc(r["pack"]["unit"])}</span></td>\n'
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


def jsonld_catalogue(products, grades):
    rows = sku_rows(products, grades)
    offers = []
    for r in rows:
        offers.append({
            "@type": "Product",
            "sku": r["sku"],
            "name": f'Aragonite, {r["grade"]["name"]} grade, {r["pack"]["name"]}',
            "description": f'{r["grade"]["grain_mm"]} ({r["grade"]["mesh"]} mesh) oolitic aragonite, '
                           f'{r["pack"]["name"]}. {r["pack"]["spec"]}.',
            "brand": {"@type": "Brand", "name": "AragoCor"},
            "offers": {
                "@type": "Offer",
                "priceCurrency": products["currency"],
                "price": "{:.2f}".format(r["list"]),
                "availability": "https://schema.org/InStock",
                "url": "https://aragonitesand.com/products.html",
            },
        })
    return json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                       "name": "Aragonite wholesale price list",
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": o}
                                           for i, o in enumerate(offers)]},
                      ensure_ascii=False).replace("</", "<\\/")


def jsonld_product(g, pack):
    """`pack` is a plain string listing the formats this grade ships in."""
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
            {"@type": "PropertyValue", "name": "Formats", "value": pack},
        ],
    }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def build():
    grades_doc = load_json("grades.json")
    pack = load_json("packaging.json")
    products = load_json("products.json")
    links = load_json("links.json")
    lit = load_json("literature.json")
    markets = load_json("markets.json")
    company = load_json("company.json")
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
        "literature_html": literature(lit, links, "all"),
        "literature_public_html": literature(lit, links, "public"),
        # markets, packs and company furniture
        "market_cards_html": market_cards(markets, products, grades),
        "market_sections_html": market_sections(markets, products, grades, links),
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
    common["from_per_lb"] = money(min(r["per_lb"] for r in _rows))
    common["from_per_ton"] = money(min(r["per_ton"] for r in _rows), cents=False)
    common["from_per_bag"] = money(min(r["list"] for r in _rows if r["pack"]["unit"] == "bag"))

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
        ctx["jsonld_html"] = jsonld_product(
            g, ", ".join(r["pack"]["name"] for r in sku_rows(products, grades)
                         if r["grade"]["slug"] == g["slug"]))
        ctx["sku_block_html"] = sku_block(products, grades, g["slug"], links)
        ctx["grade_markets_html"] = grade_markets(markets, g["slug"], links)
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
        out = ROOT / g["page"]
        out.write_text(render(tpl, ctx), encoding="utf-8")
        written.append(out.name)

    # Other pages carry their own title/description in a leading JSON front
    # matter comment so the data stays with the page.
    for name in ("index", "markets", "products", "wholesale", "dealers", "about", "404"):
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
