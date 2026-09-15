# aragonitesand.com

Static site + one serverless function. Deploys to Vercel with zero build step.

Start with **LAUNCH.md** — it is the step-by-step runbook, including a ready-to-paste prompt for Claude in Chrome.

## Launch checklist

1. **Confirm product facts** in `index.html`
   - Grades now match TDS-OA-001: Oolitic fine 0.2–0.5 mm, Medium 1–3 mm (WT-CAL cut), Custom 20–325 mesh. Confirm the medium grade is available bagged.
   - The hero shows the aquarium-facing bag front (`img/bag-50lb.jpg`). The print handoff is in `print/`: `bag-front-reef-mockup.png` and `reef-benefit-row.svg` (vector row for your bag printer to drop into the original artwork). Confirm the printed bag matches before retail shipments.
   - 50 lb bag back: `print/bag-back-50lb-reef-mockup.png`. Soil benefits and lawn/potting use rates replaced with reef benefits and a Reef & Aquarium Guide (bags per tank, coverage, bed depth, rinsing, storage). Contact block is AragoCor Minerals, (209) 487-0110, info@aragocorminerals.com. The sack's mislabeled 2-ton load specs are gone from the 50 lb bag.
   - Replacement panels for the printer: `print/panel-reef-benefits.*` and `print/panel-reef-use-guide.*` (PNG plus editable HTML source).
   - 2-ton sack back: `print/sack-back-contact-mockup.png` (contact block only; sack stays general-purpose).
   - Point the bag QR code at https://aragonitesand.com for reef bags.
   - "Reply within one business day" promise in the form confirmation
   - Photos in use: 50 lb bag render (hero), 2-ton sack render (wholesale), Stockton stockpile (origin band). Add the super-sack-on-pallet and yard photos to the wholesale section if wanted
2. **Lead delivery** — Vercel > Project > Settings > Environment Variables
   - `RESEND_API_KEY` — from resend.com (free tier is fine to start)
   - `LEAD_TO_EMAIL` — `Jameslerner7@gmail.com` (add more inboxes comma-separated)
   - `LEAD_FROM_EMAIL` — after verifying aragonitesand.com in Resend, e.g. `AragoCor Leads <leads@aragonitesand.com>`
   - `LEAD_WEBHOOK_URL` — optional: Zapier/Make/Sheets/CRM endpoint to log every lead
   - `ALLOWED_ORIGINS` — optional: lets the other AragoCor sites post to this same endpoint
3. **Email deliverability** — in Resend, add aragonitesand.com and copy its SPF/DKIM records into Cloudflare DNS. Until that's done, leads send from `onboarding@resend.dev`, which only delivers to the Resend account owner's address.
4. **Domain** — add `aragonitesand.com` (and `www`) to the Vercel project. In Cloudflare, point the records at Vercel and set them to **DNS only** (grey cloud). Remove the old redirect rule.
5. **Search** — verify the domain in Google Search Console, submit `https://aragonitesand.com/sitemap.xml`, and paste a GA4 tag where the comment in `index.html` marks it.
6. **Social preview** — `/og.jpg` is included (stockpile photo). Swap for a bag shot if preferred.
7. **Test** — submit the form once from the live site and confirm the email arrives with reply-to set to the sender.

## Files

- `index.html` — the whole site (inline CSS/JS, JSON-LD for Organization, Product and FAQ)
- `api/lead.js` — form endpoint: validation, honeypot, rate limit, Resend email, optional webhook
- `vercel.json` — clean URLs and security headers
- `img/` — bag, sack and stockpile photos; `og.jpg` — social preview
- `privacy.html` — privacy notice (linked from the form and footer)
- `robots.txt`, `sitemap.xml`

## Local preview

`npx vercel dev` (or just open `index.html`; the form needs the function to send).
