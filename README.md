# aragonitesand.com

B2B product and lead-generation site for AragoCor Minerals' oolitic aragonite sand. Static HTML rendered from templates, one Vercel serverless function for the quote form, no runtime dependencies.

AragoCorMinerals.com is the corporate, technical and documentation authority; this site covers the sand product line and captures sand inquiries.

## Layout

```
src/pages/*.html        Page sources. Each starts with a <!--meta {...} --> JSON block
                        (title, description, robots, schema, breadcrumb, priority).
src/partials/           layout.html (document shell), header.html, footer.html
src/css/site.css        The stylesheet (copied to assets/site.<hash>.css at build)
src/js/site.js          Navigation, attribution capture, GA4 events, quote form
src/site.json           Site-wide config: URL, company details, GA4 ID, document URLs
src/images/             Full-resolution source images (not deployed)
tools/build.mjs         Renders pages, sitemap.xml and fingerprinted assets to the root
tools/dev-server.mjs    Local preview with clean URLs, redirects and the API function
api/lead.js             POST /api/lead — validation, spam controls, Resend email, webhook
img/                    Responsive AVIF/WebP/JPEG variants used by the pages
docs/                   Public documents (OMRI certificate)
project/                Internal deliverables: audit, claims ledger, inventories,
                        launch checklist, QA results and screenshots (not deployed)
print/                  Legacy bag artwork mockups (not deployed, not used by the site)
vercel.json             Clean URLs, redirects, headers
.vercelignore           Keeps src/, tools/, project/, print/ and docs out of the deploy
```

The HTML files at the root, `sitemap.xml` and `assets/` are **generated**. Edit `src/` and run the build; commit the regenerated output with the source.

## Commands

```
node tools/build.mjs            # render pages, sitemap and assets
node tools/build.mjs --check    # fail if committed output is stale
node tools/dev-server.mjs 8080  # local preview at http://localhost:8080
```

To exercise the form locally without Resend, run the dev server with
`LEAD_WEBHOOK_URL=http://localhost:8080/__webhook`; the stub prints each delivered lead.

## Pages

`/`, `/grades-and-specifications`, `/aquarium-and-aquaculture`, `/commercial-applications`, `/packaging-and-delivery`, `/request-quote`, `/thank-you` (noindex), `/privacy`, `/terms`, `404.html`.

## Content rules

All technical values come from the controlled documents on AragoCorMinerals.com (TDS-OA-001 Rev A and the grade sheets). `project/claims-ledger.md` lists every claim, its source and status, and the claims that must not be published. Do not add a number, certification, performance statement or packaging figure that is not in the ledger with an approved source.

## Lead delivery

Environment variables (Vercel > Project > Settings > Environment Variables):

| Name | Purpose |
|---|---|
| `RESEND_API_KEY` | Resend API key (required for email delivery) |
| `LEAD_TO_EMAIL` | Recipient(s), comma-separated |
| `LEAD_FROM_EMAIL` | Sender on a domain verified in Resend, e.g. `AragoCor Leads <leads@aragonitesand.com>` |
| `LEAD_WEBHOOK_URL` | Optional JSON copy to a CRM, sheet or automation |
| `ALLOWED_ORIGINS` | Optional CORS allow-list for sibling sites |

Undelivered leads are written to the function log on one line prefixed `LEAD_UNDELIVERED`.

## Launch

See `project/launch-checklist.md`. Domain, DNS and production deployment changes require approval.
