// Screenshot one LOD of a tree library GLB and print its per-mesh extents and triangle counts.
//   node tools/preview_library.mjs <baseURL> <lib-path> <lod> <out.png> [w] [h] [sunDeg] [nameFilter,...]
// baseURL must serve the repository root, e.g. http://127.0.0.1:8765/
import {chromium} from 'playwright';
import fs from 'fs';
const [,, base, lib, lod='high', out='preview.png', w='1400', h='900', sun='38', only=''] = process.argv;
const url = new URL('tools/preview_library.html', base.endsWith('/') ? base : base + '/');
url.search = new URLSearchParams({lib, lod, sun, only}).toString();
const browser = await chromium.launch({headless: true, args: ['--use-gl=angle',
  '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist',
  '--no-sandbox', '--disable-dev-shm-usage']});
const page = await browser.newPage({viewport: {width: +w, height: +h}});
page.setDefaultTimeout(300000);
const errors = [];
page.on('console', m => {if (m.type() === 'error') {errors.push(m.text()); console.log('[browser]', m.text().slice(0, 300));}});
page.on('pageerror', e => {errors.push(e.message); console.log('[pageerror]', e.message);});
await page.goto(url.href);
await page.waitForFunction(() => window.__done, null, {timeout: 300000});
const err = await page.evaluate(() => window.__error);
if (err) {console.error('load failed:', err); await browser.close(); process.exit(1);}
const data = await page.evaluate(() => {window.__render(); return document.querySelector('canvas').toDataURL('image/png');});
fs.writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
const stats = await page.evaluate(() => window.__stats);
console.log(JSON.stringify({...stats, consoleErrors: errors.length}, null, 1));
await browser.close();
console.log('saved', out);
