import bpy, bmesh, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'weld-review'; OUT.mkdir(exist_ok=True)
report={}
for name in ['horse','sheep','llama']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=ROOT/'quadruped-repair-v2'/f'{name}_pbr_repair.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    names={'geometry_0','leg_FL','leg_FR','leg_HL','leg_HR'}
    if name=='llama': names.add('neck_ruff')
    if name=='horse': names.update({'neck_crest','leg_FL_feathering','leg_FR_feathering','leg_HL_feathering','leg_HR_feathering'})
    selected=[o for o in objects if o.name.split('.')[0] in names]
    if not selected: raise RuntimeError('no body meshes '+name)
    joined_names=[o.name for o in selected]
    bpy.ops.object.select_all(action='DESELECT')
    for o in selected: o.select_set(True)
    body=next(o for o in selected if o.name.split('.')[0]=='geometry_0')
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    mod=body.modifiers.new('voxel junction review','REMESH'); mod.mode='VOXEL';mod.voxel_size=.025;mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    smooth=body.modifiers.new('relax review','SMOOTH');smooth.factor=.6;smooth.iterations=3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    body.name='welded_body_review'
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    bm=bmesh.new();bm.from_mesh(body.data)
    unvisited=set(bm.verts);components=[]
    while unvisited:
        seed=unvisited.pop();stack=[seed];size=1
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in unvisited: unvisited.remove(other);stack.append(other);size+=1
        components.append(size)
    bad=sum(1 for e in bm.edges if not e.is_manifold);bm.free()
    dest=OUT/f'{name}_weld_review.glb'
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',export_all_vertex_colors=True)
    report[name]={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'joined_nodes':joined_names,'body_components':len(components),'component_sizes':sorted(components,reverse=True),'nonmanifold_edges':bad,'voxel_size_m':.025,'status':'static experimental proxy; anatomical fidelity and seams require review'}
    (OUT/'weld_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('WELD',name,'components',len(components),'nonmanifold',bad,flush=True)
