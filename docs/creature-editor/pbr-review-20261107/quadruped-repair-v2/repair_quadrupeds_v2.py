import bpy, math, json, hashlib
from mathutils import Vector, Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'quadruped-repair-v2'; OUT.mkdir(exist_ok=True)
summary={}
for animal in ['horse','sheep','llama']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=ROOT/'reassembled'/f'{animal}_pbr_review.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    changed=[]
    for o in meshes:
        name=o.name.split('.')[0]
        # Previous generators built cylinders along glTF Z while heights are glTF Y.
        if name not in ('leg_FL','leg_FR','leg_HL','leg_HR') and not (animal=='horse' and (name.endswith('_feathering') or name.endswith('_hoof'))): continue
        o.update_from_editmode(); o.matrix_world.inverted()
        pts=[o.matrix_world @ v.co for v in o.data.vertices]
        lo=Vector(tuple(min(p[i] for p in pts) for i in range(3))); hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
        center=(lo+hi)/2; rot=Matrix.Rotation(math.pi/2,4,'X'); inv=o.matrix_world.inverted()
        for v in o.data.vertices: v.co=inv @ (center + (rot.to_3x3() @ ((o.matrix_world @ v.co)-center)))
        if animal=='horse' and name in ('leg_FL','leg_FR','leg_HL','leg_HR'):
            world=[o.matrix_world @ v.co for v in o.data.vertices]
            top=max(v.z for v in world); bottom=min(v.z for v in world)
            for v in o.data.vertices:
                p=o.matrix_world @ v.co; p.z=top-(top-p.z)*(top-.28)/(top-bottom); v.co=inv @ p
        if animal=='horse' and name.endswith('_feathering'):
            for v in o.data.vertices:
                p=o.matrix_world @ v.co; p.y+=.175; v.co=inv @ p
        o.data.update(); changed.append(name)
    if animal=='horse':
        def sphere(name,loc,scale,color):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=loc)
            o=bpy.context.object;o.name=name;o.scale=scale
            mat=bpy.data.materials.new(name+'_review');mat.diffuse_color=(*color,1);mat.use_nodes=True
            mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1)
            mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.8
            o.data.materials.append(mat)
        sphere('horse_head_proxy',(0,.88,1.96),(.20,.30,.31),(.32,.14,.07))
        sphere('horse_muzzle_proxy',(0,1.13,1.78),(.15,.18,.14),(.48,.32,.23))
        for sign in (-1,1):
            sphere('horse_ear_proxy_'+str(sign),(sign*.13,.77,2.25),(.055,.06,.16),(.3,.12,.07))
            sphere('horse_eye_proxy_'+str(sign),(sign*.18,1.04,2.03),(.027,.025,.025),(.015,.01,.008))
    out=OUT/f'{animal}_pbr_repair.glb'
    bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',export_animations=True,export_skins=True,export_all_vertex_colors=True)
    summary[animal]={'source':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output':out.name,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'rotated_meshes':changed,'status':'static proxy review; seams, anatomy, UV and realistic texture unvalidated'}
    (OUT/'manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print('REPAIRED',animal,changed,flush=True)

