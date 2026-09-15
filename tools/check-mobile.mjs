// Check that no table is clipped at phone widths, and that every scrollable
// one can be reached from the keyboard.
//
//     npm install playwright            # not a dependency of the site itself
//     node tools/check-mobile.mjs       # exits non-zero on any failure
//
// This exists because the failure it catches is invisible: `.data-wrap` sets
// `overflow: hidden` to clip its rounded corners and `.table-wrap` sets
// `overflow-x: auto`, both one class deep, so on an element carrying both the
// later rule silently won and reset overflow-x to hidden. The seven-column
// catalogue then rendered 683px of table inside a 348px box on a 390px phone
// with the right-hand columns cut off and no way to scroll to them. Nothing
// about the page looked broken; the columns were simply gone.
//
// Run it after any change to the table CSS, and as part of the pre-launch
// retest at 390 and 430px.
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WIDTHS = [390, 430, 546];
const PAGES = ['index.html', 'products.html', 'wholesale.html',
               'grade-fine.html', 'grade-medium.html', 'grade-coarse.html',
               'about.html', '404.html'];

// Prefer the browser this environment already has over a fresh download.
const launch = process.env.PLAYWRIGHT_CHROMIUM
  ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM }
  : {};

const browser = await chromium.launch(launch);
let failures = 0;
let checked = 0;

for (const width of WIDTHS) {
  const ctx = await browser.newContext({ viewport: { width, height: 900 } });
  const page = await ctx.newPage();

  for (const file of PAGES) {
    await page.goto('file://' + path.join(ROOT, file));

    const wraps = await page.$$eval('.table-wrap', els => els.map(el => {
      const cs = getComputedStyle(el);
      return {
        caption: (el.querySelector('caption')?.textContent || '').trim().slice(0, 40),
        overflowX: cs.overflowX,
        clientWidth: el.clientWidth,
        scrollWidth: el.scrollWidth,
        tabindex: el.getAttribute('tabindex'),
        labelledby: el.getAttribute('aria-labelledby'),
        named: (() => {
          const id = el.getAttribute('aria-labelledby');
          return id ? !!el.ownerDocument.getElementById(id) : false;
        })(),
      };
    }));

    for (const w of wraps) {
      checked++;
      const overflows = w.scrollWidth > w.clientWidth + 1;
      const problems = [];
      if (overflows && w.overflowX === 'hidden') {
        problems.push(`clipped: ${w.scrollWidth}px of table in a ${w.clientWidth}px box, overflow-x: hidden`);
      }
      if (w.tabindex !== '0') {
        problems.push('not keyboard focusable (needs tabindex="0")');
      }
      if (!w.named) {
        problems.push(`aria-labelledby="${w.labelledby}" resolves to nothing`);
      }
      if (problems.length) {
        failures++;
        console.log(`FAIL ${width}px ${file} "${w.caption}"`);
        for (const p of problems) console.log(`       ${p}`);
      }
    }

    // Only the table wrappers above may scroll sideways; the page may not.
    const doc = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    if (doc.scrollWidth > doc.clientWidth + 1) {
      failures++;
      console.log(`FAIL ${width}px ${file} page scrolls sideways: `
                  + `${doc.scrollWidth}px in ${doc.clientWidth}px`);
    }
  }

  await ctx.close();
}

await browser.close();
console.log(`${checked} table wrapper(s) across ${WIDTHS.length} widths and `
            + `${PAGES.length} pages — ${failures} failure(s)`);
process.exit(failures ? 1 : 0);
