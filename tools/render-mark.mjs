/* Render assets/mark.svg to the PNG sizes the site needs and pack favicon.ico.
 *
 *   node tools/render-mark.mjs
 *
 * Uses Playwright's Chromium, which is the only renderer this project assumes.
 * The mark is authored once in assets/mark.svg; everything else here is
 * derived from it, so the favicon can never drift from the logo.
 */
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const svg = readFileSync(resolve(root, 'assets/mark.svg'), 'utf8');

/* Playwright may be a local dependency or a global install; ESM `import` does
   not consult NODE_PATH, so resolve it by hand and say so plainly if it is
   missing rather than failing with a module-resolution stack trace. */
const require = createRequire(import.meta.url);
let chromium;
for (const id of ['playwright', 'playwright-core', '/opt/node22/lib/node_modules/playwright']) {
  try { ({ chromium } = require(id)); break; } catch { /* try the next one */ }
}
if (!chromium) {
  console.error('Playwright not found. Install it (npm i -D playwright) and try again.');
  process.exit(1);
}

async function render(browser, size) {
  const ctx = await browser.newContext({ viewport: { width: size, height: size }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.setContent(
    `<style>html,body{margin:0;padding:0}svg{display:block;width:${size}px;height:${size}px}</style>${svg}`
  );
  const buf = await page.screenshot({ omitBackground: true });
  await ctx.close();
  return buf;
}

const browser = await chromium.launch();

// Standalone PNGs: favicon fallback, apple touch icon, Open Graph card.
for (const size of [32, 180, 512]) {
  writeFileSync(resolve(root, `assets/mark-${size}.png`), await render(browser, size));
  console.log(`assets/mark-${size}.png`);
}

// favicon.ico, with a PNG per size inside it (Vista and later read PNG in ICO).
const sizes = [16, 32, 48];
const pngs = [];
for (const size of sizes) pngs.push(await render(browser, size));
await browser.close();

const header = Buffer.alloc(6);
header.writeUInt16LE(0, 0);            // reserved
header.writeUInt16LE(1, 2);            // 1 = icon
header.writeUInt16LE(sizes.length, 4); // image count

let offset = 6 + 16 * sizes.length;
const entries = [];
for (let i = 0; i < sizes.length; i++) {
  const e = Buffer.alloc(16);
  e.writeUInt8(sizes[i], 0);           // width  (0 means 256)
  e.writeUInt8(sizes[i], 1);           // height
  e.writeUInt8(0, 2);                  // palette size
  e.writeUInt8(0, 3);                  // reserved
  e.writeUInt16LE(1, 4);               // colour planes
  e.writeUInt16LE(32, 6);              // bits per pixel
  e.writeUInt32LE(pngs[i].length, 8);
  e.writeUInt32LE(offset, 12);
  offset += pngs[i].length;
  entries.push(e);
}
writeFileSync(resolve(root, 'assets/favicon.ico'), Buffer.concat([header, ...entries, ...pngs]));
console.log(`assets/favicon.ico (${sizes.join(', ')})`);
