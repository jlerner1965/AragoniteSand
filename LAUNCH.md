# aragonitesand.com launch runbook

## Step 1. Put the site on GitHub (no terminal needed)
1. github.com → New repository → name it `aragonitesand` → Private → Create.
2. On the empty repo page click "uploading an existing file".
3. Unzip aragonitesand-site.zip on your computer, select everything inside the folder (not the folder itself), drag it in, click Commit.
4. Send Claude the repo name (e.g. `yourname/aragonitesand`). Claude links it to Vercel and deploys. Every later edit to the repo redeploys automatically.

## Step 2. Paste this into Claude in Chrome (with vercel.com, resend.com and dash.cloudflare.com open and signed in)

> Help me finish launching aragonitesand.com. Stop and ask me before any payment or before deleting anything.
> 1. Vercel, team ARProject, project "aragonitesand": Settings → Environment Variables. Add for Production and Preview:
>    RESEND_API_KEY = (I will paste it myself when you reach this field)
>    LEAD_TO_EMAIL = (optional; leads already default to the owner's inbox in api/lead.js. Set it only to add or change inboxes)
>    LEAD_FROM_EMAIL = AragoCor Leads <leads@aragonitesand.com>
> 2. Vercel project → Settings → Domains: add aragonitesand.com and www.aragonitesand.com. Note the DNS records Vercel asks for.
> 3. Resend → Domains → Add domain aragonitesand.com. Note the DNS records it gives (SPF, DKIM, MX for bounces).
> 4. Cloudflare → aragonitesand.com: delete the existing redirect rule (Rules → Redirect Rules / Page Rules). In DNS, add the Vercel records and the Resend records exactly as shown, with Proxy status set to DNS only (grey cloud) on the Vercel records.
> 5. Back in Resend, click Verify. Back in Vercel, wait for both domains to show Valid Configuration.
> 6. Vercel → Deployments → latest → Redeploy.
> 7. Open https://aragonitesand.com, fill the quote form with test details, submit, and confirm "Request sent." appears. Then check the lead inbox for the lead email and confirm Reply goes to the test email address.

## Step 3. Google (you must be signed in)
- Search Console → Add property → Domain → aragonitesand.com → add the TXT record in Cloudflare → Verify → Sitemaps → submit `sitemap.xml` → URL inspection on the home page → Request indexing.
- Google Analytics → create a GA4 property → copy the Measurement ID (G-…) → in `index.html` set `GA_ID = 'G-…'` → commit on GitHub (auto-redeploys) → in GA4 Admin → Events, mark `generate_lead` as a key event.
- Google Business Profile for the Stockton address, categories "Mineral supplier" and "Aquarium shop", website aragonitesand.com, phone (209) 487-0110.

## Step 4. Before paid traffic
- Upgrade the Vercel team to Pro (Hobby is non-commercial use only).
- Confirm the printed bag matches `print/` and the bag QR code points to https://aragonitesand.com.
- Confirm the 1–3 mm medium grade is available bagged, or remove that row.

## Launch check (all must be true)
- [ ] https://aragonitesand.com loads with a padlock, www redirects to it
- [ ] A test lead arrives in the inbox within a minute, reply-to is the sender
- [ ] Tap-to-call dials (209) 487-0110 on a phone
- [ ] /privacy loads
- [ ] Search Console shows the sitemap as Success
- [ ] GA4 Realtime shows your visit and a generate_lead event after the test submission
