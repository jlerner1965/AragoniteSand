# QA results — AragoniteSand.com rebuild

Run 16 September 2026 against the local preview (`node tools/dev-server.mjs 8080`, `LEAD_WEBHOOK_URL` pointed at the built-in `/__webhook` stub) in headless Chromium 1194 via Playwright 1.56. Screenshots are in `project/qa/screenshots/` (375 px and 1440 px, full page, every public page).

## Build and tests

| Check | Result |
|---|---|
| `node tools/build.mjs` | 10 pages + sitemap rendered; fingerprinted CSS/JS in `assets/` |
| `node tools/build.mjs --check` | Build output is current |
| `node --check api/lead.js`, `src/js/site.js` | pass |
| `vercel.json`, `site.webmanifest` parse | pass |
| `sitemap.xml` well-formed, 8 URLs (thank-you and 404 excluded) | pass |
| JSON-LD on every page parses; one `<h1>` per page; no unrendered template tokens | pass |

## Responsive (widths 320, 375, 768, 1024, 1440, 1920 × 10 routes)

| Check | Result |
|---|---|
| Horizontal overflow (`scrollWidth − clientWidth`) | 0 px on every route at every width (an earlier run found 155–411 px overflow from tables inside grid columns; fixed with `minmax(0,1fr)` / `min-width:0`) |
| Console errors / page errors / failed requests | none on any route (the 404 route logs the expected 404 for its own URL) |
| Mobile menu (320, 375, 768): opens, `aria-expanded`, Escape closes and returns focus | pass |
| Desktop nav fits on one line at 1024–1920 | pass (Home link is hidden on desktop; the brand links home) |
| Images: `width`/`height` on every `<img>`, alt on every image, every lazy image loads on scroll | pass (verified with a scroll-through on home and packaging) |
| Title, meta description, canonical, robots on every route | pass; `/thank-you` and `404.html` are `noindex` |

## Links

All internal links on every page at 1440 px were requested: no 4xx/5xx except the deliberate `/does-not-exist` test route. External links resolve to AragoCorMinerals.com pages that exist (`/`, `/products`, `/resources`, `/technical-data-sheet`, `/about`, `/industries`, `/industries/water-treatment`, `/industries/turf`) and to the five PDFs on that site, all of which downloaded during discovery.

## Keyboard and focus

Tab order on the home page: skip link → brand → four nav links → header CTA → hero CTAs → in-page links. Every focused element shows a 3 px solid outline. Skip link becomes visible on focus. Form status region receives focus after a validation failure.

## Accessibility (axe-core 4.x, WCAG 2.1 A/AA + best practice, 375 and 1440 px)

Initial run: 3 finding types (scrollable table regions not focusable; heading order in the quote-page aside and the 404 cards). All fixed (`tabindex="0"`/`role="region"` on table scrollers; heading levels corrected). Lighthouse accessibility 100 on every audited page after the fix. Colour contrast: all text/background pairs pass AA (navy on bone, white on navy, muted `#4B5F66` on white ≥ 7:1).

## Form

| Step | Result |
|---|---|
| Open `/request-quote?grade=WT-CAL&intent=sample&utm_source=test…` | grade preselected, sample = Yes, hidden UTM and landing-page fields populated |
| Submit empty | 12 fields marked invalid with inline messages; summary with anchor links; focus moved to the summary; `quote_error{validation}` fired |
| Fill and resubmit | data preserved; `quote_submit` → backend `200 {ok:true}` → `quote_success` and `sample_request` fired → redirect to `/thank-you`; thank-you page shows the request type |
| Backend received | full record via webhook stub (fields, attribution, `spam_status: clean`, IP, UA, timestamp) |
| Backend without delivery configured | `503` → client shows "could not be sent" with the entry preserved, a prefilled `mailto:` and a copy box; `quote_error{delivery}` fired; no redirect |
| Direct API tests | valid → 200; honeypot → silent 200, not delivered; submitted < 4 s after open → delivered, flagged `too_fast`, subject prefixed `[CHECK]`; bad email → 400 with field error; GET → 405; 6th request in 10 min → 429 |
| Script injection in message | escaped in the email HTML (`esc()`); control characters stripped |

Not tested here: actual Resend delivery to the recipient inbox (no API key in this environment). See `launch-checklist.md` C.3.

## Analytics events (console capture with `?debug_events=1`)

`quote_start`, `quote_error`, `quote_submit`, `quote_success`, `sample_request` observed with `site_hostname`, `site_environment`, `page_path` and the documented parameters. GA is not loaded on `localhost`; page-level `specification_view` / `packaging_view` and the click handlers were verified by code review and by the same console path.

## Lighthouse 13.4 (headless Chromium, local server)

| Page | Mode | Performance | Accessibility | Best practices | SEO | LCP | CLS |
|---|---|---|---|---|---|---|---|
| `/` | mobile | 97 | 100 | 100 | 100 | 2.6 s | 0 |
| `/grades-and-specifications` | mobile | 98 | 100 | 100 | 100 | 2.4 s | 0 |
| `/request-quote` | mobile | 98 | 100 | 100 | 100 | 2.4 s | 0 |
| `/` | desktop | 100 | 100 | 100 | 100 | 0.6 s | 0 |
| `/grades-and-specifications` | desktop | 100 | 100 | 100 | 100 | 0.6 s | 0.017 |

Before self-hosting the fonts the home page scored 82 on mobile (2.5 s of render-blocking third-party CSS). Remaining advisories: cache headers (the local server sends none; production `vercel.json` sets immutable caching on `/assets/*` and 30 days on `/img/*`) and ~13 KiB of CSS unused on any single page (one shared stylesheet by design).

## Not verifiable from this session

- Vercel preview deployment URL, `X-Robots-Tag` on `*.vercel.app` hosts, the host-conditional redirect from `aragonite-sand-uok7.vercel.app`, and production headers: require the branch to build on Vercel.
- Resend delivery and inbox receipt.
- GA4 DebugView.
- Apex/www behaviour is unchanged by this work and was verified live during discovery (www → apex 308, http → https 308).
