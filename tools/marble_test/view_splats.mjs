#!/usr/bin/env node
// Walk-out test for a Gaussian-splat world: render it from its origin and from points further and
// further out, in four headings, headless, so the distance at which it breaks down can be measured.
//
// Usage:
//   node tools/marble_test/view_splats.mjs --splat FILE.spz --out DIR --nm NODE_MODULES_DIR
//        [--dist 0,2,5,10,20] [--eye 0] [--scale 1] [--w 1280 --h 800 --fov 70] [--flip 1] [--frames 4]
//
// --nm must contain three and @sparkjsdev/spark (npm i @sparkjsdev/spark three).
// --scale converts metres to the file's units (1 / metric_scale_factor for Marble worlds) and
// --eye is the camera height in metres above the world origin.
// Uses the Playwright + Chromium pre-installed in the cloud container (WebGL2 on SwiftShader).

import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const splat = path.resolve(arg("splat"));
const out = path.resolve(arg("out"));
const nm = path.resolve(arg("nm"));
const dists = arg("dist", "0,2,5,10,20").split(",").map(Number);
const scale = +arg("scale", "1"), eye = +arg("eye", "0");
const W = +arg("w", "1280"), H = +arg("h", "800"), fov = +arg("fov", "70"), flip = arg("flip", "1"), frames = +arg("frames", "4");
fs.mkdirSync(out, { recursive: true });

const types = { ".js": "text/javascript", ".html": "text/html", ".spz": "application/octet-stream", ".wasm": "application/wasm" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  let f = null;
  if (u === "/" || u === "/index.html") f = path.join(here, "view_splats.html");
  else if (u.startsWith("/nm/")) f = path.join(nm, u.slice(4));
  else if (u.startsWith("/splat/")) f = splat;
  if (!f || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" });
  fs.createReadStream(f).pipe(res);
}).listen(0, "127.0.0.1");
await new Promise((r) => server.on("listening", r));
const port = server.address().port;

// Poses: for each heading, stand at distance d along that heading (camera looks outwards).
const poses = [];
for (const d of dists) for (const yaw of [0, 90, 180, 270]) {
  const r = (yaw * Math.PI) / 180;
  poses.push({ d, yaw, x: -Math.sin(r) * d * scale, y: eye * scale, z: -Math.cos(r) * d * scale, pitch: 0 });
}

const pw = await import(process.env.PLAYWRIGHT_MODULE || "/opt/node22/lib/node_modules/playwright/index.mjs");
const browser = await pw.chromium.launch({ headless: true, args: ["--no-sandbox", "--use-angle=swiftshader", "--ignore-gpu-blocklist", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on("console", (m) => { if (m.type() === "error") console.error("[page]", m.text().slice(0, 200)); });
const url = `http://127.0.0.1:${port}/?splat=/splat/${path.basename(splat)}&w=${W}&h=${H}&fov=${fov}&flip=${flip}&frames=${frames}&poses=${encodeURIComponent(JSON.stringify(poses))}`;
const t0 = Date.now();
await page.goto(url);
await page.waitForFunction(() => window.__done === true, null, { timeout: 30 * 60 * 1000 });
const logLines = await page.evaluate(() => window.__log);
const shots = await page.evaluate(() => window.__shots || []);
const index = [];
for (const s of shots) {
  const name = `d${String(s.pose.d).padStart(3, "0")}_yaw${String(s.pose.yaw).padStart(3, "0")}.png`;
  fs.writeFileSync(path.join(out, name), Buffer.from(s.png.split(",")[1], "base64"));
  index.push({ file: name, ...s.pose });
}
fs.writeFileSync(path.join(out, "views.json"), JSON.stringify({ splat, scale, eye, fov, log: logLines, seconds: (Date.now() - t0) / 1000, views: index }, null, 2) + "\n");
console.log(logLines.join("\n"), `\n${index.length} views in ${((Date.now() - t0) / 1000).toFixed(0)} s -> ${out}`);
await browser.close();
server.close();
