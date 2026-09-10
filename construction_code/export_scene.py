from build_world import *
import shutil
from glb_merge import merge_meshes
PROV={'title':'Aokigahara georeferenced surface reconstruction','coordinateSystem':{'originWgs84':[138.658,35.4775],'localProjection':'+proj=aeqd +lat_0=35.4775 +lon_0=138.658 +datum=WGS84 +units=m +no_defs','axes':{'x':'east','y':'up','z':'south'},'units':'metres','heightOffsetM':900,'verticalExaggeration':1},'observed':['GSI numerical macro terrain','Mapped community polygons','OSM mapped path centre lines'],'procedural':['Individual trees, roots, leaf distribution, deadwood and stones','Estimated path widths and compacted surfaces','Representative CC0 forest-floor and bark materials'],'unknown':['Exact tree and root positions','Fine lava relief and ground structures below DEM sampling','Cave-mouth geometry and complete underground passages','Current visitor infrastructure dimensions'],'attachment':'Aokigahara_Master_Consolidated_Dossier.pdf, 35 pages; cave conflicts retained in companion manifest'}
trees=json.load(open(ROOT/'build-assets/procedural_trees/manifest.json'))
def add_tree_library(g):
 mat=A/'materials';bark=g.material('Representative cedar bark (not verified hinoki)',[1,1,1,1],mat/'japanese_cedar_bark_diff_1k.jpg',mat/'japanese_cedar_bark_nor_gl_1k.jpg',mat/'japanese_cedar_bark_rough_1k.jpg');leaf=g.material('Procedural leaves',[1,1,1,1],double=True);lookup={}
 for i,item in enumerate(trees['variants']):
  for lod in ['high','low']:
   prims=[]
   for slot in ['bark','leaves']:
    n=np.load(item['files'][lod][slot]['path']);prims.append(g.primitive(n['positions'],n['indices'],bark if slot=='bark' else leaf,n['normals'],n['uv'],n['colors'][:,:3] if slot=='leaves' else None))
   lookup[i,lod]=g.mesh(f'tree_{i}_{lod}',prims)
 return lookup
lib=GLB();lookup=add_tree_library(lib)
for (i,lod),mesh in lookup.items():lib.node(f'tree_{i}_{lod}',mesh)
print('Tree library',lib.save(A/'tree-library.glb',PROV))
# Full 2.048 km square surface export. Reuses glTF mesh objects: instances stay editable.
g=GLB();lookup=add_tree_library(g);mat=A/'materials'
ground=g.material('Representative forest ground (not calibrated site material)',[.70,.73,.57,1],mat/'leaves_forest_ground_diff_1k.jpg',mat/'leaves_forest_ground_nor_gl_1k.jpg',mat/'leaves_forest_ground_rough_1k.jpg')
m,h=GRIDS['local'];x=np.linspace(m['minX'],m['maxX'],m['width']);z=np.linspace(m['minZ'],m['maxZ'],m['height']);xx,zz=np.meshgrid(x,z);positions=np.column_stack([xx.ravel(),h.ravel()-900,zz.ravel()]);uv=np.column_stack([xx.ravel()/1.26,zz.ravel()/1.26]);idx=[]
for j in range(m['height']-1):
 for i in range(m['width']-1):a=j*m['width']+i;idx.extend([[a,a+m['width'],a+1],[a+1,a+m['width'],a+m['width']+1]])
g.node('GSI DEM5A corridor terrain - 8m resampling',g.mesh('Ground',[g.primitive(positions,idx,ground,uv=uv)]),extras={'source':'MAP-007','geometryStatus':'Measured-source terrain, resampled; no fine displacement'})
path=g.material('Estimated compacted path surface',[.62,.57,.45,1]);g.g['materials'][path]['pbrMetallicRoughness']['baseColorTexture']=g.g['materials'][ground]['pbrMetallicRoughness']['baseColorTexture'];paths_mesh(g,json.load(open(T/'local-context.json')),path)
a=np.fromfile(A/'forest-instances.f32',dtype='<f4').reshape(-1,6)
hero=merge_meshes(g,A/'models/fir_tree_c.glb');hero_ids={int(i) for i in np.argsort(np.hypot(a[:,0]-32.14,a[:,2]+9.84)) if a[i,5]<2 and np.hypot(a[i,0]-32.14,a[i,2]+9.84)<24};hero_ids=set(sorted(hero_ids,key=lambda i:math.hypot(a[i,0]-32.14,a[i,2]+9.84))[:4])
for j,(x,y,z,s,r,v) in enumerate(a):
 if j in hero_ids:
  g.node(f'Representative_mature_fir_{j}',hero[0],[float(x),height(float(x),float(z))+.0936*float(s),float(z)],[float(s)]*3,[0,math.sin(float(r)/2),0,math.cos(float(r)/2)]);continue
 lod='high' if math.hypot(x-32.14,z+9.84)<120 else 'low';g.node(f'Procedural_tree_{j:05d}',lookup[int(v),lod],[float(x),height(float(x),float(z))-.06,float(z)],[float(s)]*3,[0,math.sin(float(r)/2),0,math.cos(float(r)/2)])
# Representative near-ground objects are exported as real reusable meshes.
from glb_merge import merge_meshes
ferns=merge_meshes(g,A/'models/fern_02.glb');logs=merge_meshes(g,A/'models/dead_tree_trunk.glb')
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
ctx=json.load(open(T/'local-context.json'));avoid=unary_union([LineString(p['coordinates']).buffer(5 if p['kind']=='road' else 1.8) for p in ctx['paths']]);decor_count=0
for j in range(-12,11):
 for i in range(-5,19):
  x=i*5+(rand(i,j,19)-.5)*4;z=j*5+(rand(i,j,20)-.5)*4
  if math.hypot(x-32.14,z+9.84)>58 or avoid.contains(Point(x,z)) or rand(i,j,21)>.48:continue
  size=.75+rand(i,j,22)*.85;rot=rand(i,j,23)*math.tau;g.node('Representative_fern_'+str(decor_count),ferns[decor_count%len(ferns)],[x,height(x,z)+.015,z],[size]*3,[0,math.sin(rot/2),0,math.cos(rot/2)]);decor_count+=1
for j in range(4):
 x,z=[(45,-29),(11,-62),(73,2),(-9,-5)][j];rot=j*1.73;g.node('Representative_fallen_log_'+str(j),logs[0],[x,height(x,z)+.012,z],[1]*3,[0,math.sin(rot/2),0,math.cos(rot/2)])
import trimesh
rock=g.material('Representative rough rock; not measured basalt',[.48,.5,.42,1],mat/'rock_3_diff_1k.jpg',mat/'rock_3_nor_gl_1k.jpg',mat/'rock_3_rough_1k.jpg');rm=trimesh.creation.icosphere(subdivisions=2,radius=1);vp=np.asarray(rm.vertices).copy();factor=.88+.16*np.sin(vp[:,0]*17+vp[:,1]*13+vp[:,2]*29);vp*=factor[:,None];vp[:,1]*=.48;rmesh=g.mesh('Procedural rough surface rock',[g.primitive(vp,rm.faces,rock,uv=vp[:,[0,2]]/1.5)])
for j in range(34):
 x=32.14+(rand(j,8,5)-.5)*115;z=-9.84+(rand(j,9,5)-.5)*115
 if avoid.contains(Point(x,z)):continue
 size=.3+rand(j,3,1)*.95;r=rand(j,2,1)*math.tau;g.node('Procedural_lava_surface_approximation_'+str(j),rmesh,[x,height(x,z)+.04,z],[size]*3,[0,math.sin(r/2),0,math.cos(r/2)])
PROV['nearFieldDecor']='Representative CC0 ferns/logs and procedural rough rock near initial station. These are not surveyed site objects.'
PROV['treeCount']=len(a);PROV['exportDetail']='Detailed mature trees within 120 m of initial forest station; simplified crowns elsewhere. Shared meshes, independent editable tree nodes.';PROV['coreBoundsLocal']=[-1024,-1024,1024,1024];PROV['coreAreaKm2']=4.194304
print('Corridor GLB',g.save(A/'Aokigahara_Cave_Corridor.glb',PROV))
for fn in ['Aokigahara_Regional_Terrain.glb','Aokigahara_Surface_Terrain.glb']:shutil.copy2(ROOT/'build-assets/terrain_exports'/fn,A/fn)
PROV['references']={'terrain':'https://maps.gsi.go.jp/development/ichiran.html','vegetation':'https://www.biodic.go.jp/','geology':'https://www.gsj.jp/Map/EN/volcano.html','paths':'https://www.openstreetmap.org/copyright','materials':'https://polyhaven.com/license'}
PROV['manifests']={k:json.load(open(p)) for k,p in [('terrain',ROOT/'build-assets/terrain/manifest.json'),('terrainExports',ROOT/'build-assets/terrain_exports/manifest.json'),('materials',ROOT/'build-assets/materials/manifest.json'),('models',ROOT/'build-assets/models/MODEL_MANIFEST.json'),('proceduralTrees',ROOT/'build-assets/procedural_trees/manifest.json'),('caveConstraints',ROOT/'build-assets/attachment_cave_constraints.json')]}
PROV['manifests']['matureFir']=json.load(open(ROOT/'build-assets/models/FIR_TREE_C_MANIFEST.json'))
PROV['manifests']['forestWide']=json.load(open(ROOT/'build-assets/full_forest/forest-wide.json'))
(A/'provenance.json').write_text(json.dumps(PROV,indent=2,ensure_ascii=False))
print('Scene sources saved')
