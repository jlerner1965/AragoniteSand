# Discovery audit — AragoniteSand.com rebuild

Date: 16 September 2026. Internal document, not deployed.

## Repository and deployment

| Item | Finding |
|---|---|
| Repository | `jlerner1965/AragoniteSand` (GitHub). Default and production branch `main`, head `4910dd8` at audit time. Working tree clean; no uncommitted changes. |
| Rebuild branch | `claude/relaxed-bell-5uy6jq`, started from `main` head. |
| Framework | Plain static HTML with inline CSS/JS and one Vercel serverless function (`api/lead.js`). No build step, no npm dependencies, `package.json` only declares `"type": "module"`. |
| Hosting | Vercel. Apex `aragonitesand.com` → A 76.76.21.21 (Vercel). `www` → CNAME `3a51f4b8c12ad131.vercel-dns-017.com`, 308 → apex. HSTS present. |
| Vercel project (current) | Not visible through the Vercel connector in this session: team "ARProject" (`team_YIUQCFkyUZRJ2ARZbiA04PJC`, Hobby plan) lists zero projects, and lookups for `aragonitesand`, `aragonite-sand` and the deployment URL return 404. The project therefore lives under a different Vercel account or team than the connector is authorised for. Runbook (`LAUNCH.md`) names team ARProject, project "aragonitesand". |
| Deployment aliases | `aragonite-sand-uok7.vercel.app` serves byte-identical content (same ETag) to production → current project's `.vercel.app` alias. `aragonite-sand.vercel.app` serves an older multi-page build (last modified 15 Sep 2026 20:59 UTC, with a CSP header the current build does not send, sitemap listing `products.html`, `grade-*.html`, `wholesale.html`, `about.html`) → **obsolete duplicate project**, indexable, with canonical tags pointing at aragonitesand.com. |
| DNS | Nameservers `donna.ns.cloudflare.com`, `fonzie.ns.cloudflare.com` (Cloudflare). TXT: `google-site-verification=3iBG…88rM` (Search Console verified). **No MX, SPF, DKIM, DMARC** on aragonitesand.com; no Resend records (`resend._domainkey`, `send.`). |
| Lead endpoint | `POST /api/lead` live; returns 400 "Missing required fields" on an empty body, so the function is deployed. Whether `RESEND_API_KEY`/`LEAD_TO_EMAIL` are set could not be read (no project access). Runbook recipient: `Jameslerner7@gmail.com`; sender falls back to `onboarding@resend.dev` until the domain is verified in Resend, which only delivers to the Resend account owner. |
| Analytics | GA4 `G-LKWW9913VR` hardcoded in `index.html`; loads `gtag.js`; one custom event `generate_lead` on form success. No hostname dimension, no other events. |
| Search Console | Domain verified (TXT record). Sitemap submission status unknown. |
| Legacy URLs | `/products.html`, `/about.html` etc. 308 → clean URL → 404 on the current domain. Old `.vercel.app` sitemap still lists them. |
| Public folders | `print/` (bag mockups, 5.6 MB) and `docs/` (OMRI certificate) are deployed. `README.md`/`LAUNCH.md` also deployed as static files. |
| Plan | Hobby (non-commercial use). `LAUNCH.md` step 4 notes the Pro upgrade. |

## Page inventory (before)

| URL | Content |
|---|---|
| `/` | Single page: reef-tank hero with bag mockup, analysis strip, "why reef keepers ask for oolitic", yard photo, grades table ("Oolitic fine 0.2–0.5 mm", "Medium 1–3 mm", "Custom"), tank sand calculator, origin band, uses list, wholesale, FAQ (7, hobbyist), quote form (name, email, phone, company, buyer type, quantity, bags, grade, destination, message), footer. |
| `/privacy` | Short privacy notice (noindex). |
| `/robots.txt`, `/sitemap.xml` | Present; sitemap lists only `/`. |
| 404 | Vercel default (no custom page). |

## Assets (before)

| File | Origin | Assessment |
|---|---|---|
| `img/stockpile.jpg` (1600×699) | Committed with the launch build; README calls it "Stockton stockpile" | Real photograph of an aragonite stockpile. Location (Stockton vs. Bahamas) not confirmed; captions on the new site avoid naming the location. Used as hero and social image. |
| `img/bulk-inventory-yard.jpg` (1500×844) | Added by repository owner in commit `7790c45` "Add optimized product and operations photography" | Owner-supplied. Used as yard/dispatch photo. Two other files from the same commit were later removed as illustrations; owner should confirm this one is a photograph. |
| `img/super-sack-pallet.jpg` (760×570) | Same commit; README calls it "2-ton sack render" | Owner-supplied branded bulk-bag image. Used on home and packaging page, captioned "Palletized AragoCor Minerals bulk bag". Confirm it depicts the actual bag specification. |
| `img/bag-50lb.jpg` | Reef-claims bag **mockup** (matches `print/bag-front-reef-mockup.png`; carries "Supports stable pH") | **Removed from the site.** Unprinted design with a prohibited claim. |
| `img/grains-closeup.jpg`, `img/reef-tank-sand.jpg` | Commit `7790c45`, removed in `1e47d42` as "illustrated" | Not used. Reef tank is clearly a render. Grain image may be a real macro; owner to confirm before it is restored. |
| Earlier branch `assets/photos/pack-50lb-front.webp` (430×722) | "AragoCor's own photography, supplied with the design system" | Current printed 50 lb bag (agricultural benefit claims on the artwork). Restored to `src/images/` and used once on the packaging page, captioned as the printed bag. Owner to confirm this is the bag that ships for sand orders. |
| Earlier branch `aragonite-macro.webp`, `hero-ocean.webp`, `process-qc.jpg`, `about-origin.jpg`, `ind-*.webp` | Design-system stock | AI-generated or generic stock. Not used. |
| `img/aragocor-minerals-logo.png` | Parent site logo | Used in footer and home. |
| `docs/omri-certificate-avw-23214.pdf` | OMRI certificate | Kept and linked. |

## Technical-data sources and conflicts

Controlling source: **TDS-OA-001 Rev A (Sep 2026)** and grade sheets TDS-AG-001 / TDS-WT-001 Rev A, published at AragoCorMinerals.com/resources.

| Topic | Conflict found | Resolution |
|---|---|---|
| Grade names | Live page: "Oolitic fine" (0.2–0.5 mm), "Medium" (1–3 mm). Earlier branch: "Fine 0.5–1.0 mm", "Medium 1.0–2.0 mm", "Coarse 2.0–5.0 mm" (invented). TDS: AG-CAL 0.2–0.5 mm, WT-CAL 1–3 mm, Custom 20–325 mesh. | Use TDS codes and ranges. |
| CaCO₃ | Earlier branch 97.8% headline and 94–98.5% range; TB-OA-002 "96–98%"; TDS 96.17% representative. | Publish 96.17% representative (ASTM C 25) only. |
| Sieve data per grade | Earlier branch invented per-grade sieve tables. | Publish only the natural commercial gradation from TDS §5. |
| OMRI code | Earlier data avw-23215; certificate avw-23214. | avw-23214. |
| Moisture | Earlier branch "max 10%"; TDS "5–10% published range". | TDS wording. |
| Density | Live page "roughly 90 lb per cubic foot" — no source. | Omitted. |
| Packaging | Earlier branch: 20 lb bags, 40/60 bags per pallet, 48×40 pallet (guessed). Live page: 50 lb bags, super sacks to 3,000 lb, bags from 1 lb. TDS: bagged from 1 lb, super sack up to 3,000 lb, dry bulk. | TDS wording; counts "confirmed on quotation". |
| Service level | "Reply within one business day". | Omitted. |
| Address, phone, email | Consistent across TDS, parent footer, live page. | Kept. |

## Integrations preserved

- `api/lead.js` delivery pattern (Resend + optional webhook, honeypot, per-instance rate limit, `LEAD_UNDELIVERED` log line). Rewritten for the new field map with server-side field errors, minimum-time and form-version checks.
- Environment variable names unchanged: `RESEND_API_KEY`, `LEAD_TO_EMAIL`, `LEAD_FROM_EMAIL`, `LEAD_WEBHOOK_URL`, `ALLOWED_ORIGINS`.
- GA4 measurement ID.
- Security headers in `vercel.json` (extended with HSTS, cache headers, noindex for `*.vercel.app`).

## Risks to production launch

1. No Vercel project access from this session: environment variables, preview URL and deployment settings cannot be verified or changed here.
2. Lead email deliverability: no Resend domain verification records exist. Until added, leads send from `onboarding@resend.dev` and may only reach the Resend account owner.
3. Obsolete `aragonite-sand.vercel.app` project is indexable and duplicates content; needs removal or a redirect (approval required).
4. Hobby plan is non-commercial.
5. Missing authentic photography (grain macro, tank-on-sand); owner confirmation needed on the yard, bulk-bag and 50 lb bag images.
6. No consent banner for analytics cookies; acceptable for a US B2B site but flagged for review in the privacy notice.
7. Packaging figures (MOQ, lead time, pallet build) unpublished by design; sales must be ready to quote them.
