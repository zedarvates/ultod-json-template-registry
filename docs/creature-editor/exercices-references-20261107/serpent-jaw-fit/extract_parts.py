"""Extract static review pieces from the locally generated coiled serpent."""
from pathlib import Path
import hashlib,json
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'serpent-coiled-v2.glb'
SOURCE_SHA='6b855a891e88ece9855f7ed2729540c99743203a69673857a33a2af078cae94c'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA, 'Source changed'
source=trimesh.load(SOURCE,force='scene')
nodes={name:source.graph[name] for name in source.graph.nodes_geometry}
expected={'coiled_body','upper_jaw','lower_jaw','mouth_interior','jaw_hinge_-1','jaw_hinge_1','fang_-1','fang_1','tongue_stem','tongue_tip_-1','tongue_tip_1'}
if not expected.issubset(nodes):raise ValueError('Missing source nodes')
upper=source.geometry[nodes['upper_jaw'][1]].copy();upper.apply_transform(nodes['upper_jaw'][0]);bounds=upper.bounds
pivot=np.array([(bounds[0,0]+bounds[1,0])/2,(bounds[0,1]+bounds[1,1])/2,bounds[1,2]])
groups={'coiled_skin':(['coiled_body'],np.zeros(3)),
        'jaw_assembly':(['upper_jaw','lower_jaw','mouth_interior','jaw_hinge_-1','jaw_hinge_1','fang_-1','fang_1','tongue_stem','tongue_tip_-1','tongue_tip_1'],pivot)}
records={}
for name,(names,origin) in groups.items():
    target=HERE/(name+'.glb')
    if target.exists():raise FileExistsError(target)
    result=trimesh.Scene()
    for node in names:
        matrix,key=nodes[node];part=source.geometry[key].copy();part.apply_transform(matrix);part.apply_translation(-origin)
        result.add_geometry(part,node_name=node)
    data=result.export(file_type='glb');target.write_bytes(data)
    records[name]={'file':target.name,'sha256':hashlib.sha256(data).hexdigest(),'source_origin_m':origin.tolist(),'nodes':names}
doc={'schema':'uo.serpent-parts-review/v1','delivery':'review_only','source_sha256':SOURCE_SHA,
     'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parts':records,
     'limitations':['static extracted pieces','hinges overlap other meshes; surfaces not welded','no articulated rig','editor reassembly not verified','not game-ready']}
(HERE/'serpent-parts.recipe.json').write_text(json.dumps(doc,indent=2),encoding='utf8')
print(json.dumps(records))

