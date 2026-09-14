# aragonitesand.com

Wholesale product site for AragoCor Minerals' bagged aragonite aquarium
substrate. Six SKUs, three grades in 20 lb retail and 50 lb trade bags, sold by
the pallet to aquarium retailers and distributors, with published pricing.

Plain static HTML, CSS and JavaScript. No framework, no build step for hosting,
no dependencies. Upload the repository root to any static host and it runs.

**Buying happens at aragocorminerals.com.** This site is the catalogue, the
price list and the lab record; every sample request, pricing request and quote
hands off to the parent site, which has the real lead form, the CRM behind it
and the sales desk. See *Driving traffic to AragoCor* below.

## Layout

```
index.html              Home: hero, the six products with prices and the quote
                        builder, volume tiers, lot lookup, grade chooser,
                        depth calculator, ordering CTA
products.html           The catalogue: six product cards, the full tier-by-tier
                        price list, volume breaks, grade comparison table
grade-fine.html         One template, three instances (generated, see below):
grade-medium.html       hero with price, the grade's two SKUs priced, spec table,
grade-coarse.html       sieve, fit and misfit, depth calculator, other grades
wholesale.html          Ordering: price summary, pallet configuration, case pack,
                        opening terms, freight, dealer inquiry form
dealers.html            Dealer resources: how the category sells at the counter,
                        the literature library, shelf and facing guidance
about.html              Ownership, Stockton operation, sourcing, testing practice
404.html

css/tokens.css          The design system: palette, type, scale, rhythm, commerce
css/site.css            Chrome (header, footer), page and commerce components
js/site.js              Nav, grain illustration, lot lookup, depth calculator,
                        inquiry form, quote builder, quote handoff

data/products.json      The six SKUs, prices and volume tiers
data/links.json         Outbound links to aragocorminerals.com
data/literature.json    Spec sheets, safety data, price list, photography, POS
data/grades.json        The three grades: sizes, densities, copy, sieve data
data/lots.json          Lot register read by the lot lookup at runtime
data/packaging.json     Bag, pallet and trade terms

templates/              Page templates and the shared head/header/footer partials
tools/build.py          Renders every page from templates/ and data/
assets/mark.svg         The site's own logo mark (source of the favicons)
assets/mark-*.png       Rendered from mark.svg: favicon, apple touch, Open Graph
assets/favicon.ico      16/32/48 packed from the same mark
assets/aragocor-logo.png  The parent wordmark, used once, in the footer
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

## Changing prices

`data/products.json` is the only place a price is written. The product cards,
the grade-page price blocks, the tier-by-tier price list, the JSON-LD offers
and the quote builder are all rendered from it, and per-pallet and per-pound
figures are derived rather than stored, so they cannot drift out of step with
the per-bag price.

While `price_status` is `"placeholder"`, every page carrying a price shows an
amber banner saying the figures are invented. To go live: put the real numbers
in, set `effective_date`, set `price_status` to `"live"`, and run the build.
The banners disappear; nothing else changes.

Volume tiers are a list under `tiers`. Add, remove or reprice them freely; the
price-list columns, the tier cards and the quote builder's arithmetic all
follow the file. The last tier is the one quoted on the product cards as the
best price.

## The quote builder

The products page and the home page let a buyer set a pallet count per SKU.
The running total applies the volume break for the total pallet count across
all grades, which is the actual commercial rule, and the matching tier card
highlights as it changes. "Send this for a firm quote" hands the line items to
the inquiry form as a query string:

```
wholesale.html?q=AR-F20:2,AR-M50:1#inquiry
```

The ordering page re-prices that string from its own embedded copy of the
catalogue, shows it above the form, and writes it into a field so what the
buyer priced is what arrives. Prices are embedded in the markup by the build
rather than fetched, so the arithmetic works with no network and from a
`file://` page. An unknown SKU or a malformed count is ignored rather than
rendered.

## Driving traffic to AragoCor

Every buying action on this site ends at `aragocorminerals.com/contact`. The
links are not bare URLs: they are deep links that arrive with the parent's own
lead form already filled in. The parameters were read out of the parent's
source (`lib/lead-form.js`, `lib/catalog.js`, `lib/attribution.js`), so they
land on real behaviour rather than being decorative:

| Parameter | What it does on arrival |
|---|---|
| `interest` | Preselects the journey: `sample`, `bulk-pricing`, `distribution`, `technical-evaluation` |
| `industry` | Preselects the industry. This site always sends `Aquarium & aquaculture` |
| `document` | Free text; the form writes it into the details field as `Requesting: …`, which is how a grade, a SKU or a whole quote travels across |
| `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` | Captured by the parent's attribution script and stored on the lead, so traffic sent from here is attributable in their CRM |

`utm_content` names the exact placement — `home-hero-sample`, `card-AR-F20`,
`pricelist-AR-C50`, `quote-builder`, `sample-fine` — so the report says which
control earned the lead, not just which site.

Where the links are: the header CTA, the home hero, an ordering band on the
home and products pages, every product card, every row of the price list, both
SKU blocks on each grade page, the grade-page ordering band, the top of the
inquiry section, the about page, the 404, and a dedicated footer column. Links
that leave the site carry a small outward-arrow icon.

`data/links.json` holds the base URL, the paths, the interest values, the
industry name and the UTM defaults. If the parent renames a path or an
interest value, change it there once; `tools/build.py` renders every link from
that file and `js/site.js` reads the same values out of the markup.

### The quote handoff

The quote builder's primary button sends the whole basket to the parent:

```
https://www.aragocorminerals.com/contact
  ?interest=bulk-pricing
  &industry=Aquarium%20%26%20aquaculture
  &document=Aragonite aquarium sand quote built on aragonitesand.com:
            Fine 20 lb (AR-F20) x 2 pallets, … — 260 bags, 7,600 lb,
            estimated $4,408.60 before freight (includes the 6% volume break)
  &utm_source=aragonitesand.com&utm_medium=referral
  &utm_campaign=aquarium-substrate&utm_content=quote-builder
```

so the buyer arrives at a form that already knows what they priced. A quieter
"Send here instead" link beside it keeps the local form path
(`wholesale.html?q=…`) working for anyone who would rather not leave.

The local dealer form on the ordering page still works and is now the
secondary route. It has no endpoint configured, so it falls back to a
pre-filled email. If you would rather have one funnel, delete that form and
the page will still convert through the AragoCor buttons above it.

## The literature library

`data/literature.json` lists every document a trade buyer asks for: spec
sheet, safety data sheet, certificate of analysis, source documentation, price
list, line sheet, credit application, product photography, shelf talkers,
counter card and web listing copy. It renders on `dealers.html` in full and on
`products.html` filtered to the public technical rows.

**No file in it exists yet**, and every entry has `file: null`. A null row is
not hidden and not a dead link: it renders as "available on request" and links
to AragoCor's contact form with the document named in the query string, so the
request reaches a person. Produce a PDF, drop it in `assets/literature/`, set
`file` to its path, rebuild, and that row becomes a download. Nothing else
changes.

Rows marked `"audience": "trade"` (price list, line sheet, credit application,
photography, point-of-sale) appear only on the dealer page. `"public"` rows
appear on both.

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
| Dealer inquiry endpoint | `templates/wholesale.html` form `data-endpoint` | empty; form falls back to a pre-filled email. The AragoCor route above needs no endpoint |
| Grain-scale visuals | every hero, and the product cards | drawn geometry at 15 px/mm, replace with photography at scale |
| Stockton facility photograph | `about.html` | empty frame |
| Every document in the literature library | `data/literature.json` | none produced; all `file: null` |
| **Every price, per bag and per pallet** | `data/products.json` `skus` | invented; `price_status` is `placeholder` |
| Volume tier discounts (6 / 11 / 15%) | `data/products.json` `tiers` | invented |
| Suggested shelf prices | `data/products.json` `suggested_shelf` | invented |
| Price-list effective date | `data/products.json` `effective_date` | TODO |
| UPCs for all six bags | `data/products.json` `upc` | TODO |

Values that come from the brief and are **not** placeholders: grain size
ranges, mesh equivalents, bulk densities (90 / 92 / 88 lb/ft³), primary uses,
20 lb retail and 50 lb trade bag weights, and the company address and phone,
which are the parent site's.

## The design system

`css/tokens.css` was extracted from the aragocorminerals.com source
(`jlerner1965/aragocor-site`) before any page here was written. It records the
type scale, section rhythm, container width, gutters, radii, button and
form-field dimensions, the header and footer pattern including mobile
behaviour, and the light/dark band alternation. Each token cites its source.

**The palette is derived from the parent, deliberately not identical to it.**
The structure is the parent's — one deep ink, one warm sand accent, an
off-white ground, white cards — because that is what makes this read as an
AragoCor site. The values are shifted so it does not read as the *same* site:

| role | parent | here | change |
|---|---|---|---|
| ink | `#0E3540` | `#0B2C3A` | deeper, a few degrees bluer |
| tide | `#526A70` | `#4E6B74` | tracks the ink |
| sand | `#D7C59C` | `#E0C68F` | warmer, more golden, more saturated |
| bone | `#F7F4ED` | `#F6F2E9` | a hair cooler |
| abyss | — | `#061C26` | new: footer and the deepest band |
| surf | — | `#17707E` | new: prices, SKUs, the quote builder |

`surf` is the one addition with a job the parent has no equivalent for. The
parent sells by quotation and publishes no prices; here commerce needs to be
visually separable from specification, so prices, SKU codes and quote controls
carry the accent and spec tables do not.

Every pair was measured. Body text runs 5.1:1 or better on its own ground, and
`surf` at 2.6:1 on ink is why `surf-light` (`#4FB8C4`, 6.3:1) exists and is the
only accent permitted on a dark band. The ratios are listed in `tokens.css`
beside the palette.

Other additions are marked `EXTENDED:` in the token file and stay inside the
palette: the three grade tints, the sieve bar chart, the grain-scale plate, the
commerce tokens, and the amber placeholder chip, which reuses the parent's one
warning colour.

### Brand

The site has its own identity. It is AragoCor's product and says so, but it no
longer wears AragoCor's logo.

**The mark** is three circles of increasing size on a screen line: the three
grades at true relative scale, which is the idea the whole catalogue is built
on. Nothing in it is taken from the AragoCor mark. It lives in
`assets/mark.svg` and is also inlined in the header and footer so the circles
can take `currentColor` and work on both the light nav and the near-black
footer; only the screen line is fixed, and it steps from sand-deep to sand on
dark grounds.

**The wordmark** is "Aragonite Sand" with "by AragoCor Minerals" beneath it in
mono. Ownership stays visible, as the brief requires, but it is an attribution
rather than the identity.

**The parent wordmark appears once**, at the foot of every page, labelled "A
product of" and linking to aragocorminerals.com. It used to sit in the header
of every page, which is what made the two sites hard to tell apart.

**The display typeface changed** from the parent's Source Serif 4 to Archivo,
a grotesque. This is the largest single change and the one most worth
reverting first if the resemblance should be closer: it is one token,
`--font-display` in `css/tokens.css`, plus the font request in
`templates/partials/head.html`. Archivo is the face the project's own
reference mockups were set in, its width axis is what the wordmark uses, and a
squared industrial face suits a price list better than a book serif. It is
still three families, not four: Archivo replaced Source Serif 4 rather than
joining it, and JetBrains Mono and the system sans body stack are the
parent's, unchanged. Those two, plus the shared palette structure and every
layout component, are what keep the sites related.

**Favicons** are generated from `mark.svg`, not hand-drawn twice. To change the
mark, edit the SVG and re-render:

```
node tools/render-mark.mjs     # needs Playwright's Chromium
```

### Density

The scale was pulled down a step from the parent's in September 2026, on the
brief that the site should read as a trade catalogue rather than an editorial
piece. The parent's hero tops out at 60px, which fills a laptop screen with
four words; here it tops out at 46px, section padding went from 96px to 64px,
and the heading, figure and lead sizes came down with them. That puts roughly a
third more on the first screen, which is what a buyer who came for a number
wants. The proportions are still the parent's — everything moved together.

A thin utility bar above the nav carries the phone number, the email and the
trade line. The parent has no equivalent; it is the most recognisable piece of
furniture on a trade supplier's site and a buyer should not have to scroll for
a phone number.

One deliberate deviation from the parent: its labels are tracked uppercase mono.
The brief rules sentence case throughout, and the brief wins on content rules,
so the same mono labels are set in sentence case with looser tracking. This is
noted at the bottom of `tokens.css`.

## Content rules

- No pH guarantees. Aragonite supports alkalinity; it does not hold pH at a
  fixed value. The footer, the home page and the about page say this in
  those words.
- Specs are typical values; the published lot analysis governs. The footer
  carries this on every page.
- Each grade page says plainly where that grade is the wrong choice, in the
  third block of its fit section.
- Sentence case throughout.
- Prices are wholesale, per bag, FOB Stockton, before freight, and every page
  that shows one says so. Suggested shelf prices are labelled a margin
  reference and explicitly not a condition of sale.

## Hosting

Static. Every link is a relative `.html` path, so the site works from a
subdirectory or the root of any host. The two data files are fetched over
HTTP; opening a page from the file system disables the lot lookup and the
runtime density refresh (the calculator still works from the values in the
markup). If the host rewrites `/grade-fine` to `/grade-fine.html` (Vercel
`cleanUrls`, Netlify pretty URLs), the canonical tags in
`templates/partials/head.html` and `sitemap.xml` should drop the extension.
