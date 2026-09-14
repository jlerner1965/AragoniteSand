# aragonitesand.com

Product site for AragoCor Minerals' bagged aragonite aquarium substrate. Plain
static HTML, CSS and JavaScript. No framework, no build step for hosting, no
dependencies. Upload the repository root to any static host and it runs.

## Layout

```
index.html              Home: hero, grain scale, spec strip, grade cards, lot lookup,
                        depth calculator, "what the material does", wholesale strip
grade-fine.html         One template, three instances (generated, see below)
grade-medium.html
grade-coarse.html
wholesale.html          Pallet configuration, case pack, opening terms, mixed-pallet
                        policy, dealer inquiry form
about.html              Ownership, Stockton operation, sourcing, testing practice
404.html

css/tokens.css          The design system extracted from aragocorminerals.com
css/site.css            Chrome (header, footer) and components built on the tokens
js/site.js              Nav, grain illustration, lot lookup, depth calculator, form

data/grades.json        The three grades: sizes, densities, copy, sieve data
data/lots.json          Lot register read by the lot lookup at runtime
data/packaging.json     Bag, pallet and trade terms

templates/              Page templates and the shared head/header/footer partials
tools/build.py          Renders every page from templates/ and data/
assets/                 Parent-company logo and favicon
```

## Editing a page

The committed HTML at the root is **generated**. Edit `templates/*.html` or a
file in `data/`, then run:

```
python3 tools/build.py
```

and commit the regenerated pages together with the source. Python 3.8+ with
the standard library is all it needs. The template syntax is three things:
`{{> partial}}` includes `templates/partials/partial.html`, `{{key}}` inserts
an HTML-escaped value, and `{{key_html}}` inserts pre-rendered HTML. An
unknown key fails the build rather than shipping literal braces.

The three grade pages are `templates/grade.html` rendered once per entry in
`data/grades.json`. Change the template to change all three; change the data
to change one.

## Adding a real lot

Add an entry to `data/lots.json` under `lots`, keyed by the code exactly as it
is printed on the bag. The home page fetches the file at runtime, so no
rebuild is needed. The `_readme` block in the file documents each field.
Delete the three demo lots (they carry `"placeholder": true`) once a real one
exists. A bag can link straight to its analysis with
`https://aragonitesand.com/?lot=AC-2608-F01` — the lookup reads the `lot`
query parameter, which is what to encode in a QR code.

## Placeholder data that must be replaced before launch

Everything below is invented. In the pages it is marked with an amber
`data-placeholder` chip so it cannot ship unnoticed; in the data files it is
called out in a `_todo` or `_readme` block; in the templates there is a
`<!-- TODO(...) -->` comment beside it. Grep for `placeholder`, `TODO(` and
`TBC` to find every instance.

| What | Where | Status |
|---|---|---|
| All three lot analyses and every number in them | `data/lots.json` | invented, delete when real lots exist |
| Testing lab name and methods | `data/lots.json` `lab`, `method`; `about.html` testing section | TODO |
| CaCO₃ percentages per grade | `data/grades.json` `caco3_pct` | invented |
| Moisture, fines and acid-insoluble limits | `data/grades.json` | invented |
| Sieve distributions on the grade pages | `data/grades.json` `sieve` | invented |
| Pallet configuration (60 bags / 1,200 lb, trade 40 bags) | `data/packaging.json` | a guess from the brief |
| Case pack, layers, pallet height, gross weight | `data/packaging.json` | TODO |
| Payment terms, lead time, freight terms | `data/packaging.json` `opening_order` | TODO |
| Dealer inquiry endpoint | `templates/wholesale.html` form `data-endpoint` | empty; form falls back to a pre-filled email |
| Grain-scale visuals | every hero | drawn geometry at 15 px/mm, replace with photography at scale |
| Stockton facility photograph | `about.html` | empty frame |

Values that come from the brief and are **not** placeholders: grain size
ranges, mesh equivalents, bulk densities (90 / 92 / 88 lb/ft³), primary uses,
20 lb retail and 50 lb trade bag weights, and the company address and phone,
which are the parent site's.

## The design system

`css/tokens.css` was extracted from the aragocorminerals.com source
(`jlerner1965/aragocor-site`) before any page here was written. It records
the exact hex palette, the three typefaces and the loaded weights, the type
scale in use, section rhythm, container width, gutters, radii, button and
form-field dimensions, the header and footer pattern including mobile
behaviour, and the light/dark band alternation. Each token cites its source
file. Additions that the parent has no equivalent for are marked `EXTENDED:`
in the file and stay inside the parent palette: the three grade tints (sand,
sand darkened toward ink, tide), the sieve bar chart, the grain-scale plate,
and the amber placeholder chip, which reuses the parent's one warning colour.

One deliberate deviation from the parent: its eyebrow and footer labels are
tracked uppercase mono. The brief rules sentence case throughout, and the
brief wins on content rules, so the same mono labels are set in sentence
case with the tracking loosened. This is noted at the bottom of `tokens.css`.

## Content rules

- No pH guarantees. Aragonite supports alkalinity; it does not hold pH at a
  fixed value. The footer, the home page and the about page say this in
  those words.
- Specs are typical values; the published lot analysis governs. The footer
  carries this on every page.
- Each grade page says plainly where that grade is the wrong choice, in the
  third block of its fit section.
- Sentence case throughout.

## Hosting

Static. Every link is a relative `.html` path, so the site works from a
subdirectory or the root of any host. The two data files are fetched over
HTTP; opening a page from the file system disables the lot lookup and the
runtime density refresh (the calculator still works from the values in the
markup). If the host rewrites `/grade-fine` to `/grade-fine.html` (Vercel
`cleanUrls`, Netlify pretty URLs), the canonical tags in
`templates/partials/head.html` and `sitemap.xml` should drop the extension.
