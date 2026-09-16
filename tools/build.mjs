// Zero-dependency page builder.
//
//   node tools/build.mjs          render src/pages/*.html to the repo root
//   node tools/build.mjs --check  fail if the committed output is stale
//
// Each page starts with a JSON block:  <!--meta { ... } -->
// Partials live in src/partials and are included with {{> name}}.
// {{key}} inserts an HTML-escaped value from the page meta (or site config);
// {{{key}}} inserts it raw. Unknown keys fail the build.

import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync, copyFileSync, statSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const check = process.argv.includes('--check');

const site = JSON.parse(readFileSync(join(root, 'src/site.json'), 'utf8'));

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const partials = {};
for (const f of readdirSync(join(root, 'src/partials'))) {
  partials[basename(f, '.html')] = readFileSync(join(root, 'src/partials', f), 'utf8');
}

// Asset fingerprints so the CSS and JS can be cached hard and still update.
function fingerprint(rel) {
  const h = createHash('sha1').update(readFileSync(join(root, rel))).digest('hex').slice(0, 8);
  return h;
}
const cssHash = fingerprint('src/css/site.css');
const jsHash = fingerprint('src/js/site.js');
mkdirSync(join(root, 'assets'), { recursive: true });
const cssOut = `assets/site.${cssHash}.css`;
const jsOut = `assets/site.${jsHash}.js`;

function render(tpl, ctx, page) {
  // partials first, so they can use the page context
  tpl = tpl.replace(/\{\{>\s*([\w-]+)\s*\}\}/g, (_, name) => {
    if (!partials[name]) throw new Error(`${page}: unknown partial "${name}"`);
    return render(partials[name], ctx, page);
  });
  // conditionals: {{#if key}}...{{/if}}
  tpl = tpl.replace(/\{\{#if\s+([\w.]+)\s*\}\}([\s\S]*?)\{\{\/if\}\}/g, (_, key, body) => (lookup(ctx, key) ? render(body, ctx, page) : ''));
  tpl = tpl.replace(/\{\{\{\s*([\w.]+)\s*\}\}\}/g, (_, key) => {
    const v = lookup(ctx, key);
    if (v === undefined) throw new Error(`${page}: unknown key "${key}"`);
    return String(v);
  });
  tpl = tpl.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (_, key) => {
    const v = lookup(ctx, key);
    if (v === undefined) throw new Error(`${page}: unknown key "${key}"`);
    return esc(v);
  });
  return tpl;
}
function lookup(ctx, key) {
  return key.split('.').reduce((o, k) => (o == null ? undefined : o[k]), ctx);
}

const pages = readdirSync(join(root, 'src/pages')).filter(f => f.endsWith('.html'));
const outputs = [];
const sitemap = [];

for (const f of pages) {
  const src = readFileSync(join(root, 'src/pages', f), 'utf8');
  const m = src.match(/^<!--meta\s*([\s\S]*?)-->\s*/);
  if (!m) throw new Error(`${f}: missing <!--meta {...} --> block`);
  const meta = JSON.parse(m[1]);
  const body = src.slice(m[0].length);
  const path = meta.path ?? ('/' + basename(f, '.html'));
  const canonical = site.url + (path === '/' ? '/' : path);
  const ctx = {
    site,
    ...meta,
    path,
    canonical,
    css: '/' + cssOut,
    js: '/' + jsOut,
    year: new Date().getFullYear(),
    robots: meta.robots ?? 'index, follow, max-image-preview:large',
    og_image: site.url + (meta.og_image ?? site.og_image),
    og_type: meta.og_type ?? 'website',
    schema: meta.schema ? JSON.stringify(expandIds(meta.schema, site.url), null, 1) : '',
    nav: site.nav.map(n => ({ ...n, active: n.href === path })),
    breadcrumb: meta.breadcrumb ? renderBreadcrumb(meta.breadcrumb, site.url, meta.title_short ?? meta.h1) : '',
  };
  ctx.body = render(body, ctx, f);
  const html = render(partials.layout, ctx, f);
  const outName = path === '/' ? 'index.html' : (meta.out ?? path.slice(1) + '.html');
  outputs.push({ file: outName, html });
  if (!/noindex/.test(ctx.robots) && !meta.exclude_from_sitemap) sitemap.push({ loc: canonical, lastmod: meta.lastmod ?? site.lastmod, priority: meta.priority ?? '0.7' });
}

function expandIds(obj, base) {
  // Lets page schema use "@id": "#organization" style short ids.
  return JSON.parse(JSON.stringify(obj).replaceAll('"@id":"#', `"@id":"${base}/#`).replaceAll('"@id":"/', `"@id":"${base}/`));
}
function renderBreadcrumb(items, base, current) {
  const all = [{ name: 'Home', href: '/' }, ...items, { name: current }];
  const html = `<nav class="crumbs" aria-label="Breadcrumb"><ol>${all.map((c, i) => c.href ? `<li><a href="${c.href}">${esc(c.name)}</a></li>` : `<li aria-current="page">${esc(c.name)}</li>`).join('')}</ol></nav>`;
  const ld = { '@context': 'https://schema.org', '@type': 'BreadcrumbList', itemListElement: all.map((c, i) => ({ '@type': 'ListItem', position: i + 1, name: c.name, ...(c.href ? { item: base + (c.href === '/' ? '/' : c.href) } : {}) })) };
  return { html, ld: JSON.stringify(ld) };
}

// sitemap and robots
const sm = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${sitemap.sort((a, b) => (a.loc === site.url + '/' ? -1 : b.loc === site.url + '/' ? 1 : a.loc.localeCompare(b.loc))).map(u => `  <url><loc>${u.loc}</loc><lastmod>${u.lastmod}</lastmod><priority>${u.priority}</priority></url>`).join('\n')}\n</urlset>\n`;
outputs.push({ file: 'sitemap.xml', html: sm });

// static assets
const assetFiles = [
  { from: 'src/css/site.css', to: cssOut },
  { from: 'src/js/site.js', to: jsOut },
];

let stale = [];
for (const o of outputs) {
  const dest = join(root, o.file);
  if (check) {
    if (!existsSync(dest) || readFileSync(dest, 'utf8') !== o.html) stale.push(o.file);
  } else {
    writeFileSync(dest, o.html);
  }
}
for (const a of assetFiles) {
  const dest = join(root, a.to);
  if (check) {
    if (!existsSync(dest) || readFileSync(dest, 'utf8') !== readFileSync(join(root, a.from), 'utf8')) stale.push(a.to);
  } else {
    // remove older fingerprints of the same asset
    for (const f of readdirSync(join(root, 'assets'))) {
      if (f.startsWith('site.') && f.endsWith(a.to.endsWith('.css') ? '.css' : '.js') && 'assets/' + f !== a.to) {
        try { (await import('node:fs')).unlinkSync(join(root, 'assets', f)); } catch {}
      }
    }
    copyFileSync(join(root, a.from), dest);
  }
}

if (check) {
  if (stale.length) { console.error('Stale build output:\n  ' + stale.join('\n  ') + '\nRun: node tools/build.mjs'); process.exit(1); }
  console.log('Build output is current.');
} else {
  console.log(`Rendered ${outputs.length - 1} pages + sitemap; assets ${cssOut}, ${jsOut}`);
}
