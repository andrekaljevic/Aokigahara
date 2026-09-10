"""Deterministic scene placements; mapped masks do not define a legal forest boundary."""
from pathlib import Path
import json,math,hashlib,ast,time
import numpy as np
import shapely
from shapely.geometry import LineString

ROOT=Path(__file__).parent
T=ROOT.parent/'terrain'
SITE=Path('/workspace/sites/aokigahara-field-world')
LOCAL_FILE=SITE/'dist/assets/forest-instances.f32'
def load_grid(name):
    m=json.loads((T/f'{name}-height.json').read_text())
    h=np.fromfile(T/m['file'],dtype='<f4').reshape(m['height'],m['width'])
    return m,h
GRIDS={n:load_grid(n) for n in ['local','study','regional']}
sm,sh=GRIDS['study'];lm,lh=GRIDS['local']
slc=np.fromfile(T/'study-landcover.u8',np.uint8).reshape(sh.shape)
sj=np.fromfile(T/'study-jogan.u8',np.uint8).reshape(sh.shape)
llc=np.fromfile(T/'local-landcover.u8',np.uint8).reshape(lh.shape)
study_eligible=(sj==1)&np.isin(slc,[1,2,3])
local_eligible=np.isin(llc,[1,2,3])

def rand(i,j,k=0):
    # All intermediates fit signed 64-bit; low-32-bit arithmetic matches Python.
    n=((i*374761393)^(j*668265263)^(k*144269))&0xffffffff
    n=((n^(n>>13))*1274126177)&0xffffffff
    return ((n^(n>>16))&0xffffffff)/4294967296

def height_vector(x,z):
    result=np.empty(len(x),np.float32);done=np.zeros(len(x),bool)
    for m,h in GRIDS.values():
        valid=(~done)&(x>=m['minX'])&(x<=m['maxX'])&(z>=m['minZ'])&(z<=m['maxZ'])
        if not valid.any():continue
        u=(x[valid]-m['minX'])/m['dx'];v=(z[valid]-m['minZ'])/m['dz']
        i=np.minimum(u.astype(np.int64),m['width']-2);j=np.minimum(v.astype(np.int64),m['height']-2)
        a=u-i;b=v-j
        # Match NumPy 2.x scalar weak-promotion operations in root height().
        top=h[j,i]*(1-a).astype(np.float32)+h[j,i+1]*a.astype(np.float32)
        bottom=h[j+1,i]*(1-a).astype(np.float32)+h[j+1,i+1]*a.astype(np.float32)
        result[valid]=top*(1-b).astype(np.float32)+bottom*b.astype(np.float32)-np.float32(900)
        done|=valid
    assert done.all()
    return result.astype(np.float64)

def cell_lengths(m,axis,clip=None):
    lo=m['min'+axis];hi=m['max'+axis];n=m['width'] if axis=='X' else m['height'];d=m['dx'] if axis=='X' else m['dz']
    centers=np.linspace(lo,hi,n);low=np.maximum(lo,centers-d/2);high=np.minimum(hi,centers+d/2)
    if clip is not None:low=np.maximum(low,clip[0]);high=np.minimum(high,clip[1])
    return np.maximum(0,high-low)

start=time.time()
local_bytes=LOCAL_FILE.read_bytes();local=np.frombuffer(local_bytes,dtype='<f4').reshape(-1,6).copy()
assert ((np.abs(local[:,0])<=1024)&(np.abs(local[:,2])<=1024)).all()
# Core geometry buffers are unchanged, so exact old instances remain valid.
for n in ['local','study','regional']:
    for file in [f'{n}-height.json',f'{n}-height.f32']:
        assert (T/file).read_bytes()==(SITE/'dist/assets/terrain'/file).read_bytes(),f'Grid differs from root: {file}'

ctx=json.loads((T/'study-context.json').read_text())
lines=[LineString(p['coordinates']) for p in ctx['paths']]
radii=np.array([5 if p['kind']=='road' else 1.7 for p in ctx['paths']])
avoid=shapely.union_all(shapely.buffer(lines,radii,quad_segs=16))
shapely.prepare(avoid)
print('ROAD_BUFFERS_READY',len(lines),'seconds',round(time.time()-start,2),flush=True)

imin=math.floor((sm['minX']-2.9)/8.5);imax=math.ceil((sm['maxX']+2.9)/8.5)
jmin=math.floor((sm['minZ']-2.9)/8.5);jmax=math.ceil((sm['maxZ']+2.9)/8.5)
pieces=[local];pre_gaps=0;gap_rejected=0;path_rejected=0;checks=[]
for j0 in range(jmin,jmax+1,96):
    ii,jj=np.meshgrid(np.arange(imin,imax+1,dtype=np.int64),np.arange(j0,min(jmax+1,j0+96),dtype=np.int64))
    ii=ii.ravel();jj=jj.ravel()
    x=ii*8.5+(rand(ii,jj,1)-.5)*5.8;z=jj*8.5+(rand(ii,jj,2)-.5)*5.8
    valid=(x>=sm['minX'])&(x<=sm['maxX'])&(z>=sm['minZ'])&(z<=sm['maxZ'])&((np.abs(x)>1024)|(np.abs(z)>1024))
    ii,jj,x,z=[a[valid] for a in [ii,jj,x,z]]
    col=np.rint((x-sm['minX'])/sm['dx']).astype(np.int64);row=np.rint((z-sm['minZ'])/sm['dz']).astype(np.int64)
    valid=study_eligible[row,col];c=slc[row,col]
    ii,jj,x,z,c=[a[valid] for a in [ii,jj,x,z,c]]
    pre_gaps+=len(x)
    valid=rand(ii,jj,8)>=.045;gap_rejected+=int((~valid).sum())
    ii,jj,x,z,c=[a[valid] for a in [ii,jj,x,z,c]]
    valid=~shapely.contains_xy(avoid,x,z);path_rejected+=int((~valid).sum())
    ii,jj,x,z,c=[a[valid] for a in [ii,jj,x,z,c]]
    y=height_vector(x,z)-.06
    scale=.72+rand(ii,jj,5)*.5;yaw=rand(ii,jj,6)*math.tau
    variant=np.where(c==2,2,0)+(rand(ii,jj,4)*2).astype(np.int64)
    out=np.column_stack([x,y,z,scale,yaw,variant]).astype('<f4')
    pieces.append(out)
    if len(x):
        for k in np.linspace(0,len(x)-1,min(8,len(x)),dtype=int):checks.append((int(ii[k]),int(jj[k]),float(x[k]),float(z[k]),float(y[k])))
arr=np.vstack(pieces).astype('<f4')
assert arr[:len(local)].tobytes()==local_bytes
assert np.isfinite(arr).all()

# Read only the root functions for independent exact-hash/height checks. No Site import/write.
source=ast.parse((SITE/'build_world.py').read_text())
functions=[node for node in source.body if isinstance(node,ast.FunctionDef) and node.name in ['rand','height']]
env={'GRIDS':GRIDS};exec(compile(ast.Module(body=functions,type_ignores=[]),'root_reference_functions','exec'),env)
for i,j,x,z,y in checks:
    assert x==i*8.5+(env['rand'](i,j,1)-.5)*5.8
    assert z==j*8.5+(env['rand'](i,j,2)-.5)*5.8
    assert np.float32(y)==np.float32(env['height'](x,z)-.06)

sx=cell_lengths(sm,'X');sz=cell_lengths(sm,'Z');lx=cell_lengths(lm,'X');lz=cell_lengths(lm,'Z')
overlapx=cell_lengths(sm,'X',(-1024,1024));overlapz=cell_lengths(sm,'Z',(-1024,1024))
study_area=float((study_eligible*sz[:,None]*sx[None,:]).sum())
study_local_overlap=float((study_eligible*overlapz[:,None]*overlapx[None,:]).sum())
local_area=float((local_eligible*lz[:,None]*lx[None,:]).sum())
selection_area=study_area-study_local_overlap+local_area
file=ROOT/'forest-wide.f32';arr.tofile(file)
metadata=dict(version=1,file=file.name,count=len(arr),stride=6,fields=['x','y','z','uniformScale','yawRadians','variantId'],
 encoding='float32 little-endian; tightly packed interleaved records',recordBytes=24,bytes=file.stat().st_size,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
 spacingM=8.5,jitterM=5.8,hashGapFraction=.045,seedMethod='Exact integer spatial hash from root build_world.py; implementation reproduced in build_forest_wide.py',
 coordinateSystem=dict(projection=json.loads((T/'manifest.json').read_text())['projection'],originWgs84=[138.658,35.4775],axes='x east, y up, z south',height='Root-compatible bilinear measured grid height, local first then study, y=elevationM-900-0.06'),
 selection=dict(definition='Outside the local rectangle, nearest study sample must have study-jogan=1 and study-landcover in [1,2,3]. Inside local x/z ±1024 m, use exact existing local forest instances, preserving forested local classes regardless of Jogan mask.',
    legalBoundary=False,interpretation='PROJECT INTERPRETATION: mapped eruption-product footprint intersected with forested landcover plus forested local core; not a legal, surveyed or definitive Aokigahara forest boundary.',
    boundsXZ=[sm['minX'],sm['minZ'],sm['maxX'],sm['maxZ']],
    studyMappedIntersectionAreaM2=study_area,studyIntersectionInsideLocalAreaM2=study_local_overlap,forcedLocalForestedAreaM2=local_area,
    selectedAreaBeforeBuffersAndHashGapsM2=selection_area,selectedAreaBeforeBuffersAndHashGapsKm2=selection_area/1e6,
    areaBasis='Exact clipped nearest-sample raster-cell area for the supplied categorical grids. Boundary sample cells extend half a cell inward. Study/local overlap is replaced, not double counted. This is a project mask area, not measured forest extent.'),
 placement=dict(individualTreesSurveyed=False,treeCountIsCensus=False,roadBufferM=5,trailBufferM=1.7,
    roadSource='study-context.json OSM mapped centre lines; estimated exclusion widths include private/no-access tagged paths to match root exclusion rule',
    scaleFormula='.72 + rand(i,j,5)*.5',yawFormula='rand(i,j,6)*2*pi',
    variantFormula='(2 if class==2 else 0)+int(rand(i,j,4)*2)',
    forestedClasses={'1':'natural conifer','2':'broadleaf/mixed woody','3':'plantation'},
    outerEligibleCandidatesBeforeGaps=pre_gaps,outerRejectedByHashGaps=gap_rejected,outerRejectedByPathBuffersAfterGaps=path_rejected,outerCount=len(arr)-len(local)),
 localOverlap=dict(localPrefixCount=len(local),localPrefixBytes=len(local_bytes),localPrefixSha256=hashlib.sha256(local_bytes).hexdigest(),
    originalFile=str(LOCAL_FILE),exactBytesPreserved=True,remainingRecords='All appended records are outside abs(x)<=1024 AND abs(z)<=1024; local and appended records never overlap.',
    use='Use this file to replace forest-instances.f32, or append only records after localPrefixCount to existing local instances. Do not append the complete file to the existing local instances.'),
 boundsMinXYZ=arr[:,:3].min(0).tolist(),boundsMaxXYZ=arr[:,:3].max(0).tolist(),
 variants={str(k):int((arr[:,5]==k).sum()) for k in range(4)},
 sourceFiles=[dict(file=name,sha256=hashlib.sha256((T/name).read_bytes()).hexdigest()) for name in ['study-jogan.u8','study-landcover.u8','study-height.json','study-height.f32','local-landcover.u8','local-height.json','local-height.f32','study-context.json']],
 validation=dict(allFinite=True,localPrefixByteIdentical=True,rootHashAndHeightExactChecks=len(checks),duplicateXZCount=int(len(arr)-len(np.unique(arr[:,[0,2]],axis=0)))),
 limits=['Procedural mature-tree transform positions, heights, scales, rotations and variant assignments are project interpretations, not an individual-tree survey or species census.',
    'Mapped geology and landcover have different source dates, scales and semantics. Their intersection does not establish a forest boundary.',
    'Ground heights are bilinear samples of measured numerical DEM grids; trunks are sunk 0.06 m to match the existing local scene.',
    'Placement excludes approximate OSM road/trail buffers but does not describe public access or current trail conditions.'],
 elapsedSeconds=round(time.time()-start,2))
(ROOT/'forest-wide.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2))
print('DONE',json.dumps({k:metadata[k] for k in ['count','bytes','boundsMinXYZ','boundsMaxXYZ','validation','elapsedSeconds']}),flush=True)
