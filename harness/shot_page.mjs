import {chromium} from 'playwright';import fs from 'fs';
const [,, url, out, w='1400', h='900']=process.argv;
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox','--disable-dev-shm-usage']});
const page=await browser.newPage({viewport:{width:+w,height:+h}});page.setDefaultTimeout(600000);
page.on('console',m=>{if(m.type()==='error')console.log('[browser]',m.text().slice(0,300));});page.on('pageerror',e=>console.log('[pageerror]',e.message));
await page.goto(url);await page.waitForFunction(()=>window.__done,null,{timeout:600000});
const data=await page.evaluate(()=>{window.__render();return document.querySelector('canvas').toDataURL('image/png');});
fs.writeFileSync(out,Buffer.from(data.split(',')[1],'base64'));await browser.close();console.log('saved',out);
