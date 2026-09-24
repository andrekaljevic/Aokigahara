import {chromium} from '/opt/node22/lib/node_modules/playwright/index.mjs';
const configs = [
 ['default-headless', ['--enable-unsafe-webgpu','--no-sandbox']],
 ['swiftshader-vulkan', ['--enable-unsafe-webgpu','--enable-features=Vulkan','--use-vulkan=swiftshader','--use-webgpu-adapter=swiftshader','--use-angle=swiftshader','--no-sandbox','--disable-gpu-sandbox']],
 ['swiftshader-new-headless', ['--headless=new','--enable-unsafe-webgpu','--enable-features=Vulkan','--use-webgpu-adapter=swiftshader','--no-sandbox']],
];
for (const [name,args] of configs) {
  const b = await chromium.launch({headless:true,args, executablePath: name.includes('new')?'/opt/pw-browsers/chromium-1194/chrome-linux/chrome':undefined});
  const p = await b.newPage();
  await p.goto('http://localhost:8799/blank.html');
  const r = await p.evaluate(async()=>{ if(!navigator.gpu) return 'no navigator.gpu';
    try{ const a = await navigator.gpu.requestAdapter(); if(!a) return 'adapter null';
      const info = a.info||{}; const d = await a.requestDevice();
      // tiny compute test
      const buf = d.createBuffer({size:16,usage:GPUBufferUsage.STORAGE|GPUBufferUsage.COPY_SRC});
      const rb = d.createBuffer({size:16,usage:GPUBufferUsage.MAP_READ|GPUBufferUsage.COPY_DST});
      const m = d.createShaderModule({code:`@group(0)@binding(0) var<storage,read_write> o:array<u32,4>; @compute @workgroup_size(4) fn main(@builtin(local_invocation_index) i:u32){o[i]=i*7u;}`});
      const pl = d.createComputePipeline({layout:'auto',compute:{module:m,entryPoint:'main'}});
      const bg = d.createBindGroup({layout:pl.getBindGroupLayout(0),entries:[{binding:0,resource:{buffer:buf}}]});
      const e = d.createCommandEncoder(); const pass=e.beginComputePass(); pass.setPipeline(pl); pass.setBindGroup(0,bg); pass.dispatchWorkgroups(1); pass.end(); e.copyBufferToBuffer(buf,0,rb,0,16); d.queue.submit([e.finish()]);
      await rb.mapAsync(GPUMapMode.READ); const out = Array.from(new Uint32Array(rb.getMappedRange()));
      return JSON.stringify({vendor:info.vendor,arch:info.architecture,desc:info.description,maxBuf:a.limits.maxBufferSize,maxStor:a.limits.maxStorageBufferBindingSize,out});
    }catch(e){return 'err '+e.message}});
  console.log(name, '=>', r, await b.version());
  await b.close();
}
