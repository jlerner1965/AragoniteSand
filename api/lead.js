// POST /api/lead
// Receives quote, product-detail and sample requests from /request-quote and
// delivers them by email (Resend), with an optional JSON webhook copy.
//
// Environment variables (Vercel > Project > Settings > Environment Variables):
//   RESEND_API_KEY     required for email delivery
//   LEAD_TO_EMAIL      recipient(s), comma-separated
//   LEAD_FROM_EMAIL    sender on a domain verified in Resend,
//                      e.g. "AragoCor Leads <leads@aragonitesand.com>"
//   LEAD_WEBHOOK_URL   optional, receives the lead as JSON (CRM, sheet, Zapier)
//   ALLOWED_ORIGINS    optional, comma-separated origins allowed to post here
//
// Responses are JSON: { ok: true } or { ok: false, error, fields? }.
// A 400 with `fields` maps field names to messages so the client can show them.

const ALLOWED = (process.env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
const FORM_VERSION_PREFIX = '2026-';
const hits = new Map(); // best-effort per-instance rate limit

function cors(req, res) {
  const origin = req.headers.origin;
  if (origin && ALLOWED.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Vary', 'Origin');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  }
}

// Strip control characters (except newline/tab, which `clean` then collapses).
const CONTROL = /[\x00-\x08\x0B\x0C\x0E-\x1F]/g;
function clean(v, max = 300) {
  return String(v ?? '').replace(CONTROL, '').replace(/[\r\n\t]+/g, ' ').trim().slice(0, max);
}
function multiline(v, max = 4000) {
  return String(v ?? '').replace(CONTROL, '').trim().slice(0, max);
}
function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// Field map: name → [label, max length, required]
const FIELDS = [
  ['request_type', 'Request type', 40, false],
  ['first_name', 'First name', 80, true],
  ['last_name', 'Last name', 80, true],
  ['company', 'Company', 160, true],
  ['role', 'Job title or role', 120, true],
  ['email', 'Work email', 200, true],
  ['phone', 'Phone', 60, false],
  ['country', 'Country', 80, true],
  ['region', 'State, province or region', 120, true],
  ['buyer_type', 'Buyer type', 80, true],
  ['application', 'Intended application', 120, true],
  ['grade', 'Grade or particle-size requirement', 120, false],
  ['grade_detail', 'Particle-size detail', 200, false],
  ['quantity', 'Estimated order quantity', 80, true],
  ['annual_volume', 'Estimated annual volume', 80, false],
  ['packaging', 'Preferred packaging', 80, false],
  ['destination', 'Delivery destination or postal code', 160, true],
  ['timing', 'Required timing', 80, false],
  ['documents', 'Required technical documents', 300, false],
  ['sample_request', 'Sample request', 20, false],
  ['private_label', 'Private-label interest', 20, false],
];
const ATTRIBUTION = ['landing_page', 'current_page', 'referrer', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'first_touch', 'last_touch', 'hostname', 'form_version'];

export default async function handler(req, res) {
  cors(req, res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });

  // Rate limit: 5 submissions per 10 minutes per IP (per warm instance)
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  const now = Date.now();
  if (hits.size > 5000) hits.clear();
  const recent = (hits.get(ip) || []).filter(t => now - t < 10 * 60 * 1000);
  if (recent.length >= 5) return res.status(429).json({ ok: false, error: 'Too many requests. Please try again later.' });
  hits.set(ip, [...recent, now]);

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = {}; } }
  body = body || {};

  // Spam controls: honeypot, minimum time on form, form version.
  const spam = [];
  if (clean(body.website) || clean(body.company_url)) spam.push('honeypot');
  const startedAt = parseInt(body.started_at, 10);
  if (!startedAt || now - startedAt < 4000) spam.push('too_fast');
  if (!String(body.form_version || '').startsWith(FORM_VERSION_PREFIX)) spam.push('version');
  if (spam.includes('honeypot')) {
    // Pretend success so bots learn nothing; nothing is delivered.
    return res.status(200).json({ ok: true });
  }

  const lead = {};
  const fields = {};
  for (const [name, label, max, required] of FIELDS) {
    lead[name] = clean(body[name], max);
    if (required && !lead[name]) fields[name] = `${label} is required.`;
  }
  lead.email = lead.email.toLowerCase();
  if (lead.email && !EMAIL_RE.test(lead.email)) fields.email = 'Enter a valid email address.';
  if (String(body.consent) !== 'yes') fields.consent = 'Please confirm you have read the privacy notice.';
  lead.message = multiline(body.message);
  if (Object.keys(fields).length) return res.status(400).json({ ok: false, error: 'Please check the highlighted fields.', fields });

  const attribution = {};
  for (const k of ATTRIBUTION) attribution[k] = clean(body[k], 300);
  const meta = {
    ip,
    user_agent: clean(req.headers['user-agent'], 200),
    received_at: new Date(now).toISOString(),
    spam_status: spam.length ? 'flagged:' + spam.join(',') : 'clean',
    request_host: clean(req.headers.host, 120),
  };
  const record = { ...lead, ...attribution, ...meta };

  const tasks = [];

  // 1) Email via Resend
  if (process.env.RESEND_API_KEY && process.env.LEAD_TO_EMAIL) {
    const to = process.env.LEAD_TO_EMAIL.split(',').map(s => s.trim()).filter(Boolean);
    const from = process.env.LEAD_FROM_EMAIL || 'AragoCor Leads <onboarding@resend.dev>';
    const kind = lead.request_type || 'Quote';
    const flag = spam.length ? '[CHECK] ' : '';
    const subject = `${flag}${kind} request: ${lead.company} · ${lead.application} · ${lead.quantity}`;
    const section = (title, rows) => `
      <h3 style="margin:18px 0 6px;font-size:14px;color:#526A70;text-transform:uppercase;letter-spacing:.06em">${esc(title)}</h3>
      <table cellpadding="5" style="border-collapse:collapse;font-size:15px">
        ${rows.filter(([, v]) => v).map(([k, v]) => `<tr><td style="color:#526A70;padding-right:14px;vertical-align:top;white-space:nowrap">${esc(k)}</td><td><b>${esc(v)}</b></td></tr>`).join('')}
      </table>`;
    const contact = [['Name', `${lead.first_name} ${lead.last_name}`], ['Company', lead.company], ['Role', lead.role], ['Email', lead.email], ['Phone', lead.phone], ['Country', lead.country], ['Region', lead.region], ['Buyer type', lead.buyer_type]];
    const need = [['Request type', kind], ['Application', lead.application], ['Grade', lead.grade], ['Particle-size detail', lead.grade_detail], ['Order quantity', lead.quantity], ['Annual volume', lead.annual_volume], ['Packaging', lead.packaging], ['Destination', lead.destination], ['Timing', lead.timing], ['Documents', lead.documents], ['Sample', lead.sample_request], ['Private label', lead.private_label]];
    const src = [['Landing page', attribution.landing_page], ['Form page', attribution.current_page], ['Referrer', attribution.referrer], ['First touch', attribution.first_touch], ['Last touch', attribution.last_touch], ['UTM', [attribution.utm_source, attribution.utm_medium, attribution.utm_campaign, attribution.utm_content, attribution.utm_term].filter(Boolean).join(' / ')], ['Hostname', attribution.hostname], ['Form version', attribution.form_version], ['Spam status', meta.spam_status], ['Received', meta.received_at], ['IP', ip]];
    const html = `
      <div style="font-family:Arial,sans-serif;font-size:15px;color:#13272E;max-width:720px">
        <h2 style="margin:0 0 4px;color:#0E3540">${esc(kind)} request from aragonitesand.com</h2>
        <p style="margin:0;color:#526A70">${esc(lead.company)} · ${esc(lead.application)} · ${esc(lead.quantity)}</p>
        ${section('Contact', contact)}
        ${section('Requirement', need)}
        ${lead.message ? `<h3 style="margin:18px 0 6px;font-size:14px;color:#526A70;text-transform:uppercase;letter-spacing:.06em">Message</h3><p style="white-space:pre-wrap;border-left:4px solid #D7C59C;padding-left:10px;margin:0">${esc(lead.message)}</p>` : ''}
        ${section('Source', src)}
        <p style="margin-top:18px;color:#526A70;font-size:13px">Reply to this email to answer ${esc(lead.first_name)} directly.</p>
      </div>`;
    const text = [...contact, ...need, ['Message', lead.message], ...src].filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`).join('\n');

    tasks.push(fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to, reply_to: lead.email, subject, html, text }),
    }).then(async r => {
      if (!r.ok) { const e = new Error(`Resend ${r.status}: ${await r.text()}`); e.channel = 'resend'; e.status = r.status; throw e; }
    }));
  }

  // 2) Webhook (CRM, sheet, Slack, etc.)
  if (process.env.LEAD_WEBHOOK_URL) {
    tasks.push(fetch(process.env.LEAD_WEBHOOK_URL, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(record),
    }).then(r => { if (!r.ok) { const e = new Error(`Webhook ${r.status}`); e.channel = 'webhook'; e.status = r.status; throw e; } }));
  }

  if (tasks.length === 0) {
    console.error('LEAD_UNDELIVERED (no delivery configured; set RESEND_API_KEY + LEAD_TO_EMAIL) ' + JSON.stringify(record));
    return res.status(503).json({ ok: false, error: 'Lead delivery is not configured' });
  }

  const results = await Promise.allSettled(tasks);
  const failed = results.filter(r => r.status === 'rejected');
  failed.forEach(f => console.error('Lead delivery failed:', f.reason));

  if (failed.length === results.length) {
    // Every channel refused it. Keep the whole enquiry in the log, on one
    // greppable line, so it can be recovered and answered by hand:
    //   Vercel → Project → Logs → filter: LEAD_UNDELIVERED
    console.error('LEAD_UNDELIVERED ' + JSON.stringify(record));
    const why = failed.map(f => `${f.reason?.channel || 'channel'}:${f.reason?.status || 'error'}`).join(' ');
    return res.status(502).json({ ok: false, error: 'Could not deliver the request', provider: why });
  }
  return res.status(200).json({ ok: true });
}
