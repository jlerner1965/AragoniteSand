// Local preview: node tools/dev-server.mjs [port]
// Serves the repo root with Vercel-style clean URLs and mounts api/lead.js.
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, extname, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const port = Number(process.argv[2] || 8080);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.xml': 'application/xml', '.txt': 'text/plain', '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.avif': 'image/avif', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.pdf': 'application/pdf', '.webmanifest': 'application/manifest+json' };
const vercel = JSON.parse(readFileSync(join(root, 'vercel.json'), 'utf8'));
const redirects = vercel.redirects || [];
const { default: lead } = await import(join(root, 'api/lead.js'));

function toRegex(source) {
  return new RegExp('^' + source.replace(/:(\w+)\*/g, '(?<$1>.*)').replace(/:(\w+)/g, '(?<$1>[^/]+)') + '$');
}

createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const p = decodeURIComponent(url.pathname);
  if (p === '/__webhook' && req.method === 'POST') {
    // Local stand-in for LEAD_WEBHOOK_URL: prints the delivered lead.
    let raw = ''; for await (const c of req) raw += c;
    console.log('WEBHOOK RECEIVED ' + raw);
    res.setHeader('Content-Type', 'application/json'); return res.end('{"ok":true}');
  }
  if (p.startsWith('/api/lead')) {
    let raw = '';
    for await (const c of req) raw += c;
    req.body = raw;
    const r = {
      status(c) { res.statusCode = c; return r; },
      setHeader: (k, v) => res.setHeader(k, v),
      json(o) { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); },
      end: (b) => res.end(b),
      redirect(c, l) { res.statusCode = c; res.setHeader('Location', l); res.end(); },
    };
    return lead(req, r);
  }
  for (const rd of redirects) {
    if (rd.has) continue;
    const m = p.match(toRegex(rd.source));
    if (m) { res.statusCode = rd.permanent ? 308 : 307; res.setHeader('Location', rd.destination.replace(/:(\w+)/g, (_, k) => m.groups?.[k] ?? '')); return res.end(); }
  }
  if (p.endsWith('.html') && p !== '/index.html') { res.statusCode = 308; res.setHeader('Location', p.replace(/\.html$/, '')); return res.end(); }
  if (p.endsWith('/') && p !== '/') { res.statusCode = 308; res.setHeader('Location', p.slice(0, -1)); return res.end(); }
  let file = p === '/' ? join(root, 'index.html') : join(root, p);
  if (!existsSync(file) || statSync(file).isDirectory()) file = join(root, p + '.html');
  if (!existsSync(file) || statSync(file).isDirectory()) {
    res.statusCode = 404; res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.end(readFileSync(join(root, '404.html')));
  }
  res.setHeader('Content-Type', types[extname(file)] || 'application/octet-stream');
  res.end(readFileSync(file));
}).listen(port, () => console.log('dev server on http://localhost:' + port));
