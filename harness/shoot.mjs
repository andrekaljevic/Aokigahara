// Headless audit renderer: loads the viewer, freezes the animation loop, sets fixed cameras, renders once per camera, saves PNGs.
import {chromium} from 'playwright';
import fs from 'fs';
const [,, viewerDir, outDir, camFile, w='1280', h='800'] = process.argv;
const cams = JSON.parse(fs.readFileSync(camFile,'utf8'));
fs.mkdirSync(outDir,{recursive:true});
const browser = await chromium.launch({headless:true, args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--enable-webgl','--disable-gpu-sandbox','--no-sandbox','--disable-dev-shm-usage']});
const page = await browser.newPage({viewport:{width:+w,height:+h},deviceScaleFactor:1});
page.setDefaultTimeout(900000);
page.on('console', m=>{ if(m.type()==='error'||m.type()==='warning') console.log('[browser]', m.text().slice(0,300)); });
page.on('pageerror', e=>console.log('[pageerror]', e.message));
const t0=Date.now();
await page.goto(`http://127.0.0.1:8000/${viewerDir}/`, {waitUntil:'load'});
await page.waitForFunction(()=>window.__aoki && window.__aoki.ready, null, {timeout:900000, polling:500});
console.log('ready in', ((Date.now()-t0)/1000).toFixed(1),'s');
// Freeze the continuous loop so each render is explicit and measurable.
await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
await page.waitForTimeout(500);
for (const c of cams){
  const t1=Date.now();
  const res = await page.evaluate(async c=>{
    const a=window.__aoki; if(c.preset&&a.setPreset)a.setPreset(c.preset,c.sun); a.setPose(c.x,c.z,c.yaw,c.pitch,c.eye??1.72);
    if(a.tick) a.tick(); // optional per-frame update hook in the improved viewer
    const s=performance.now(); a.render(); const ms=performance.now()-s;
    const canvas=document.getElementById('world');
    return {data:canvas.toDataURL('image/png'),ms:Math.round(ms),pos:a.camera.position.toArray().map(v=>+v.toFixed(2)),trees:a.trees.length,calls:a.renderer.info.render.calls,tris:a.renderer.info.render.triangles};
  }, c);
  fs.writeFileSync(`${outDir}/${c.name}.png`, Buffer.from(res.data.split(',')[1],'base64'));
  delete res.data;
  console.log(c.name, JSON.stringify(res), 'wall', ((Date.now()-t1)/1000).toFixed(1),'s');
}
await browser.close();
