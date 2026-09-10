from build_world import *
from glb_merge import merge_meshes
import re,copy
O=ROOT/'recreation_output';g=GLB()
def import_component(path,filter_node=None):
 b=Path(path).read_bytes();l=struct.unpack_from('<I',b,12)[0];src=json.loads(b[20:20+l]);access_offset=len(g.g['accessors']);meshes=merge_meshes(g,path);count=0
 for n in src['nodes']:
  if 'mesh'not in n or (filter_node and not filter_node(n)):continue
  node=copy.deepcopy(n);node['mesh']=meshes[n['mesh']]
  if 'extensions'in node and 'EXT_mesh_gpu_instancing'in node['extensions']:
   a=node['extensions']['EXT_mesh_gpu_instancing']['attributes'];node['extensions']['EXT_mesh_gpu_instancing']['attributes']={k:v+access_offset for k,v in a.items()}
  i=len(g.g['nodes']);g.g['nodes'].append(node);g.g['scenes'][0]['nodes'].append(i);count+=1
 return count
counts={};counts['corridor']=import_component(O/'Aokigahara_Cave_Corridor.glb')
counts['context']=import_component(A/'Aokigahara_Surface_Terrain.glb',lambda n:not n.get('name','').startswith('Local_Ground'))
def outside(n):
 m=re.search(r'E(-?\d+) S(-?\d+)',n.get('name',''))
 return not(m and -2<=int(m[1])<=1 and -2<=int(m[2])<=1)
counts['forest_tiles']=import_component(A/'Aokigahara_Instanced_Forest.glb',outside)
extra=json.load(open(A/'provenance.json'));extra['assembly']={'components':counts,'overlapRemoval':'Excluded the Surface local ground and wider-forest 512m tile groups entirely inside the 2.048km corridor. Keeps corridor tree nodes and outside instanced vegetation.','requires':'EXT_mesh_gpu_instancing','geometryStatus':'Measured-source macro terrain; interpreted forest distribution and representative/procedural objects','not_a_surveyed_digital_twin':True};print('Assembled world',g.save(O/'Aokigahara_World.glb',extra),'bytes',counts)
