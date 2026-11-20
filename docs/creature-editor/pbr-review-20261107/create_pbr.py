import bpy, math, json, hashlib, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'reference-pieces-20261107'
CASES = {
 'bull': ('bull/bull_rigged_walk.glb',(0.27,0.105,0.048),'hair'),
 'horse': ('cheval/cheval_rigged_walk.glb',(0.36,0.16,0.075),'hair'),
 'sheep': ('sheep/sheep_rigged_walk.glb',(0.72,0.66,0.53),'wool'),
 'llama': ('llama/llama_rigged_walk.glb',(0.56,0.35,0.20),'wool'),
 'rat': ('rat/rat_rigged_walk.glb',(0.27,0.22,0.17),'hair'),
 'crab': ('crab/crab_rigged_walk.glb',(0.57,0.19,0.08),'shell'),
 'snake': ('snake/serpent_rigged_walk.glb',(0.13,0.25,0.20),'scales'),
 'slime': ('gelee/slime_rigged_walk.glb',(0.08,0.43,0.62),'gel'),
}
SIZE=256
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def maps(name, color, kind):
    random.seed(4100 + sum(map(ord,name)))
    pix=[]; rough=[]; normal=[]
    for y in range(SIZE):
      for x in range(SIZE):
        u=x/SIZE; v=y/SIZE
        if kind=='scales':
          row=int(v*18); a=(u*24+(row%2)*.5)%1-.5; b=(v*18)%1-.5
          shape=max(0.,1.-math.sqrt((a/.53)**2+(b/.55)**2)); h=.45+.35*shape
        elif kind=='wool': h=.48+.15*math.sin(2*math.pi*(u*29+math.sin(v*31)*.3))*math.sin(v*math.pi*62)
        elif kind=='hair': h=.5+.14*math.sin(2*math.pi*(u*71+.12*math.sin(v*12)))
        elif kind=='shell': h=.52+.08*math.sin(u*81)*math.sin(v*53)
        else: h=.57+.035*math.sin(u*math.pi*8)*math.sin(v*math.pi*8)
        h=max(0,min(1,h+(random.random()-.5)*.07))
        pix.extend([max(0,min(1,c*(.68+h*.62))) for c in color]+[1])
        r={'hair':.83,'wool':.93,'scales':.57,'shell':.39,'gel':.16}[kind]
        r=max(0,min(1,r+(h-.5)*.16));rough.extend((r,r,r,1))
        # Neutral normal: height is not presented as measured surface geometry.
        normal.extend((.5,.5,1.,1.))
    paths={}
    for label,data,colorspace in [('basecolor',pix,'sRGB'),('roughness',rough,'Non-Color'),('normal',normal,'Non-Color')]:
      im=bpy.data.images.new(name+'_'+label,width=SIZE,height=SIZE,alpha=True)
      im.colorspace_settings.name=colorspace
      im.pixels.foreach_set(data); im.filepath_raw=str(ROOT/f'{name}_{label}.png'); im.file_format='PNG'; im.save()
      paths[label]=im
    return paths

report={}
for name,(relative,color,kind) in CASES.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=SRC/relative
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    if not objects: raise RuntimeError('no mesh: '+name)
    images=maps(name,color,kind)
    mat=bpy.data.materials.new('review_'+name); mat.use_nodes=True
    nt=mat.node_tree; bs=nt.nodes.get('Principled BSDF')
    def image_node(label):
      n=nt.nodes.new('ShaderNodeTexImage'); n.image=images[label]; return n
    nt.links.new(image_node('basecolor').outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(image_node('roughness').outputs['Color'],bs.inputs['Roughness'])
    normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(image_node('normal').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    bs.inputs['Metallic'].default_value=0
    if name=='slime': bs.inputs['Alpha'].default_value=.67; mat.surface_render_method='DITHERED'
    for obj in objects:
      bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
      bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.uv.smart_project(island_margin=0.02)
      bpy.ops.object.mode_set(mode='OBJECT')
      obj.data.materials.clear();obj.data.materials.append(mat)
      for poly in obj.data.polygons: poly.material_index=0
    dest=ROOT/(name+'_pbr_review.glb')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_animations=True,export_skins=True)
    report[name]={'source':str(source),'source_sha256':sha(source),'output':dest.name,'output_sha256':sha(dest),'mesh_count':len(objects),'material':kind,'maps':{k:{'file':Path(v.filepath_raw).name,'sha256':sha(Path(v.filepath_raw))} for k,v in images.items()},'limitations':['procedural review textures, not photorealistic','neutral normal map; no measured microgeometry','single material per creature; source material regions replaced','UV layout and seams need visual inspection','rig and animation remain unvalidated']}
    (ROOT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('PBR_REVIEW_EXPORTED',name,flush=True)
