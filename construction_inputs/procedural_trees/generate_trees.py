"""Deterministic, original procedural tree meshes. Y-up, metres, base at zero.
No source photo or third-party mesh is embedded in the geometry.
"""
from pathlib import Path
import json, math, hashlib
import numpy as np

OUT=Path(__file__).resolve().parent


def unit(v):
    v=np.asarray(v,dtype=float)
    return v/(np.linalg.norm(v)+1e-12)

def frame(axis):
    axis=unit(axis)
    ref=np.array([0.,1.,0.]) if abs(axis[1])<.85 else np.array([1.,0.,0.])
    side=unit(np.cross(axis,ref))
    return side,unit(np.cross(side,axis))

class Mesh:
    def __init__(self):self.p=[];self.n=[];self.uv=[];self.c=[];self.i=[]
    def vertex(self,p,n,uv,c):
        self.p.append(p);self.n.append(n);self.uv.append(uv);self.c.append(c)
        return len(self.p)-1
    def tube(self,points,radii,sides=6,color=(.49,.45,.36,1),uv_scale=(.7,1.8),phase=0,cap=True):
        points=np.asarray(points);radii=np.asarray(radii)
        rings=[];dist=0.
        for j,(point,r) in enumerate(zip(points,radii)):
            if j:dist+=np.linalg.norm(point-points[j-1])
            tangent=unit(points[min(j+1,len(points)-1)]-points[max(j-1,0)])
            side,up=frame(tangent)
            ring=[]
            for k in range(sides+1):
                a=2*math.pi*k/sides+phase
                normal=math.cos(a)*side+math.sin(a)*up
                # modest longitudinal fluting; no random high-frequency noise
                uneven=1+.07*math.sin(3*a+.25*j)+.035*math.cos(5*a-.12*j)
                p=point+normal*r*uneven
                # trunk/root intersection below the model datum is flattened
                p[1]=max(0.,p[1])
                ring.append(self.vertex(p,normal,[k/sides*2*math.pi*r/uv_scale[0],dist/uv_scale[1]],color))
            rings.append(ring)
        for j in range(len(rings)-1):
            for k in range(sides):
                a,b,c,d=rings[j][k],rings[j][k+1],rings[j+1][k],rings[j+1][k+1]
                self.i.extend([[a,c,b],[b,c,d]])
        for j in ([0,len(rings)-1] if cap else []):
            tangent=unit(points[min(j+1,len(points)-1)]-points[max(j-1,0)])*(-1 if j==0 else 1)
            center=self.vertex(points[j],tangent,[.5,.5],color)
            for k in range(sides):
                self.i.append([center,rings[j][k],rings[j][k+1]] if j==0 else [center,rings[j][k+1],rings[j][k]])
    def leaf(self,base,direction,normal,length,width,color,curl=.09):
        direction=unit(direction);normal=unit(normal-direction*np.dot(direction,normal));side=unit(np.cross(direction,normal))
        # Bent lance/kite: two faces with a raised tip; no alpha cutout.
        ps=[base,base+direction*length*.44-side*width*.50,base+direction*length+normal*length*curl,base+direction*length*.58+side*width*.50]
        uvs=[[.5,0],[0,.44],[.5,1],[1,.58]]
        ids=[self.vertex(p,normal,uv,color) for p,uv in zip(ps,uvs)]
        self.i.extend([[ids[0],ids[2],ids[1]],[ids[0],ids[3],ids[2]]])
    def blob(self,center,radii,rng,segments=8,rings=4,color=(.20,.31,.13,1)):
        # Irregular closed lobed canopy cluster for lower LOD, never a cone/billboard.
        center=np.asarray(center);radii=np.asarray(radii)
        ids=[]
        top=self.vertex(center+[0,radii[1],0],[0,1,0],[.5,1],color)
        for j in range(1,rings):
            theta=math.pi*j/rings;row=[]
            for k in range(segments):
                phi=2*math.pi*k/segments
                n=np.array([math.sin(theta)*math.cos(phi),math.cos(theta),math.sin(theta)*math.sin(phi)])
                fac=1+.12*math.sin(3*phi+j*.7)+rng.uniform(-.06,.06)
                pos=center+n*radii*fac
                row.append(self.vertex(pos,unit(n/radii),[k/segments,1-j/rings],color))
            ids.append(row)
        bottom=self.vertex(center-[0,radii[1],0],[0,-1,0],[.5,0],color)
        for k in range(segments):
            k1=(k+1)%segments
            self.i.append([top,ids[0][k1],ids[0][k]])
            self.i.append([bottom,ids[-1][k],ids[-1][k1]])
        for j in range(len(ids)-1):
            for k in range(segments):
                k1=(k+1)%segments
                self.i.extend([[ids[j][k],ids[j][k1],ids[j+1][k]],[ids[j][k1],ids[j+1][k1],ids[j+1][k]]])
    def arrays(self):
        positions=np.asarray(self.p,dtype=np.float32)
        normals=np.asarray(self.n,dtype=np.float32)
        indices=np.asarray(self.i,dtype=np.uint32)
        cross=np.cross(positions[indices[:,1]]-positions[indices[:,0]],positions[indices[:,2]]-positions[indices[:,0]])
        reverse=np.einsum('ij,ij->i',cross,normals[indices].mean(1))<0
        indices[reverse]=indices[reverse][:,[0,2,1]]
        return dict(positions=positions,normals=normals,uv=np.asarray(self.uv,dtype=np.float32),indices=indices,colors=np.asarray(self.c,dtype=np.float32))
    def save(self,p):
        a=self.arrays();np.savez_compressed(p,**a)
        return {'path':str(p),'vertices':len(a['positions']),'triangles':len(a['indices']),'bounds_min':a['positions'].min(0).tolist(),'bounds_max':a['positions'].max(0).tolist(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def interp(points,t):
    j=t*(len(points)-1);i=min(int(j),len(points)-2);f=j-i
    return points[i]*(1-f)+points[i+1]*f


def curved_branch(start,end,bow,radius,rng,segments=6):
    t=np.linspace(0,1,segments+1)
    points=np.array([start+(end-start)*q+bow*math.sin(math.pi*q) for q in t])
    radii=radius*(1-t)**1.1+.004
    return points,radii


def green(rng,evergreen,tip=0):
    if evergreen:
        base=np.array([.135,.235,.095]);v=rng.uniform(.8,1.27)
    else:
        base=np.array([.21,.335,.11]);v=rng.uniform(.75,1.25)
    c=base*v+np.array([.045,.05,.017])*tip
    return [*np.clip(c,0,1),1.]


def build(name,seed,height,evergreen,kind):
    rng=np.random.default_rng(seed)
    bark,leaves,lodbark,lodleaves=Mesh(),Mesh(),Mesh(),Mesh()
    bend=rng.normal(size=2);bend=unit(bend)*rng.uniform(.38,.75)
    trunk=[]
    for t in np.linspace(0,1,19):
        trunk.append([bend[0]*t*t+.12*math.sin(t*7),height*t,bend[1]*t*t+.1*math.sin(t*5)])
    trunk=np.array(trunk)
    trunk_radius=.39 if evergreen else .46
    ts=np.linspace(0,1,len(trunk))
    rr=trunk_radius*(1-ts)**.82+.012
    bark.tube(trunk,rr,10)
    lodbark.tube(trunk[::3],rr[::3],5)
    # Surface roots splay irregularly from the buttress into the ground.
    for j in range(8):
        ang=j*2*math.pi/8+rng.uniform(-.22,.22)
        span=rng.uniform(1.2,2.3)
        points=[];radii=[]
        for t in np.linspace(0,1,6):
            r=.17*(1-t)**1.3+.012
            a=ang+.24*math.sin(t*2)
            points.append([math.cos(a)*span*t,r*.8+.035*(1-t),math.sin(a)*span*t])
            radii.append(r)
        bark.tube(points,radii,6)
        if j%2==0:lodbark.tube(np.array(points)[::2],np.array(radii)[::2],4)
    primary_count=20 if evergreen else 15
    canopy=[]
    for j in range(primary_count):
        # Golden-angle phyllotaxis with missing sectors, not rotational layers.
        if evergreen:
            level=.27+.66*j/(primary_count-1)+rng.uniform(-.018,.018)
            spread=(4.25 if kind=='hemlock' else 3.7)*(1-(level-.22)/.82)**.62*rng.uniform(.77,1.2)
            rise=rng.uniform(-.25,.9) if kind=='hemlock' else rng.uniform(.1,1.25)
        else:
            level=rng.uniform(.40,.71)
            spread=rng.uniform(3.4,5.8)*(1 if kind=='oak' else .90)
            rise=rng.uniform(2.2,5.6)
        a=j*2.399963+rng.uniform(-.28,.28)
        radial=np.array([math.cos(a),0,math.sin(a)])
        start=interp(trunk,level)
        end=start+radial*spread+np.array([0,rise,0])
        bow=radial*.15+np.array([0,-.55 if evergreen else .42,0])
        p,r=curved_branch(start,end,bow,.10 if evergreen else .135,rng,7)
        bark.tube(p,r,6)
        if j%2==0:lodbark.tube(p[::2],r[::2],4)
        secondary_count=6
        for k in range(secondary_count):
            t=.29+.66*k/(secondary_count-1)
            origin=interp(p,t)
            tangent=unit(end-start)
            sign=1 if (k+j)%2 else -1
            sideways=np.array([-radial[2],0,radial[0]])*sign
            if evergreen:
                length=rng.uniform(.6,1.35)*(1-.3*t)
                secdir=unit(radial*.38+sideways*.86+np.array([0,rng.uniform(-.12,.30),0]))
                secend=origin+secdir*length+np.array([0,-.17 if kind=='hemlock' else .1,0])
            else:
                length=rng.uniform(.9,1.65)
                secdir=unit(radial*.25+sideways*.50+np.array([0,rng.uniform(.5,1.2),0]))
                secend=origin+secdir*length
            sp,sr=curved_branch(origin,secend,np.array([0,.1,0]),.026 if evergreen else .034,rng,4)
            bark.tube(sp,sr,4)
            canopy.append((secend,radial,evergreen))
            shoot_count=3 if evergreen else 4
            for q in range(shoot_count):
                st=interp(sp,.43+.56*q/(shoot_count-1))
                spin=rng.uniform(-1,1)
                shootdir=unit(secdir*.5+sideways*spin*.7+np.array([0,rng.uniform(-.12,.75),0]))
                shootlen=rng.uniform(.46,.78) if evergreen else rng.uniform(.50,.86)
                shootend=st+shootdir*shootlen
                tp,tr=curved_branch(st,shootend,np.array([0,.035,0]),.007 if evergreen else .008,rng,2)
                bark.tube(tp,tr,3,cap=False)
                side,normal=frame(shootdir)
                # Most spray planes face upward but with independent modest twists.
                normal=unit(normal*np.cos(spin)+side*np.sin(spin))
                if normal[1]<0:normal=-normal
                side=unit(np.cross(shootdir,normal))
                nleaf=19 if evergreen else 22
                for m in range(nleaf):
                    fraction=(m+.6)/(nleaf+.8)
                    originleaf=interp(tp,fraction)
                    side_sign=1 if m%2 else -1
                    direction=unit(shootdir*.45+side*side_sign*.82+normal*rng.uniform(-.08,.20))
                    length=rng.uniform(.16,.25) if evergreen else rng.uniform(.16,.27)
                    if evergreen and kind=='cypress':length*=.85
                    width=length*(rng.uniform(.10,.19) if evergreen else rng.uniform(.47,.66))
                    color=green(rng,evergreen,fraction*.3)
                    leaves.leaf(originleaf,direction,normal,length,width,color,curl=.04 if evergreen else .09)
        # End tuft makes tips terminate in actual foliage rather than naked sticks.
        side,normal=frame(unit(end-start))
        for k in range(14):
            direction=unit(radial*.25+side*rng.uniform(-1,1)+np.array([0,rng.uniform(.1,.6),0]))
            leaves.leaf(end+direction*rng.uniform(0,.10),direction,normal,rng.uniform(.18,.30),.04 if evergreen else .12,green(rng,evergreen,.7))
    # Upper leader sprigs for evergreen trees; broadleaf leader is hidden in crown.
    if True:
        for j in range(18):
            t=.85+.145*j/18
            a=j*2.39996
            start=interp(trunk,t);direction=unit([math.cos(a),.35,math.sin(a)])
            length=.55*(1-(t-.85)/.17)+.1
            end=start+direction*length
            p,r=curved_branch(start,end,np.array([0,.04,0]),.012,rng,3)
            bark.tube(p,r,4)
            side,normal=frame(direction)
            for k in range(14):
                sign=1 if k%2 else -1
                leaves.leaf(interp(p,(k+.5)/15),unit(direction*.35+side*sign),normal,.19 if evergreen else .26,.036 if evergreen else .14,green(rng,evergreen,.6))
    # Simplified canopy clusters follow actual endpoints, grouped every 6/7 nodes.
    stride=7 if evergreen else 6
    for i in range(0,len(canopy),stride):
        group=canopy[i:i+stride]
        centers=np.array([x[0] for x in group]);center=centers.mean(0)
        ext=np.ptp(centers,axis=0)*.42+np.array([.7,.36 if evergreen else .65,.7])
        ext=np.clip(ext,[.65,.30,.65],[1.85,1.25,1.85])
        lodleaves.blob(center,ext,rng,segments=7,rings=3,color=green(rng,evergreen))
    # Merge a modest upper leader canopy into an irregular ellipsoid.
    if evergreen:
        lodleaves.blob(interp(trunk,.92),[.75,height*.065,.7],rng,7,3,green(rng,True,.5))
    directory=OUT/name;directory.mkdir(exist_ok=True)
    files={}
    for level,meshes in [('high',{'bark':bark,'leaves':leaves}),('low',{'bark':lodbark,'leaves':lodleaves})]:
        files[level]={k:mesh.save(directory/f'{level}_{k}.npz') for k,mesh in meshes.items()}
        files[level]['triangles_total']=sum(v['triangles'] for v in files[level].values())
    meta={'variant':name,'seed':seed,'units':'metres','up_axis':'Y','origin':'trunk centre at ground; minimum y=0','approximate_leader_height_m':height,
          'description':{'hemlock':'Asymmetric evergreen with long drooping lateral sprays; suggestive of Tsuga structure, not a botanically exact species.','cypress':'Slender evergreen with ascending branches and flattened lance sprays; suggestive of Chamaecyparis, not a botanical specimen.','oak':'Broad deciduous crown with rising scaffold branches, irregular bent leaves.','beech':'Leaning broadleaf crown with more upright limb distribution and bent oval-lance leaves.'}[kind],
          'procedural_status':'Entire tree is original deterministic procedural geometry; not an observed individual Aokigahara tree, scanned species or surveyed placement.',
          'material_slots':{'bark':{'double_sided':False,'uv_repeat_metres':{'around_branch':.7,'along_branch':1.8},'note':'Approximate physical UV repeats; rings vary with tapered circumference. Use white basecolor multiplier if applying bark texture; vertex tint optional.'},'leaves':{'double_sided':True,'alpha_mode':'OPAQUE','vertex_colors':'RGBA linear-like natural green tints, not calibrated leaf reflectance','note':'Folded single-surface leaf/spray geometry. Enable double sided rendering/export material. No alpha or billboard textures.'}},
          'lod_note':'High has individually modelled foliage sprigs/leaves and tapered branches. Low has closed irregular ellipsoidal crown lobes, no cones or billboards. LODs share local origin but crown silhouettes are approximate.',
          'files':files}
    (directory/'manifest.json').write_text(json.dumps(meta,indent=2))
    return meta

if __name__=='__main__':
    variants=[('evergreen_spreading',73621,17.0,True,'hemlock'),('evergreen_ascending',83019,19.0,True,'cypress'),('broadleaf_spreading',99347,14.5,False,'oak'),('broadleaf_leaning',17429,16.2,False,'beech')]
    records=[build(*v) for v in variants]
    (OUT/'manifest.json').write_text(json.dumps({'generator':'generate_trees.py','generator_version':'1','provenance':'Original procedural geometry generated for this task; no third-party mesh copied. Species and site placement are interpretive.','arrays':{'positions':'float32 (N,3)','normals':'float32 (N,3)','uv':'float32 (N,2)','indices':'uint32 (M,3)','colors':'float32 RGBA (N,4)'},'variants':records},indent=2))
    for r in records:print(r['variant'],r['files']['high']['triangles_total'],r['files']['low']['triangles_total'])
