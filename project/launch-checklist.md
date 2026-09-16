# Launch checklist — AragoniteSand.com

Internal document, not deployed. Nothing below that touches the production domain, DNS or the production deployment is to be done without explicit approval.

## A. Launch blockers (all must be closed)

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Correct repository and Vercel project identified | Done for the repo (`jlerner1965/AragoniteSand`, `main`). Vercel project not visible to this session; owner to confirm project name/team and grant access or run the checks in B. | Open |
| 2 | Canonical domain confirmed: apex `https://aragonitesand.com`, `www` → apex 308 | Verified live | Done |
| 3 | Final approved technical data: TDS-OA-001 Rev A, TDS-AG-001, TDS-WT-001 | Used as source of truth | Done |
| 4 | Conflicting specifications reconciled (see `audit.md`) | Done | Done |
| 5 | Grade names and particle ranges: AG-CAL 0.2–0.5 mm, WT-CAL 1–3 mm, Custom 20–325 mesh | Owner to approve that these codes are used on the sand site (instead of "Oolitic fine"/"Medium") | Open |
| 6 | Authentic full-resolution images: grain macro, tank on sand missing; yard / bulk-bag / 50 lb bag authenticity to confirm | Owner | Open |
| 7 | Packaging terminology approved ("bagged", "super sack", "dry bulk") | Owner | Open |
| 8 | Bag and pallet information: intentionally omitted ("confirmed on quotation") | Owner to accept or supply approved figures | Open |
| 9 | MOQ and lead-time language: intentionally omitted | Owner to accept or supply | Open |
| 10 | Form backend connected: `api/lead.js` deployed; env vars to verify | Owner / Vercel | Open |
| 11 | Lead recipient confirmed | Owner (runbook says Jameslerner7@gmail.com) | Open |
| 12 | Successful test lead received | Submit from the preview once env vars are confirmed; confirm inbox receipt | Open |
| 13 | GA4 measurement ID confirmed: `G-LKWW9913VR` | Owner to confirm it is the intended property | Open |
| 14 | Analytics events tested: verified locally (console); verify in GA4 DebugView on the preview | Owner / QA | Partly |
| 15 | Privacy and terms reviewed by the owner | Owner | Open |
| 16 | Domain access available (Cloudflare) | Owner | Open |
| 17 | Production DNS change approved (none required for the domain itself; Resend records are new) | Owner | Open |
| 18 | No unresolved critical accessibility, security or SEO defects | See `qa-results.md` | See QA |
| 19 | Vercel plan: Hobby is non-commercial; upgrade before commercial launch | Owner | Open |
| 20 | Obsolete `aragonite-sand.vercel.app` project: delete or redirect | Owner approval required | Open |

## B. Domain and DNS verification (read-only checks, done 16 Sep 2026)

| Check | Result |
|---|---|
| Registrar | Not determinable from DNS alone; owner to confirm |
| DNS host | Cloudflare (`donna.ns.cloudflare.com`, `fonzie.ns.cloudflare.com`) |
| Apex A | `76.76.21.21` (Vercel) |
| `www` CNAME | `3a51f4b8c12ad131.vercel-dns-017.com` |
| MX | none |
| SPF / DKIM / DMARC | none |
| Verification records | `google-site-verification=3iBGLmlhay0O7p4Afq9wXB2whEK1tEde6uqVMdY88rM` |
| CAA | none |
| SSL | Valid on apex and www (HSTS present) |
| Redirect | www → apex 308; http → https 308 |

Do not change nameservers. Do not remove any existing record.

## C. Pre-launch steps (need owner access or approval)

1. **Vercel**: confirm the project connected to `jlerner1965/AragoniteSand`, production branch `main`. Check `RESEND_API_KEY`, `LEAD_TO_EMAIL`, `LEAD_FROM_EMAIL` exist for Production and Preview. Confirm a preview deployment built for branch `claude/relaxed-bell-5uy6jq` (Vercel adds `X-Robots-Tag: noindex` to preview deployments; `vercel.json` also sets it for every `*.vercel.app` host).
2. **Resend**: add domain `aragonitesand.com`; add the SPF, DKIM (and bounce MX, if provided) records in Cloudflare exactly as given, DNS-only. Set `LEAD_FROM_EMAIL` to a sender on that domain. Optional but recommended: a `_dmarc` TXT (`v=DMARC1; p=none; rua=mailto:...`).
3. **Test lead** from the preview: fill the form with obviously-test values (company "TEST — ignore"), confirm receipt in the recipient inbox, confirm Reply-To is the tester's address, confirm `quote_success` in GA4 DebugView with `site_environment=preview`.
4. **Review** privacy, terms, captions and the grade naming.
5. **Approve** merge of `claude/relaxed-bell-5uy6jq` into `main` (this replaces the production deployment).

## D. Controlled launch (after approval)

1. Merge to `main`; Vercel deploys production.
2. Confirm `https://aragonitesand.com/` serves the new build (title "Aragonite Sand | Commercial Grades and Bulk Supply"); `www` still 308s; `/products.html` 308s to `/grades-and-specifications`; `/thank-you` sends `X-Robots-Tag: noindex`.
3. Confirm `aragonite-sand-uok7.vercel.app` 308s to the apex (host-conditional redirect in `vercel.json`).
4. Submit a second controlled test lead on production; confirm receipt.
5. GA4 Realtime: confirm page views with `site_environment=production` and the `quote_success` key event.
6. Search Console: submit `https://aragonitesand.com/sitemap.xml`; request indexing for `/` and `/grades-and-specifications`; check that legacy URLs report as redirects.
7. Decide on `aragonite-sand.vercel.app`: delete the obsolete project (preferred) or add a redirect. Not done without approval.
8. Upgrade the Vercel plan if commercial-use terms require it.
9. Monitor Vercel function logs for `LEAD_UNDELIVERED` and `Lead delivery failed` for the first week.

## E. Rollback

`main` before this rebuild is commit `4910dd8`. Reverting the merge commit restores the previous single-page site; the `api/lead.js` env var names are unchanged so no configuration rollback is needed.
