import os
os.environ['PYOPENGL_PLATFORM']='egl'
from pathlib import Path
import json,struct,io,math
import numpy as np
np.infty=np.inf
from PIL import Image
import pyrender
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).parent;A=ROOT/'dist/assets';O=Path('/workspace/scratch/f25aff235357/recreation_output');O.mkdir(exist_ok=True)
data=(A/'Aokigahara_Cave_Corridor.glb').read_bytes();jslen=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+jslen]);off=20+jslen;blen=struct.unpack_from('<I',data,off)[0];binary=data[off+8:off+8+blen]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];d={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.frombuffer(binary,dtype=d,count=a['count']*dim,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],dim)
def image_tex(i):
 d=g['images'][g['textures'][i]['source']];v=g['bufferViews'][d['bufferView']];return np.array(Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGBA'))
materials=[]
for m in g['materials']:
 p=m.get('pbrMetallicRoughness',{});tx=image_tex(p['baseColorTexture']['index']) if p.get('baseColorTexture') else None
 materials.append(pyrender.MetallicRoughnessMaterial(name=m['name'],baseColorFactor=p.get('baseColorFactor',[1]*4),baseColorTexture=tx,roughnessFactor=.92,metallicFactor=0,doubleSided=m.get('doubleSided',False),alphaMode=m.get('alphaMode','OPAQUE'),alphaCutoff=m.get('alphaCutoff',.5)))
campos=np.array([32.14,103.12,-9.84]);groups={};ground=[]
for n in g['nodes']:
 if 'translation' in n:
  pos=np.array(n['translation']);dist=np.linalg.norm((pos-campos)[[0,2]])
  if dist>95:continue
  mat=np.eye(4);mat[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));mat[:3,3]=pos;groups.setdefault(n['mesh'],[]).append(mat)
 else:groups.setdefault(n['mesh'],[]).append(np.eye(4))
scene=pyrender.Scene(bg_color=[.66,.73,.73,1],ambient_light=[1.05,1.12,1.02])
for mi,poses in groups.items():
 prims=[]
 for p in g['meshes'][mi]['primitives']:
  at=p['attributes'];pos=acc(at['POSITION']);idx=acc(p['indices']).reshape(-1,3)
  if 'GSI' in g['meshes'][mi].get('name','') or mi>=8:
   centre=pos[idx].mean(1);idx=idx[np.linalg.norm(centre[:,[0,2]]-campos[[0,2]],axis=1)<150]
  colors=acc(at['COLOR_0']) if 'COLOR_0'in at else None
  if colors is not None and colors.shape[1]==3:colors=np.column_stack([colors,np.ones(len(colors))])
  prims.append(pyrender.Primitive(positions=pos,normals=acc(at['NORMAL']),texcoord_0=acc(at['TEXCOORD_0']) if 'TEXCOORD_0'in at else None,color_0=colors,indices=idx,material=materials[p['material']],poses=np.array(poses)))
 scene.add(pyrender.Mesh(prims))
yaw=.45;pitch=-.025;pose=np.eye(4);pose[:3,:3]=Rotation.from_euler('YX',[yaw,pitch]).as_matrix();pose[:3,3]=campos
camera=pyrender.PerspectiveCamera(yfov=math.radians(62),znear=.12,zfar=800)
scene.add(camera,pose=pose)
lightpose=np.eye(4);direction=np.array([-.6,-.7,.25]);direction/=np.linalg.norm(direction);right=np.cross(direction,[0,1,0]);right/=np.linalg.norm(right);up=np.cross(right,direction);lightpose[:3,:3]=np.column_stack([right,up,-direction]);lightpose[:3,3]=campos+[0,35,0]
scene.add(pyrender.DirectionalLight(color=[1,.94,.83],intensity=3),pose=lightpose)
r=pyrender.OffscreenRenderer(1600,1000);color,depth=r.render(scene,flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL);r.delete();Image.fromarray(color).save(O/'Aokigahara_Model_Ground_View.png');print('Rendered',len(groups),'mesh groups',sum(len(p) for p in groups.values()),'instances', 'depth positive fraction',float(np.mean(depth>0)))
