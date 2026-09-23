import {chromium} from '/opt/node22/lib/node_modules/playwright/index.mjs';
const b=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-webgpu','--no-sandbox','--disable-dev-shm-usage','--enable-features=Vulkan','--use-vulkan=swiftshader','--use-angle=swiftshader','--ignore-gpu-blocklist','--disable-vulkan-surface']});
const p=await b.newPage({viewport:{width:960,height:600}});
p.on('console',m=>{if(m.type()!=='log')console.log('[console]',m.type(),m.text().slice(0,200))});p.on('pageerror',e=>console.log('[pageerror]',e.message));
const t=Date.now();await p.goto('http://localhost:8799/wgpu_three.html?mode='+(process.argv[2]||'ssgi'));await p.waitForFunction(()=>window.__done,null,{timeout:300000});
console.log(await p.evaluate(()=>window.__log), 'total s', (Date.now()-t)/1000);
const png=await p.evaluate(()=>window.__png||'');if(png){(await import('node:fs')).writeFileSync('wgpu_three_'+(process.argv[2]||'ssgi')+'_canvas.png',Buffer.from(png.split(',')[1],'base64'));}await p.screenshot({path:'wgpu_three_'+(process.argv[2]||'ssgi')+'.png'});await b.close();
