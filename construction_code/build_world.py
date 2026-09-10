"""Reproducible Aokigahara scene assets. Source geometry and procedural placement remain separate."""
from pathlib import Path
import json, math, struct, copy, io
import numpy as np
from PIL import Image
ROOT=Path('/workspace/scratch/f25aff235357'); SITE=Path(__file__).parent; A=SITE/'dist/assets'; T=A/'terrain'
class GLB:
 def __init__(self):
  self.g={'asset':{'version':'2.0','generator':'Aokigahara georeferenced reconstruction compiler'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[{'byteLength':0}],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497}]};self.b=bytearray()
 def buffer(self,b,target=None):
  self.b.extend(b'\0'*((-len(self.b))%4));v={'buffer':0,'byteOffset':len(self.b),'byteLength':len(b)}
  if target:v['target']=target
  self.b.extend(b);i=len(self.g['bufferViews']);self.g['bufferViews'].append(v);return i
 def accessor(self,a,typ):
  a=np.asarray(a);a=a.astype('<f4' if a.dtype.kind=='f' else '<u4');v=self.buffer(a.tobytes(),34963 if typ=='SCALAR' else 34962);d={'bufferView':v,'componentType':5126 if a.dtype.kind=='f' else 5125,'count':len(a),'type':typ}
  if typ=='VEC3' and a.dtype.kind=='f':d.update(min=a.min(0).tolist(),max=a.max(0).tolist())
  self.g['accessors'].append(d);return len(self.g['accessors'])-1
 def tex(self,p):
  p=Path(p);i=len(self.g['images']);self.g['images'].append({'bufferView':self.buffer(p.read_bytes()),'mimeType':'image/png' if p.suffix.lower()=='.png' else 'image/jpeg'});j=len(self.g['textures']);self.g['textures'].append({'source':i,'sampler':0});return j
 def material(self,name,color,base=None,normal=None,rough=None,double=False):
  p={'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':.93}
  if base:p['baseColorTexture']={'index':self.tex(base)}
  d={'name':name,'pbrMetallicRoughness':p,'doubleSided':double}
  if normal:d['normalTexture']={'index':self.tex(normal),'scale':.6}
  if rough:
   im=Image.open(rough).convert('L');packed=Image.merge('RGB',(Image.new('L',im.size,255),im,Image.new('L',im.size,0)));tmp=A/(name+'_MR.png');packed.save(tmp);p['metallicRoughnessTexture']={'index':self.tex(tmp)}
  self.g['materials'].append(d);return len(self.g['materials'])-1
 def primitive(self,positions,indices,material,normals=None,uv=None,color=None):
  p=np.asarray(positions,dtype=np.float32);f=np.asarray(indices,dtype=np.uint32).reshape(-1,3)
  if normals is None:
   normals=np.zeros_like(p);n=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]);[np.add.at(normals,f[:,i],n) for i in range(3)];normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-9)
  at={'POSITION':self.accessor(p,'VEC3'),'NORMAL':self.accessor(np.asarray(normals,dtype=np.float32),'VEC3')}
  if uv is not None:at['TEXCOORD_0']=self.accessor(np.asarray(uv,dtype=np.float32),'VEC2')
  if color is not None:at['COLOR_0']=self.accessor(np.asarray(color,dtype=np.float32),'VEC3')
  return {'attributes':at,'indices':self.accessor(f.reshape(-1),'SCALAR'),'material':material}
 def mesh(self,name,prims):
  self.g['meshes'].append({'name':name,'primitives':prims});return len(self.g['meshes'])-1
 def node(self,name,mesh,translation=None,scale=None,rotation=None,extras=None):
  d={'name':name,'mesh':mesh}
  for k,v in [('translation',translation),('scale',scale),('rotation',rotation),('extras',extras)]:
   if v is not None:d[k]=v
  self.g['nodes'].append(d);i=len(self.g['nodes'])-1;self.g['scenes'][0]['nodes'].append(i);return i
 def save(self,p,extras=None):
  if extras:self.g['extras']=extras
  self.g['buffers'][0]['byteLength']=len(self.b);j=json.dumps(self.g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=bytes(self.b);b+=b'\0'*((-len(b))%4);p=Path(p);p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b);return p.stat().st_size

def load_grid(name):
 m=json.load(open(T/f'{name}-height.json'));return m,np.fromfile(T/m['file'],dtype='<f4').reshape(m['height'],m['width'])
GRIDS={n:load_grid(n) for n in ['local','study','regional']}
def height(x,z):
 for m,h in GRIDS.values():
  if m['minX']<=x<=m['maxX'] and m['minZ']<=z<=m['maxZ']:
   u=(x-m['minX'])/m['dx'];v=(z-m['minZ'])/m['dz'];i=min(int(u),m['width']-2);j=min(int(v),m['height']-2);a=u-i;b=v-j;return float(((1-a-b)*h[j,i]+a*h[j,i+1]+b*h[j+1,i] if a+b<=1 else (1-b)*h[j,i+1]+(1-a)*h[j+1,i]+(a+b-1)*h[j+1,i+1])-900)
 return 0.
def rand(i,j,k=0):
 n=((i*374761393)^(j*668265263)^(k*144269))&0xffffffff;n=((n^(n>>13))*1274126177)&0xffffffff;return ((n^(n>>16))&0xffffffff)/4294967296

def paths_mesh(g,ctx,material):
 v=[];f=[];uv=[]
 for path in ctx['paths']:
  if path.get('access') in ['private','no']:continue
  pts=path['coordinates'];width=6.8 if path['kind']=='road' else 1.6
  for a,b in zip(pts,pts[1:]):
   dx,dz=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dz)
   if l<.01:continue
   px,pz=-dz/l*width/2,dx/l*width/2;n=max(1,math.ceil(l/.8));start=len(v)
   for t in range(n+1):
    x=a[0]+dx*t/n;z=a[1]+dz*t/n
    for side in [-1,1]:v.append([x+side*px,height(x+side*px,z+side*pz)+.055,z+side*pz]);uv.append([0 if side<0 else 1,t*l/n/width])
   for t in range(n):q=start+2*t;f.extend([[q,q+1,q+2],[q+1,q+3,q+2]])
 if v:g.node('Mapped paths - widths approximated',g.mesh('Path surfaces',[g.primitive(v,f,material,uv=uv)]),extras={'evidence':'OSM centre lines; width and surface treatment procedural; not access guidance'})

def build_positions():
 ctx=json.load(open(T/'local-context.json'));m,h=GRIDS['local'];classes=np.fromfile(T/'local-landcover.u8',dtype='uint8').reshape(h.shape)
 from shapely.geometry import LineString,Point
 from shapely.ops import unary_union
 avoid=unary_union([LineString(p['coordinates']).buffer(5 if p['kind']=='road' else 1.7) for p in ctx['paths']])
 out=[]
 for j in range(-120,121):
  for i in range(-120,121):
   x=i*8.5+(rand(i,j,1)-.5)*5.8;z=j*8.5+(rand(i,j,2)-.5)*5.8
   if abs(x)>1024 or abs(z)>1024:continue
   c=int(classes[min(256,max(0,round((z+1024)/8))),min(256,max(0,round((x+1024)/8)))])
   if c not in [1,2,3] or rand(i,j,8)<.045 or avoid.contains(Point(x,z)):continue
   variant=(2 if c==2 else 0)+int(rand(i,j,4)*2);s=.72+rand(i,j,5)*.5;r=rand(i,j,6)*math.tau
   out.append([x,height(x,z)-.06,z,s,r,variant])
 arr=np.asarray(out,dtype='<f4');arr.tofile(A/'forest-instances.f32');(A/'forest-instances.json').write_text(json.dumps({'count':len(arr),'stride':6,'fields':['x','y','z','uniformScale','yawRadians','variantId'],'spacingM':8.5,'seedMethod':'integer spatial hash in build_world.py','placement':'Procedural, constrained to mapped natural conifer, broadleaf/mixed and plantation classes; excludes mapped paths/roads with estimated buffers. Individual trees not surveyed.','coordinateSystem':'local AEQD x east z south y elevation-900','file':'forest-instances.f32'},indent=2));print('Procedural tree placements',len(arr))
if __name__=='__main__':build_positions()
