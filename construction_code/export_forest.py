from build_world import *
import shutil
src=ROOT/'build-assets/full_forest';m=json.load(open(src/'forest-wide.json'));data=np.fromfile(src/'forest-wide.f32',dtype='<f4').reshape(-1,6);g=GLB();g.g['extensionsUsed']=['EXT_mesh_gpu_instancing'];g.g['extensionsRequired']=['EXT_mesh_gpu_instancing'];b=g.material('Distant bark proxy',[.23,.17,.11,1]);l=g.material('Distant canopy proxy',[1,1,1,1],double=True);meshes=[];trees=json.load(open(ROOT/'build-assets/procedural_trees/manifest.json'))
for i,v in enumerate(trees['variants']):
 prim=[]
 for name,mat in [('bark',b),('leaves',l)]:
  n=np.load(v['files']['low'][name]['path']);prim.append(g.primitive(n['positions'],n['indices'],mat,n['normals'],n['uv'],n['colors'][:,:3] if name=='leaves' else None))
 meshes.append(g.mesh(f'Community canopy proxy {i}',prim))
# Tile the instance sets to preserve useful spatial culling and editable groups.
tile=np.floor(data[:,[0,2]]/512).astype('int32');keys=np.column_stack([tile,data[:,5].astype('int32')]);unique,inv=np.unique(keys,axis=0,return_inverse=True)
for i,k in enumerate(unique):
 a=data[inv==i];trans=a[:,:3].copy();scale=np.repeat(a[:,3:4],3,axis=1);rot=np.zeros((len(a),4),dtype='<f4');rot[:,1]=np.sin(a[:,4]/2);rot[:,3]=np.cos(a[:,4]/2);node=g.node(f'Forest tile E{k[0]} S{k[1]} variant{k[2]}',meshes[k[2]],extras={'status':'Procedural placement; interpreted vegetation and lava footprint','treeCount':len(a),'tileMetres':512});g.g['nodes'][node]['extensions']={'EXT_mesh_gpu_instancing':{'attributes':{'TRANSLATION':g.accessor(trans,'VEC3'),'ROTATION':g.accessor(rot,'VEC4'),'SCALE':g.accessor(scale,'VEC3')}}}
extras={'name':'Aokigahara interpreted forest placement layer','treeCount':len(data),'geometry':'Simplified distant vegetation proxies, no individual tree survey','boundary':'Mapped forested communities intersected with Jogan deposits plus the local modelling square; not the official named forest boundary','coordinates':'AEQD at138.658E35.4775N; x east,z south,y GSI elevation minus900 metres','import':'EXT_mesh_gpu_instancing support required. Import with Surface_Terrain at the same origin. Do not overlay local prefix with Corridor trees without removing duplicates.','localPrefixCount':53999,'vegetationSource':'MAP-013','lavaSource':'GEO-004','fullPlacementMetadata':m}
path=A/'Aokigahara_Instanced_Forest.glb';print('Full forest export',g.save(path,extras),'bytes;',len(data),'trees;',len(unique),'tile groups');shutil.copy2(src/'forest-wide.json',A/'forest-wide.json')
