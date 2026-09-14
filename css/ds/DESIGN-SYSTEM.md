# AragoCor Minerals — Design System

The brand, tokens, components and screen recreations behind **aragocorminerals.com**.

## The company

AragoCor Minerals LLC supplies oolitic aragonite from the Great Bahama Bank — one of the
few places on earth where calcium carbonate precipitates as free-rolling spherical grains
(ooids) rather than being crushed out of rock. The material assays at **97.8% CaCO₃**
representative in an **orthorhombic** crystal structure, is **OMRI Listed®** (product
listing avw-23215), and is distributed from Stockton, California. The mineral is sourced
through **Aragosan Minerals Limited** in The Bahamas — the site credits that partner on
every page, and so should anything you build.

Four bulk grades, one deposit: **AG-CAL** (agricultural sand-grade), **GL-CAL** (glass
batch feed), **WT-CAL** (water-treatment media), **PL-CAL** (functional filler). Nine
markets: agriculture, aquarium & aquaculture, energy, construction, glass, environmental
remediation, ground calcium carbonate, water treatment, horticulture.

The brief also names a consumer line — **Aragonite Soil**, with **Aragonite Oasis** as
the residential lawn product. **Deliberately out of scope.** Aragonite Oasis has a locked
name and tagline and nothing else: no logo, no pack design, no product photography, pack
line still open. Building a retail skin now would mean inventing a brand identity rather
than systematizing one, and it would be rebuilt the moment real packaging exists. Two
decisions here keep that skin a config change rather than a fork: colours are consumed
through **semantic roles** (`--surface-*`, `--text-*`, `--action-*`), not literal names,
and **radius is a token** (`--radius-control` / `-media` / `-card`) rather than a
hardcoded value. Reskinning means overriding the role layer, nothing else.

### Sources

Everything here was read from one repository:

- **https://github.com/jlerner1965/aragocor-site** (branch `main`) — the live site, a
  TanStack Start app deployed on Vercel. Key files: `src/components/site/Chrome.tsx`
  (the whole class-based style layer), `public/ds/colors_and_type.css` (palette, type,
  motion, elevation tokens), `src/lib/brand.ts` (legal and contact facts),
  `src/lib/catalog.ts` (verified product and industry catalogue), `src/routes/index.tsx`
  (homepage), `src/lib/site-chrome.ts` (ported header/footer markup).
- `uploads/aragocor-logo.png` — the wordmark, matching `public/assets/aragocor-logo.png`.

Read those repositories directly if you can; the code is the source of truth and will
tell you more than this summary. `src/components/ui/` in that repo is an untouched
shadcn/Radix scaffold that the site does not use — ignore it. The real design system is
the `ar-*` class layer in `Chrome.tsx`, which is what this project reproduces.

See `github.md` for sync metadata.

---

## Content fundamentals

**The voice is a supplier's, not a marketer's.** Flat, technical, unhedged. It states
what is measured and names what is not.

- **Second person for the reader, first-person plural for the company.** "Tell us the
  spec and the dock." "We come back with a delivered number." Never "I".
- **Sentence case everywhere** — headings, buttons, labels, nav. The only uppercase is
  mono eyebrows and footer column titles, and those are uppercased by CSS, not typed.
- **Headings are complete sentences and usually end in a full stop.** "From the sea to
  industry." "One deposit. Four bulk grades." "Nine markets, one mineral." "Tell us the
  spec and the dock." Short, declarative, often two clauses split by a period.
- **Buttons name the action and its object.** "Get a delivered bulk quote", "Request a
  technical evaluation pack", "Explore water treatment". Never "Submit", "Learn more",
  or "Click here".
- **Every number carries its caveat.** "97.8% **representative**", "Fe₂O₃ **≤** 0.04%",
  "Representative values, technical data sheet Rev 2026.1. Lot-specific values are given
  on the certificate of analysis for the shipment supplied."
- **Unverified facts are printed as gaps, not guesses.** The codebase has a literal
  constant for it: `TBC = "Confirm with our supply team"`. Minimum order quantity, lead
  time and Incoterms are all unconfirmed and the site says so. Do not fill these in.
- **Regulated claims are fenced.** OMRI is always "OMRI Listed®" with the listing ID and
  the disclaimer that listing reviews the input, not the buyer's operation. The repo
  explicitly forbids the phrase "carbon negative" until a third-party lifecycle
  assessment is published; the approved processing line is "No kiln. No calcination.
  Less processing than conventional calcined lime."
- **Honest negatives are a feature.** Where no grade fits, the industry card says
  "Technical consultation" and the copy reads: "or an honest 'technical consultation
  required' where we have no verified single-grade fit."
- **Occasional dry wit, never a joke.** "Buffers, not blasts." "Methods cited, numbers
  shipped — no proprietary asterisks." "Nine markets it walks into." "That page has
  drifted off the bank." One per page at most.
- **No emoji. Ever.** None appear anywhere in the repository.
- Em dashes are used sparingly, mid-sentence. The tagline set is
  "Bahamas-born · Ocean-formed · Industry-trusted" and
  "AragoCor Minerals · Engineered by nature" — middots, not slashes.

---

## Visual foundations

**Colour.** Two layers. The **palette layer** holds the literal marine colours; the
**role layer** (`--surface-page`, `--surface-card`, `--surface-inverse`, `--text-heading`,
`--text-body`, `--action-primary`, `--accent-warm`, …) is the API you build against.
Reference a literal only when you genuinely mean that colour. A cool marine palette on warm paper. `--ink #0E3540` is the brand's near-black
teal and does most of the work: type, footers, ink panels, CTA fills. `--tide #526A70`
is the interactive/secondary tone (hover fill, focus ring, link colour). `--shore
#7C97A0` appears only in gradients. `--sand #D7C59C` is the single warm accent — one
section band per page at most, plus the hover state on bone buttons. `--bone #F7F4ED` is
the page background; `--paper #FFFFFF` is every card. `--root/--leaf #49613C` is reserved
for agronomic affirmation: check marks and the "No kiln" figure. The site header is
`#0d141c`, a shade darker than ink, so chrome reads as chrome. Beyond that, tints are
never new hues — the `--ink-04 … --ink-80` scale supplies every hairline, tint and scrim,
and the `--bone-55 … --bone-92` scale every text weight on dark surfaces.

**Type.** Three families, strictly divided. Source Serif 4 at 600 is the only display
voice — 84px hero, 64/44/38px sections, 24/21/20px card titles, always with negative
tracking (−0.02em to −0.01em) and tight leading (1.0–1.18). Geist carries all body text
at 400/500/600 — 19px hero lead, 15px body, 13.5px captions, 1.55–1.65 leading. JetBrains
Mono is the labelling face: 12px 0.12em uppercase eyebrows, 11px footer column titles,
11.5px table column heads, 12.5px card meta and grade codes. Nothing else. A sans-serif
heading or a serif button is off-brand.

**Backgrounds and imagery.** Real photography only — turquoise Bahamian water, macro
aragonite grains, crops, glass, construction. Warm-to-cool, high-key, no grain filter, no
duotone. Images are always subordinated to type: the homepage hero stacks a 105° blue
wash (`rgba(32,84,140,.66)` → `rgba(150,196,232,.10)`) over the photo plus a
bottom-weighted deepening; interior heroes drop the photo to 24–26% opacity behind flat
ink; tiles carry a 5%→68% bottom scrim that deepens to 78% on hover. The one texture in
the system is the **ooid speckle** — a 3px repeating radial gradient at 12% opacity in
overlay blend, a literal nod to the spherical grains. Gradients are otherwise limited to
these scrims and one radial sustainability card; there are no decorative purple or
rainbow gradients anywhere.

**Cards and borders.** A card is paper with a 1px `--border` hairline and an 8px radius —
flat by default. Only the homepage documentation row is elevated, and elevation is a
two-layer ink shadow: `--shadow-1` at rest → `--shadow-2` on hover with the border
darkening to `--ink-20`. `--shadow-3` is reserved for the lifted technical data sheet.
No coloured left borders, no glow, no inner shadows.

**Radii.** 4px for controls (buttons, fields), 6px for images inside cards, 8px for cards,
panels and tables, 50% for spec medallions. Nothing is pill-shaped.

**Layout.** One shell: 1440px max, `clamp(20px, 4.5vw, 56px)` gutters (the ported static
pages use a flat 40px). Vertical rhythm is 96 / 72 / 56px. Grids are `ar-grid-2` (18px
gap), `ar-grid-3` (20px), `ar-split` (1.1fr/1fr, 40px). Everything collapses to one column
at 900px. The header is the only fixed element — `position: sticky; top: 0; z-index: 50`.

**Motion.** One curve, `--ease-tide: cubic-bezier(0.22, 1, 0.36, 1)`, at 220ms for colour
and transform. The only entrance animation on the site is the hero's 600ms `revealUp`
(10px rise + fade), used once per page. Nothing else fades in on scroll.

**Hover.** Colour shifts, never lifts or scales. Primary buttons go ink → tide; bone
buttons go bone → sand; outline buttons invert to ink; boneline buttons fill to 8% bone.
Nav links go 85% → 100% bone. Cards deepen their shadow and border. Arrows slide 4px
right — that nudge is the brand's signature affordance and appears on every "keep going"
link.

**Press.** `transform: scale(0.98)` at 120ms (0.97 on the ported pages). No colour change
on press.

**Focus.** `3px solid var(--tide)` at 3px offset, switching to sand on bone-filled buttons
so it stays visible. Fields get a tide border plus a 3px `rgba(46,93,110,.18)` halo.

**Transparency and blur.** Transparency is used constantly (every scrim and text tone is
an alpha of ink or bone); **blur is used nowhere.** There is no frosted glass in this
brand. Protection for type over imagery is always a gradient scrim, never a capsule or a
backdrop-filter.

---

## Iconography

There is no icon font, no sprite sheet and no icon library in the repository. Icons are
**inline SVG paths written directly into the markup**, all on a 24×24 viewBox, all drawn
with `currentColor` at **1.5 stroke weight**, unfilled — with one exception, the ooid
cluster, which is filled circles.

The complete set the product uses, reproduced verbatim in `components/core/Icon.jsx`:

| Glyph | Where it appears |
| --- | --- |
| `arrow-right` | every CTA, every "keep going" link, every tile — by far the most used |
| `pin`, `phone`, `mail` | footer and contact block |
| `doc` | document-library rows |
| `check` | benefit lists, drawn in `--leaf` green |
| `cube` | crystal-system spec medallion |
| `ooids` | particle-size spec medallion (filled) |

Rendered at 15, 16, 18 or 22px. Two unicode characters serve as UI glyphs: `☰` / `✕` for
the mobile nav toggle, and `·` as a separator in taglines and meta lines. **No emoji.**

If a design needs a glyph outside this set, flag it rather than inventing one — the
nearest CDN match would be Lucide (same 24px box, same 1.5 stroke, same rounded caps),
but nothing in this system currently depends on it.

---

## Index

```
styles.css              the one file consumers link — @import list only
tokens/                 colors · typography · spacing · radius · elevation · motion · fonts
patterns/               base · layout · buttons · cards · data · forms (the ar-* class layer)
components/             React primitives, grouped by concern
guidelines/             foundation specimen cards
ui_kits/website/        click-through recreation of the marketing site (7 screens)
ui_kits/data-sheet/     Rev 2026.1 technical data sheet, print-ready
assets/                 logos and photography copied from the repo
thumbnail.html          project tile
github.md               source repo + sync record
SKILL.md                Agent Skills entry point
```

### Components

**core/** — `Button`, `Card`, `Eyebrow`, `Heading`, `Icon`, `MediaCard`
**content/** — `Claim`, `ClaimCaveat`, `ClaimText`, `ClaimTBC`
**data/** — `SpecCallout`, `SpecTable`, `StatStrip`
**forms/** — `Field`
**site/** — `CtaBanner`, `FaqItem`, `Hero`, `IndustryTile`, `ProcessSteps`, `SiteFooter`,
`SiteHeader`

Each has a sibling `.d.ts` (props contract) and `.prompt.md` (what, when, example).

**Inventory note.** The source defines its component vocabulary as CSS classes rather
than React components (`.btn-ar`, `.ar-card`, `.ar-card-media`, `.ar-table`, `.fld`,
`.ind-card`, `.ar-eyebrow`, `.ar-h1/2/3`, the stat strip, the spec medallion, the process
row, `details.ar-card`) plus three real components (`SiteHeader`, `SiteFooter`,
`PageSections`). Each component above maps to one of those. Nothing was added that the
product does not already draw.

**Intentional additions.** Three:
- `Icon` — the eight inline SVG paths, so nobody redraws them by hand.
- `Hero` — the homepage image hero and the interior ink band, which the routes repeat
  verbatim on six pages.
- `Claim` — the evidence-tier guardrail. The rule already exists in the source as code
  (`TBC`, `PROCESSING_CLAIM`, the `cleanSpecs`/`cleanFaqs` filters); this makes it
  visible in design work.

---

## Claim tiers

Every factual statement about the material belongs to one of four tiers, and the tier
decides how it may be typeset — or whether it ships at all. Styles in
`patterns/claims.css`, components in `components/content/`.

| Tier | What it covers | How it ships |
| --- | --- | --- |
| **verified** | Published, method-cited, third-party backed — "OMRI Listed®, product listing avw-23215" | Plain |
| **representative** | True of the deposit, varies by lot — every number on the data sheet | Plain **plus** `ClaimCaveat` |
| **hold** | No data yet: carbon, sequestration, soil fertility, yield. Also all commercial terms (MOQ, lead time, capacity, Incoterms) | `ClaimTBC` — "Confirm with our supply team" — or omitted |
| **prohibited** | "Carbon negative", "climate positive", "carbon sequestering", anything implying the buyer's operation is organically certified | Never |

The approved processing line is fixed: **"No kiln. No calcination. Less processing than
conventional calcined lime."** That is the whole claim. Competitors in this category run
"climate positive" language; drifting toward it is the specific failure this system exists
to prevent.

`ClaimText` renders held copy highlighted and prohibited copy struck through — for
mockups and review artefacts only. If either treatment reaches a live page, that is the
bug, not the style.

### Assets

`assets/aragocor-logo.png` (wordmark), `assets/aragosan-logo-v2.png` (sourcing credit),
`hero-ocean.webp`, `aragonite-macro.webp`, nine `ind-*.webp` industry photos,
`about-origin.jpg`, `process-qc.jpg`, `carbon-vitality.jpg`, `contact-droplet.jpg`,
`industries-platform.jpg`, `favicon.ico`.

### Fonts

**Self-hosted, no CDN dependency.** All three families are SIL Open Font License 1.1 —
nothing to buy, nothing to clear. `.woff2` files sit in `assets/fonts/` with their OFL
text; desktop `.otf`/`.ttf` for print work sit in `assets/fonts/desktop/`. The upstream
site still requests them from `fonts.googleapis.com`; this system does not, which is what
makes print data sheets and fixed-size social graphics export reliably.

| Family | Weights | Source |
| --- | --- | --- |
| Source Serif 4 | 600, 400 | adobe-fonts/source-serif @ release |
| Geist | 400, 500, 600 | vercel/geist-font @ main |
| JetBrains Mono | 400, 500 | JetBrains/JetBrainsMono @ master |

Adding a weight means adding a download; omitting one the design sets makes the browser
synthesise it. Check `tokens/fonts.css` before setting a new `font-weight`.
