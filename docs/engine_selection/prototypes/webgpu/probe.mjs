import {chromium} from '/opt/node22/lib/node_modules/playwright/index.mjs';
const FULL='/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const SHELL='/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const sets = {
 A_adapter_swiftshader: ['--enable-unsafe-webgpu','--use-webgpu-adapter=swiftshader','--no-sandbox'],
 B_vulkan_swiftshader: ['--enable-unsafe-webgpu','--enable-features=Vulkan','--use-vulkan=swiftshader','--no-sandbox'],
 C_recipe: ['--enable-unsafe-webgpu','--no-sandbox','--enable-features=Vulkan','--use-vulkan=swiftshader','--use-angle=swiftshader','--ignore-gpu-blocklist','--disable-vulkan-surface'],
 E_native_nosurface: ['--enable-unsafe-webgpu','--enable-features=Vulkan','--use-vulkan=native','--use-angle=vulkan','--ignore-gpu-blocklist','--disable-vulkan-surface','--no-sandbox'],
 F_native_webgpu_default: ['--enable-unsafe-webgpu','--enable-features=Vulkan','--use-vulkan=native','--use-angle=vulkan','--ignore-gpu-blocklist','--disable-vulkan-surface','--use-webgpu-adapter=default','--enable-dawn-features=vulkan_use_d32s8','--no-sandbox'],
 D_vulkan_native_lavapipe: ['--enable-unsafe-webgpu','--enable-features=Vulkan','--use-vulkan=native','--use-angle=vulkan','--ignore-gpu-blocklist','--no-sandbox'],
};
const which = process.argv[2]; const exe = process.argv[3]==='shell'?SHELL:FULL;
const args = sets[which];
const t0=Date.now();
let res;
try{
const b = await chromium.launch({headless:true,args,executablePath:exe,timeout:60000});
const p = await b.newPage();
await p.goto('http://127.0.0.1:8799/blank.html');
res = await p.evaluate(async()=>{ const o={gpu:!!navigator.gpu};
  // webgl2 info too
  try{const c=document.createElement('canvas');const gl=c.getContext('webgl2');if(gl){const e=gl.getExtension('WEBGL_debug_renderer_info');o.webgl2=e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER);}else o.webgl2=null;}catch(e){o.webgl2='err '+e.message}
  if(!navigator.gpu) return o;
  try{ const a = await navigator.gpu.requestAdapter(); if(!a){o.adapter=null;return o;}
    const i=a.info||{}; o.adapter={vendor:i.vendor,arch:i.architecture,device:i.device,desc:i.description,fallback:a.isFallbackAdapter??i.isFallbackAdapter, features:[...a.features].length, maxTex2D:a.limits.maxTextureDimension2D};
    const d = await a.requestDevice();
    let lost=false; d.lost.then(x=>{lost=x.message});
    const buf=d.createBuffer({size:16,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC});const rb=d.createBuffer({size:16,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});
    const m=d.createShaderModule({code:`@group(0)@binding(0) var<storage,read_write> o:array<u32,4>; @compute @workgroup_size(4) fn main(@builtin(local_invocation_index) i:u32){o[i]=i*7u;}`});
    const pl=d.createComputePipeline({layout:'auto',compute:{module:m,entryPoint:'main'}});
    const bg=d.createBindGroup({layout:pl.getBindGroupLayout(0),entries:[{binding:0,resource:{buffer:buf}}]});
    const e=d.createCommandEncoder();const ps=e.beginComputePass();ps.setPipeline(pl);ps.setBindGroup(0,bg);ps.dispatchWorkgroups(1);ps.end();e.copyBufferToBuffer(buf,0,rb,0,16);d.queue.submit([e.finish()]);
    await rb.mapAsync(GPUMapMode.READ); o.compute=Array.from(new Uint32Array(rb.getMappedRange())).join(',');
    // canvas present test
    const c=document.createElement('canvas');c.width=64;c.height=64;document.body.appendChild(c);const ctx=c.getContext('webgpu');ctx.configure({device:d,format:navigator.gpu.getPreferredCanvasFormat()});
    const e2=d.createCommandEncoder();const rp=e2.beginRenderPass({colorAttachments:[{view:ctx.getCurrentTexture().createView(),loadOp:'clear',clearValue:{r:1,g:0,b:0,a:1},storeOp:'store'}]});rp.end();d.queue.submit([e2.finish()]);await d.queue.onSubmittedWorkDone();
    await new Promise(r=>setTimeout(r,200)); o.lost=lost;
    const u=c.toDataURL('image/png'); o.canvasPngLen=u.length;
    const img=new Image();img.src=u;await img.decode();const c2=document.createElement('canvas');c2.width=64;c2.height=64;const g=c2.getContext('2d');g.drawImage(img,0,0);o.pixel=Array.from(g.getImageData(10,10,1,1).data).join(',');
  }catch(e){o.err=e.message}
  return o;});
res.version=await b.version();
await b.close();
}catch(e){res={launchErr:e.message.slice(0,200)}}
console.log(JSON.stringify({set:which,exe:process.argv[3]||'full',ms:Date.now()-t0,...res}));
