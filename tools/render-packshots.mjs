/* Rasterise the pack-shot sources in assets/photos/src/*.svg to PNG.
 *
 *   node tools/render-packshots.mjs
 *
 * Chromium is the renderer because the shots use SVG filters — turbulence for
 * the matte grain, gaussian blurs for the folds and the contact shadow — and a
 * static SVG viewer will not composite those the way a browser does. The PNG is
 * what ships; the SVG beside it is the source and is not served.
 */
import { createRequire } from 'module';
import { readFileSync, readdirSync, mkdirSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { fileURLToPath } from 'url';

const require = createRequire('/opt/node22/lib/node_modules/');
let chromium;
for (const id of ['playwright', 'playwright-core', '/opt/node22/lib/node_modules/playwright/index.js']) {
  try { ({ chromium } = require(id)); break; } catch {}
}
if (!chromium) { console.error('playwright not found'); process.exit(1); }

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SRC = join(ROOT, 'assets', 'photos', 'src');
const OUT = join(ROOT, 'assets', 'photos');
mkdirSync(OUT, { recursive: true });

const files = readdirSync(SRC).filter((f) => f.endsWith('.svg')).sort();
const browser = await chromium.launch();
const page = await (await browser.newContext({
  viewport: { width: 1600, height: 1200 },
  deviceScaleFactor: 1,
})).newPage();

for (const f of files) {
  const svg = readFileSync(join(SRC, f), 'utf8');
  await page.setContent(
    `<body style="margin:0;background:#fff">${svg}</body>`,
    { waitUntil: 'load' }
  );
  await page.waitForTimeout(220);
  const el = await page.$('svg');
  // JPEG, not PNG: a white-sweep pack shot is smooth gradient almost
  // everywhere, which PNG stores badly. At quality 88 these come out about a
  // sixth of the size with no visible difference on the page.
  const name = f.replace(/\.svg$/, '.jpg');
  await el.screenshot({ path: join(OUT, name), type: 'jpeg', quality: 88 });
  console.log('wrote assets/photos/' + name);
}
await browser.close();
