// POST /api/lead
// Receives quote requests from the site form and delivers them by email (Resend).
// Optional: also forwards every lead to a webhook (Zapier, Make, Google Sheets, a CRM).
//
// Environment variables (set in Vercel > Project > Settings > Environment Variables):
//   RESEND_API_KEY     required for email delivery
//   LEAD_TO_EMAIL      where leads go, comma-separated for several inboxes
//   LEAD_FROM_EMAIL    a sender on a domain verified in Resend, e.g. "AragoCor Leads <leads@aragonitesand.com>"
//   LEAD_WEBHOOK_URL   optional, receives the lead as JSON
//   ALLOWED_ORIGINS    optional, comma-separated origins allowed to post here from other sites
//                      e.g. "https://aragocorminerals.com,https://aragonitesoil.com"

const ALLOWED = (process.env.ALLOWED_ORIGINS || '')
  .split(',').map(s => s.trim()).filter(Boolean);

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

function clean(v, max = 500) {
  return String(v ?? '').replace(/[\r\n\t]+/g, ' ').trim().slice(0, max);
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  cors(req, res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ ok: false, error: 'Method not allowed' });

  // Rate limit: 5 submissions per 10 minutes per IP (per warm instance)
  const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  const now = Date.now();
  if (hits.size > 5000) hits.clear();
  const recent = (hits.get(ip) || []).filter(t => now - t < 10 * 60 * 1000);
  if (recent.length >= 5) return res.status(429).json({ ok: false, error: 'Too many requests. Try again later.' });
  hits.set(ip, [...recent, now]);

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = {}; } }
  body = body || {};

  // Honeypot: real people never fill the hidden "website" field
  if (clean(body.website)) return res.status(200).json({ ok: true });

  const lead = {
    name: clean(body.name, 120),
    email: clean(body.email, 200).toLowerCase(),
    phone: clean(body.phone, 60),
    company: clean(body.company, 160),
    buyer_type: clean(body.buyer_type, 80),
    quantity: clean(body.quantity, 80),
    bags: String(parseInt(body.bags, 10) || '').slice(0, 8),
    grade: clean(body.grade, 40),
    destination: clean(body.destination, 120),
    message: String(body.message ?? '').trim().slice(0, 3000),
    calc: clean(body.calc, 300),
    source: clean(body.source, 80) || 'aragonitesand.com',
    page: clean(body.page, 300),
    ip,
    received_at: new Date().toISOString(),
  };

  if (!lead.name || !lead.email || !lead.buyer_type || !lead.quantity) {
    return res.status(400).json({ ok: false, error: 'Missing required fields' });
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(lead.email)) {
    return res.status(400).json({ ok: false, error: 'Invalid email' });
  }

  const tasks = [];

  // 1) Email via Resend
  if (process.env.RESEND_API_KEY && process.env.LEAD_TO_EMAIL) {
    const to = process.env.LEAD_TO_EMAIL.split(',').map(s => s.trim()).filter(Boolean);
    const from = process.env.LEAD_FROM_EMAIL || 'AragoCor Leads <onboarding@resend.dev>';
    const subject = `New quote request: ${lead.buyer_type} · ${lead.bags ? lead.bags + ' bags' : lead.quantity} · ${lead.source}`;
    const rows = [
      ['Name', lead.name], ['Email', lead.email], ['Phone', lead.phone || '—'], ['Company', lead.company || '—'],
      ['Buyer type', lead.buyer_type], ['Quantity', lead.quantity + (lead.bags ? ` (${lead.bags} bags)` : '')], ['Grade', lead.grade || '—'], ['Delivery to', lead.destination || '—'],
      ['Calculator', lead.calc || '—'], ['Source', lead.source], ['Page', lead.page || '—'], ['Received', lead.received_at],
    ];
    const html = `
      <div style="font-family:Arial,sans-serif;font-size:15px;color:#10302F">
        <h2 style="margin:0 0 12px;color:#0E4A4F">New quote request from ${esc(lead.source)}</h2>
        <table cellpadding="6" style="border-collapse:collapse">
          ${rows.map(([k, v]) => `<tr><td style="color:#4F6664;padding-right:14px;vertical-align:top">${esc(k)}</td><td><b>${esc(v)}</b></td></tr>`).join('')}
        </table>
        ${lead.message ? `<p style="margin-top:14px;white-space:pre-wrap;border-left:4px solid #B89A63;padding-left:10px">${esc(lead.message)}</p>` : ''}
        <p style="margin-top:18px;color:#4F6664;font-size:13px">Reply to this email to answer ${esc(lead.name)} directly.</p>
      </div>`;
    const text = rows.map(([k, v]) => `${k}: ${v}`).join('\n') + (lead.message ? `\n\n${lead.message}` : '');

    tasks.push(fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.RESEND_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to, reply_to: lead.email, subject, html, text }),
    }).then(async r => { if (!r.ok) throw new Error(`Resend ${r.status}: ${await r.text()}`); }));
  }

  // 2) Webhook (CRM, sheet, Slack, etc.)
  if (process.env.LEAD_WEBHOOK_URL) {
    tasks.push(fetch(process.env.LEAD_WEBHOOK_URL, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(lead),
    }).then(r => { if (!r.ok) throw new Error(`Webhook ${r.status}`); }));
  }

  if (tasks.length === 0) {
    console.error('Lead received but no delivery configured (set RESEND_API_KEY + LEAD_TO_EMAIL):', lead);
    return res.status(500).json({ ok: false, error: 'Lead delivery is not configured' });
  }

  const results = await Promise.allSettled(tasks);
  const failed = results.filter(r => r.status === 'rejected');
  failed.forEach(f => console.error('Lead delivery failed:', f.reason));

  // Success if at least one channel delivered
  if (failed.length === results.length) {
    return res.status(502).json({ ok: false, error: 'Could not deliver lead' });
  }
  return res.status(200).json({ ok: true });
}
