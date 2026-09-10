import json,struct,sys
from pathlib import Path
def info(p):
    d=Path(p).read_bytes();jl=struct.unpack_from('<I',d,12)[0];g=json.loads(d[20:20+jl])
    print(p, 'nodes',len(g.get('nodes',[])),'meshes',len(g.get('meshes',[])),'materials',len(g.get('materials',[])),'images',len(g.get('images',[])),'exts',g.get('extensionsUsed'))
    for i,m in enumerate(g.get('meshes',[])):
        tris=[];names=[]
        for pr in m['primitives']:
            a=g['accessors'][pr['indices']] if 'indices' in pr else None
            tris.append(a['count']//3 if a else g['accessors'][pr['attributes']['POSITION']]['count']//3)
            names.append(g['materials'][pr['material']]['name'] if 'material' in pr else None)
        print('  mesh',i,m.get('name'),'tris',tris,'mats',names, 'attrs',list(m['primitives'][0]['attributes'].keys()))
    for i,mt in enumerate(g.get('materials',[])):
        p=mt.get('pbrMetallicRoughness',{})
        print('  mat',i,mt.get('name'),'base',p.get('baseColorFactor'),'tex',bool(p.get('baseColorTexture')),'norm',bool(mt.get('normalTexture')),'alpha',mt.get('alphaMode'),'ds',mt.get('doubleSided'))
    for i,im in enumerate(g.get('images',[])):
        v=g['bufferViews'][im['bufferView']];print('  img',i,im.get('name'),im.get('mimeType'),v['byteLength'])
for p in sys.argv[1:]:info(p)
