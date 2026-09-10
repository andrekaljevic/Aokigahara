from pathlib import Path
import json,zipfile,hashlib,re,struct,io
import numpy as np
from PIL import Image
ROOT=Path('/workspace/scratch/f25aff235357');S=Path(__file__).parent;D=S/'dist';O=ROOT/'recreation_output';A=D/'assets'
p=O/'Aokigahara_3D_README.md';s=p.read_text();s=s.replace('## Open the models','## Open the models\n\n**Start with Aokigahara_World.glb** for the assembled landscape. It combines the detailed corridor, surrounding terrain and wider instanced forest, with duplicate local ground and vegetation groups removed. It requires EXT_mesh_gpu_instancing. Use the separate standard Corridor/Terrain files if your application does not support that extension.');p.write_text(s)
# Runtime download succeeds with either a hosted ZIP or the local model file.
p=D/'app.js';t=p.read_text().replace('Download ready. The ZIP contains the GLB and source information.','Model download ready. Keep the source information with it.');p.write_text(t)
checks=[]
for p in sorted(O.glob('*.glb')):
 b=p.read_bytes();magic,ver,size=struct.unpack_from('<III',b);assert(magic,ver,size)==(0x46546c67,2,len(b));n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;binary=b[off+8:]
 for v in g['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=len(binary)
 for m in g['meshes']:
  for pr in m['primitives']:
   a=g['accessors'][pr['indices']];v=g['bufferViews'][a['bufferView']];dt={5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];q=np.frombuffer(binary,dtype=dt,count=a['count'],offset=v.get('byteOffset',0)+a.get('byteOffset',0));assert q.max()<g['accessors'][pr['attributes']['POSITION']]['count']
 for im in g['images']:
  v=g['bufferViews'][im['bufferView']];Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).verify()
 instance_count=0
 for node in g['nodes']:
  ex=node.get('extensions',{}).get('EXT_mesh_gpu_instancing')
  if ex:
   counts=[g['accessors'][i]['count'] for i in ex['attributes'].values()];assert len(set(counts))==1;instance_count+=counts[0]
 checks.append({'file':p.name,'bytes':len(b),'nodes':len(g['nodes']),'meshResources':len(g['meshes']),'gpuInstances':instance_count,'sha256':hashlib.sha256(b).hexdigest(),'validation':'GLB structure, buffer bounds, indices and embedded images passed'})
assert next(x for x in checks if x['file']=='Aokigahara_World.glb')['gpuInstances']==413602
for p in D.rglob('*'):
 if p.is_file():assert p.stat().st_size<=25*1024*1024,('Static asset too large',p)
# Download parts reproduce the exact prepared ZIP.
man=json.load(open(A/'corridor-download.json'));parts=b''.join((A/x['file']).read_bytes() for x in man['parts']);assert parts==(O/'Aokigahara_Cave_Corridor.zip').read_bytes()
with zipfile.ZipFile(io.BytesIO(parts)) as z:assert z.testzip() is None
(O/'Aokigahara_3D_Validation.json').write_text(json.dumps({'files':checks,'localTreeCount':53999,'widerTreeCount':467601,'assembledOutsideInstanceCount':413602,'terrainRayChecks':'Validated in Three.js at start, Fugaku, Narusawa and Fuji context','browserInteractionTested':False},indent=2))
items={}
def add(path,name):
 p=Path(path)
 if p.is_file():items[name]=p.read_bytes()
for p in O.glob('*.glb'):add(p,'models/'+p.name)
for fn in ['Aokigahara_3D_README.md','Aokigahara_3D_Provenance.json','Aokigahara_3D_Validation.json','Aokigahara_Model_Ground_View.png']:add(O/fn,fn)
# Browser assets: reuse top-level model files, avoid duplicate binaries and hosted download parts.
skip={'Aokigahara_Surface_Terrain.glb','Aokigahara_Regional_Terrain.glb','Aokigahara_Instanced_Forest.glb','corridor-download.json'}
for p in D.rglob('*'):
 if not p.is_file() or p.name in skip or p.name.startswith('corridor-download-'):continue
 name='viewer/'+str(p.relative_to(D));data=p.read_bytes()
 if p.name in ['app.js','index.html']:
  tx=data.decode()
  for model in ['Aokigahara_Surface_Terrain.glb','Aokigahara_Regional_Terrain.glb','Aokigahara_Instanced_Forest.glb']:tx=tx.replace('assets/'+model,'../models/'+model)
  if p.name=='index.html':tx=tx.replace('Download corridor · GLB in ZIP','Download corridor · GLB')
  data=tx.encode()
 items[name]=data
core=O/'Aokigahara_Cave_Corridor.glb';items['viewer/assets/corridor-download.json']=json.dumps({'fileName':core.name,'mimeType':'model/gltf-binary','bytes':core.stat().st_size,'parts':[{'file':'../../models/'+core.name,'bytes':core.stat().st_size}]}).encode()
items['launch_viewer.py']=b'''from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nfrom pathlib import Path\nimport os, webbrowser\nos.chdir(Path(__file__).resolve().parent)\naddress="http://127.0.0.1:8000/viewer/"\nprint("Open",address,"; press Ctrl+C to stop")\nwebbrowser.open(address)\nThreadingHTTPServer(("127.0.0.1",8000),SimpleHTTPRequestHandler).serve_forever()\n'''
for fn in ['forest-wide.f32','forest-wide.json','build_forest_wide.py']:add(ROOT/'build-assets/full_forest'/fn,'data/'+fn)
for fn in ['attachment_audit.md','attachment_cave_constraints.json','attachment_asset_manifest.json']:add(ROOT/'build-assets'/fn,'evidence/'+fn)
add(ROOT/'output/Aokigahara_Source_Catalogue.csv','evidence/Research_Source_Catalogue.csv')
for group in ['materials','models','terrain','terrain_exports','procedural_trees']:
 for p in (ROOT/'build-assets'/group).glob('*.json'):add(p,'source_manifests/'+group+'/'+p.name)
for fn in ['build_world.py','export_scene.py','export_forest.py','assemble_world.py','glb_merge.py','prepare_delivery.py','package_recreation.py','validate_runtime.mjs','render_model.py']:add(S/fn,'construction_code/'+fn)
for p in (ROOT/'build-assets/procedural_trees').rglob('*.npz'):add(p,'construction_inputs/procedural_trees/'+str(p.relative_to(ROOT/'build-assets/procedural_trees')))
add(ROOT/'build-assets/procedural_trees/generate_trees.py','construction_inputs/procedural_trees/generate_trees.py')
items['construction_code/PORTABILITY.md']=b'These are the exact construction/validation scripts from this session, supplied for audit and adaptation. Some source paths refer to the original research workspace; they are not a one-command portable build. The ready GLBs and local viewer do not require rerunning them.\n'
manifest={k:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()} for k,v in items.items()};items['MANIFEST_SHA256.json']=json.dumps(manifest,indent=2).encode()
with zipfile.ZipFile(O/'Aokigahara_3D_Package.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for k,v in items.items():z.writestr(k,v)
with zipfile.ZipFile(O/'Aokigahara_3D_Package.zip') as z:assert z.testzip() is None
print(json.dumps({'validatedModels':len(checks),'worldBytes':(O/'Aokigahara_World.glb').stat().st_size,'packageBytes':(O/'Aokigahara_3D_Package.zip').stat().st_size,'packageFiles':len(items),'staticAssetsUnderLimit':True},indent=2))
