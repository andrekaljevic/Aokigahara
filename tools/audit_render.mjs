// Portable headless audit renderer for the Aokigahara viewer (fixed cameras, deterministic frames).
// Derived from harness/shoot.mjs (the original session harness, kept unmodified) but takes a base URL
// instead of assuming a server on port 8000 rooted at /home/claude/aoki.
//
// Usage: node tools/audit_render.mjs <baseUrl> <outDir> <cams.json> [width] [height]
//   e.g.  python3 launch_viewer.py --port 8765 &   (serves the repo root)
//         node tools/audit_render.mjs http://127.0.0.1:8765/viewer/ renders/audit harness/cams2.json 1280 800
// Requires the `playwright` package (npm i playwright) and a Chromium build; SwiftShader software GL is used.
import {chromium} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const [,, baseUrl, outDir, camFile, w = '1280', h = '800'] = process.argv;
if (!baseUrl || !outDir || !camFile) { console.error('usage: node tools/audit_render.mjs <baseUrl> <outDir> <cams.json> [w] [h]'); process.exit(2); }
const cams = JSON.parse(fs.readFileSync(camFile, 'utf8'));
fs.mkdirSync(outDir, {recursive: true});
const say = (...a) => console.log(a.join(' '));
const browser = await chromium.launch({headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--disable-gpu-sandbox', '--no-sandbox', '--disable-dev-shm-usage']});
const page = await browser.newPage({viewport: {width: +w, height: +h}, deviceScaleFactor: 1});
page.setDefaultTimeout(1200000);
const events = [];
page.on('console', m => { const t = m.type(); if (t === 'error' || t === 'warning') { events.push({type: t, text: m.text().slice(0, 500)}); say('[browser ' + t + ']', m.text().slice(0, 300)); } });
page.on('pageerror', e => { events.push({type: 'pageerror', text: String(e.message).slice(0, 500)}); say('[pageerror]', e.message); });
page.on('requestfailed', r => { events.push({type: 'requestfailed', text: r.url() + ' ' + (r.failure()?.errorText || '')}); say('[requestfailed]', r.url()); });
page.on('response', r => { if (r.status() >= 400) { events.push({type: 'http' + r.status(), text: r.url()}); say('[http ' + r.status() + ']', r.url()); } });
const t0 = Date.now();
await page.goto(baseUrl, {waitUntil: 'load'});
await page.waitForFunction(() => window.__aoki && window.__aoki.ready, null, {timeout: 1200000, polling: 500});
const readySeconds = +((Date.now() - t0) / 1000).toFixed(1);
say('ready in', readySeconds, 's');
await page.evaluate(() => { window.requestAnimationFrame = () => 0; });
await page.waitForTimeout(500);
const results = [];
for (const c of cams) {
  const t1 = Date.now();
  const res = await page.evaluate(async c => {
    const a = window.__aoki; if (c.preset && a.setPreset) a.setPreset(c.preset, c.sun);
    a.setPose(c.x, c.z, c.yaw, c.pitch, c.eye ?? 1.72); if (a.tick) a.tick();
    const s = performance.now(); a.render(); const ms = performance.now() - s;
    const canvas = document.getElementById('world');
    return {data: canvas.toDataURL('image/png'), ms: Math.round(ms), pos: a.camera.position.toArray().map(v => +v.toFixed(2)), trees: a.trees.length, calls: a.renderer.info.render.calls, tris: a.renderer.info.render.triangles};
  }, c);
  fs.writeFileSync(path.join(outDir, c.name + '.png'), Buffer.from(res.data.split(',')[1], 'base64'));
  delete res.data; res.name = c.name; res.wallSeconds = +((Date.now() - t1) / 1000).toFixed(1); results.push(res);
  say(c.name, JSON.stringify(res));
}
fs.writeFileSync(path.join(outDir, 'audit.json'), JSON.stringify({baseUrl, viewport: [+w, +h], readySeconds, results, events}, null, 1));
await browser.close();
say('done');
