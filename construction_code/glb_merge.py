import json,struct,copy
from pathlib import Path

def merge_meshes(dst,path):
 raw=Path(path).read_bytes();n=struct.unpack_from('<I',raw,12)[0];src=json.loads(raw[20:20+n]);p=20+n;size=struct.unpack_from('<I',raw,p)[0];binary=raw[p+8:p+8+size]
 assert not src.get('skins') and not src.get('animations')
 keys=['bufferViews','accessors','images','samplers','textures','materials','meshes'];offsets={k:len(dst.g[k]) for k in keys};dst.b.extend(b'\0'*((-len(dst.b))%4));base=len(dst.b);dst.b.extend(binary)
 for x in src.get('bufferViews',[]):
  x=copy.deepcopy(x);x['buffer']=0;x['byteOffset']=x.get('byteOffset',0)+base;dst.g['bufferViews'].append(x)
 for x in src.get('accessors',[]):
  x=copy.deepcopy(x)
  if 'bufferView'in x:x['bufferView']+=offsets['bufferViews']
  if 'sparse'in x:
   for k in ['indices','values']:x['sparse'][k]['bufferView']+=offsets['bufferViews']
  dst.g['accessors'].append(x)
 for x in src.get('images',[]):
  x=copy.deepcopy(x);assert 'bufferView'in x,'Only embedded GLB images accepted';x['bufferView']+=offsets['bufferViews'];dst.g['images'].append(x)
 dst.g['samplers'].extend(copy.deepcopy(src.get('samplers',[])))
 for x in src.get('textures',[]):
  x=copy.deepcopy(x)
  if 'source'in x:x['source']+=offsets['images']
  if 'sampler'in x:x['sampler']+=offsets['samplers']
  dst.g['textures'].append(x)
 def tex_refs(x):
  if isinstance(x,dict):
   if 'index'in x:x['index']+=offsets['textures']
   for v in x.values():tex_refs(v)
  elif isinstance(x,list):
   for v in x:tex_refs(v)
 for x in src.get('materials',[]):x=copy.deepcopy(x);tex_refs(x);dst.g['materials'].append(x)
 for x in src.get('meshes',[]):
  x=copy.deepcopy(x)
  for pr in x['primitives']:
   pr['attributes']={k:v+offsets['accessors'] for k,v in pr['attributes'].items()}
   if 'indices'in pr:pr['indices']+=offsets['accessors']
   if 'material'in pr:pr['material']+=offsets['materials']
  dst.g['meshes'].append(x)
 for k in ['extensionsUsed','extensionsRequired']:
  if src.get(k):dst.g[k]=list(dict.fromkeys(dst.g.get(k,[])+src[k]))
 return [i+offsets['meshes'] for i in range(len(src['meshes']))]
