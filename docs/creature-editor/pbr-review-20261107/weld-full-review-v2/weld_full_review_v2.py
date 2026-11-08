import bpy, bmesh, json, hashlib
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'weld-full-review-v2'; OUT.mkdir(exist_ok=True)
report={}
for name in ['horse','sheep','llama']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=ROOT/'quadruped-repair-v2'/f'{name}_pbr_repair.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for obj in objects:
        lower=obj.name.lower()
        if 'eye' in lower or lower.endswith('_hoof') or lower.endswith('_foot'):
            mat=bpy.data.materials.new('review_eye' if 'eye' in lower else 'review_hoof')
            mat.use_nodes=True
            bs=mat.node_tree.nodes.get('Principled BSDF')
            bs.inputs['Base Color'].default_value=(.012,.009,.006,1) if 'eye' in lower else (.065,.047,.032,1)
            bs.inputs['Roughness'].default_value=.2 if 'eye' in lower else .7
            obj.data.materials.clear();obj.data.materials.append(mat)
    selected=[o for o in objects if 'eye' not in o.name.lower()]
    if not selected: raise RuntimeError('no body meshes '+name)
    joined_names=[o.name for o in selected]
    bpy.ops.object.select_all(action='DESELECT')
    for o in selected: o.select_set(True)
    body=next(o for o in selected if o.name.split('.')[0]=='geometry_0')
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.join()
    vertices=[v.co.copy() for v in body.data.vertices]
    polygons=[tuple(p.vertices) for p in body.data.polygons]
    slots=[p.material_index for p in body.data.polygons]
    tree=BVHTree.FromPolygons(vertices,polygons,all_triangles=False)
    mod=body.modifiers.new('voxel junction review','REMESH'); mod.mode='VOXEL';mod.voxel_size=.025;mod.use_smooth_shade=True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    smooth=body.modifiers.new('relax review','SMOOTH');smooth.factor=.6;smooth.iterations=3
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    for poly in body.data.polygons:
        nearest=tree.find_nearest(poly.center)
        if nearest and nearest[2] is not None: poly.material_index=slots[nearest[2]]
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
    report[name]={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'joined_nodes':joined_names,'body_components':len(components),'component_sizes':sorted(components,reverse=True),'nonmanifold_edges':bad,'voxel_size_m':.025,'status':'static experimental proxy; nearest-surface material transfer; eyes excluded; UV and fidelity require review'}
    (OUT/'weld_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('WELD',name,'components',len(components),'nonmanifold',bad,flush=True)
