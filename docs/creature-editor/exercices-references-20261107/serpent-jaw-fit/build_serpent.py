"""Static coiled serpent silhouette for editor review, not game animation."""
from pathlib import Path
import hashlib,json
import numpy as np
import trimesh
from scipy.interpolate import splprep,splev

HERE=Path(__file__).resolve().parent
output=HERE/'serpent-coiled-v2.glb'
if output.exists(): raise FileExistsError(output)
nodes=[]
for t in np.linspace(0,1,28):
    a=2*np.pi*(1.4*t+.05);r=.78-.40*t
    nodes.append([r*np.cos(a),.14+.08*t,r*np.sin(a)])
nodes.extend([[-.40,.27,.18],[-.48,.42,.06],[-.48,.70,-.09],[-.39,1.00,-.22],[-.23,1.14,-.36]])
nodes=np.array(nodes);spline,_=splprep(nodes.T,s=.003,k=3)
u=np.linspace(0,1,280);centers=np.stack(splev(u,spline),axis=1)
tangent=np.stack(splev(u,spline,der=1),axis=1);tangent/=np.linalg.norm(tangent,axis=1)[:,None]
frame=[];last=np.array([0.,1.,0.])
for t in tangent:
    side=np.cross(last,t)
    if np.linalg.norm(side)<1e-5:side=np.cross([1.,0.,0.],t)
    side/=np.linalg.norm(side);up=np.cross(t,side);up/=np.linalg.norm(up);frame.append((side,up));last=up
vertices=[];colors=[]; sides=48
for i,(c,(side,up)) in enumerate(zip(centers,frame)):
    radius=.155*(.10+.90*min(1,u[i]/.18))*(1-.18*max(0,(u[i]-.78)/.22))
    for j,angle in enumerate(np.linspace(0,2*np.pi,sides,endpoint=False)):
        vertices.append(c+radius*(np.cos(angle)*side+np.sin(angle)*up))
        ventral=np.clip((-np.sin(angle)-.42)*3,0,1)
        pattern=.75+.25*(.5+.5*np.cos(i*.72+(j%2)*np.pi))* (.5+.5*np.cos(j*2.4))
        back=np.array([30,105,96])*pattern; belly=np.array([205,191,143])
        rgb=back*(1-ventral)+belly*ventral;colors.append([*rgb.astype(int),255])
faces=[]
for i in range(len(u)-1):
    for j in range(sides):
        a=i*sides+j;b=i*sides+(j+1)%sides;c=(i+1)*sides+j;d=(i+1)*sides+(j+1)%sides
        faces.extend([[a,b,c],[b,d,c]])
faces.extend([[0,j+1,j] for j in range(1,sides-1)])
last_ring=(len(u)-1)*sides;faces.extend([[last_ring,last_ring+j,last_ring+j+1] for j in range(1,sides-1)])
body=trimesh.Trimesh(vertices=np.array(vertices),faces=np.array(faces),process=False)
body.visual.vertex_colors=np.array(colors,dtype=np.uint8)
scene=trimesh.Scene();scene.add_geometry(body,node_name='coiled_body')
def ellipsoid(name,center,scale,color):
    mesh=trimesh.creation.icosphere(subdivisions=3,radius=1);mesh.apply_scale(scale);mesh.apply_translation(center)
    mesh.visual.vertex_colors=np.tile(color,(len(mesh.vertices),1));scene.add_geometry(mesh,node_name=name)
head=centers[-1]
ellipsoid('upper_jaw',head+[0,.045,-.08],[.19,.075,.28],[38,99,90,255])
ellipsoid('mouth_interior',head+[0,-.06,-.09],[.158,.035,.245],[70,20,24,255])
ellipsoid('lower_jaw',head+[0,-.095,-.09],[.16,.055,.25],[195,173,131,255])
for sign in (-1,1):
    ellipsoid('jaw_hinge_'+str(sign),head+[sign*.115,-.027,.075],[.065,.086,.065],[38,99,90,255])
def segment(name,start,end,radius,color):
    start=np.asarray(start);end=np.asarray(end);axis=end-start
    mesh=trimesh.creation.cylinder(radius=radius,height=np.linalg.norm(axis),sections=12)
    transform=trimesh.geometry.align_vectors([0,0,1],axis);transform[:3,3]=(start+end)/2;mesh.apply_transform(transform)
    mesh.visual.vertex_colors=np.tile(color,(len(mesh.vertices),1));scene.add_geometry(mesh,node_name=name)
for sign in (-1,1):
    ellipsoid('eye_'+str(sign),head+[sign*.14,.07,-.10],[.034,.030,.027],[228,177,44,255])
    ellipsoid('pupil_'+str(sign),head+[sign*.167,.073,-.113],[.009,.021,.010],[15,15,8,255])
    fang=trimesh.creation.cone(radius=.018,height=.13,sections=12)
    fang.apply_transform(trimesh.geometry.align_vectors([0,0,1],[0,-1,0]));fang.apply_translation(head+[sign*.105,.005,-.22])
    fang.visual.vertex_colors=np.tile([235,223,191,255],(len(fang.vertices),1));scene.add_geometry(fang,node_name='fang_'+str(sign))
segment('tongue_stem',head+[0,-.075,-.27],head+[0,-.12,-.48],.009,[145,32,37,255])
for sign in (-1,1):segment('tongue_tip_'+str(sign),head+[0,-.12,-.48],head+[sign*.035,-.13,-.56],.005,[145,32,37,255])
raw=scene.export(file_type='glb');output.write_bytes(raw)
manifest={'schema':'uo.creature-static-review/v1','status':'scaffolding_proxy','reference':'Designer (3).png',
          'glb':output.name,'sha256':hashlib.sha256(raw).hexdigest(),
          'limitations':['static procedural candidate','vertex colors only, no texture','no rig or animation','no game validation','visual review required']}
(HERE/'serpent-coiled-v2.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(HERE/'serpent-coiled-v2.recipe.json').write_text(json.dumps({'schema':'uo.serpent-coiled-review/v1','delivery':'review_only',
 'model_sha256':manifest['sha256'],'coils':1.4,'coil_radius_start_m':.78,'coil_radius_end_m':.38,
 'height_target_m':1.14,'sections':280,'sides':48,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2),encoding='utf8')
print(json.dumps({'sha256':manifest['sha256'],'triangles':len(body.faces),'mesh_count':len(scene.geometry)}))

