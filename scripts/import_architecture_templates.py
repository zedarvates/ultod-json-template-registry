#!/usr/bin/env python3
"""Import versioned, locally qualified HouseBlueprints into the public registry."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.template_contract import (KEBAB, SEMVER, compute_spec_checksum, decode_json_bytes,
                                       validate_with_schema)
from scripts.validate_registry import validate_public_content

FAMILY = 'architecture-editor'
COLLECTION = 'old-school-90s-mmorpg-like'
SCHEMA = f'templates/schemas/{FAMILY}/v1.0.0/schema.json'
CATALOG = 'templates/catalog.json'
INDEX = f'templates/{FAMILY}/README.md'
GALLERY = f'templates/{FAMILY}/GALERIE.md'
SHA = re.compile(r'^[a-f0-9]{64}$')
PRIVATE_VALUE = re.compile(r'://|[A-Za-z]:[\\/]|[\\/]{2}|(?:^|\s)localhost\b|[<>\x00-\x1f]',re.I)

FIELDS = {
    'root': 'blueprint_id name kind lot floors roof garden props ornaments sub_basement building_params decor_options runtime_profile medieval_profile style_id',
    'lot': 'width depth cell_size floor_height',
    'floor': 'level tiles walls',
    'tile': 'x z part_id material_lib',
    'wall': 'x z edge part_id stack material_lib',
    'roof': 'x z part_id rotation material_lib',
    'props': 'prop_id x z floor rotation',
    'ornaments': 'ornament_id x z edge floor',
    'sub_basement': 'enabled height',
    'building_params': 'roof_pitch_deg flat_parapet_enabled flat_parapet_height flat_crenellation_enabled',
    'decor_options': 'charpente cheminee_auto cache_moineaux crete_coq lambrequins gouttieres soupirails',
    'runtime_profile': 'budget_class collision_enabled collide_props collision_layer collision_mask hlod_scene',
    'medieval_profile': 'version enabled seed wear timberDepth roof shutters braces',
}
CHILDREN = {'root': {'lot':'lot','floors':['floor'],'roof':['roof'],'props':['props'],
                     'ornaments':['ornaments'],'sub_basement':'sub_basement',
                     'building_params':'building_params','decor_options':'decor_options',
                     'runtime_profile':'runtime_profile','medieval_profile':'medieval_profile'},
            'floor':{'tiles':['tile'],'walls':['wall']}}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value, compact=False):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       **({'separators':(',', ':')} if compact else {'indent':2}))+'\n').encode()


def read(path):
    return decode_json_bytes(path.read_bytes())


def verify_recipe(value, group='root'):
    if not isinstance(value, dict) or set(value)-set(FIELDS[group].split()):
        raise ValueError(f'unsupported fields in {group}; review before public import')
    for key, field in value.items():
        child=CHILDREN.get(group,{}).get(key)
        if isinstance(child,list):
            if not isinstance(field,list):
                raise ValueError(f'{key} must be an array')
            for item in field:
                verify_recipe(item,child[0])
        elif child:
            verify_recipe(field,child)
        elif key=='garden' and field==[]:
            continue
        elif type(field) not in (str,bool,int,float):
            raise ValueError(f'unsupported value in {group}.{key}')
        elif isinstance(field,str) and (len(field)>140 or PRIVATE_VALUE.search(field)):
            raise ValueError(f'private path or unsupported string in {group}.{key}')
    if group=='root':
        if not re.fullmatch(r'uo_regen_multi_[0-9]{4}_v1',value.get('blueprint_id','')):
            raise ValueError('expected an original regenerated architecture identifier')
        if not {'name','lot','floors'}<=value.keys() or not value['floors']:
            raise ValueError('incomplete HouseBlueprint')
        if validate_public_content(value):
            raise ValueError('recipe violates public registry policy')


def generate_index(entries, documents):
    lines=['# Éditeur d’architecture — Old School 90s MMORPG Like','',
           '[**Voir la galerie des architectures en images**](GALERIE.md)','',
           'Recettes HouseBlueprint à importer avec **Importer un .json** dans l’éditeur. '
           'Chaque version est immuable et accompagnée d’une capture réelle de la vue 3D.','',
           'Les preuves couvrent le validateur Zig local et l’aperçu dans l’éditeur. '
           'Les captures montrent le GLB de revue ; ni le GLB ni le code du serveur ne sont distribués ici.','',
           '| Modèle | Version | Recette | Capture |','|---|---|---|---|']
    for entry in sorted(entries,key=lambda e:(e['slug'],tuple(map(int,e['version'].split('.'))))):
        spec=documents[entry['file']]['spec']
        name=spec['display_name'].replace('|','\\|')
        local=Path(entry['file']).relative_to(f'templates/{FAMILY}').as_posix()
        lines.append(f"| {name} | [{entry['version']}]({local}) | [JSON](../../{spec['recipe_file']}) | [Aperçu](../../{spec['preview_file']}) |")
    return ('\n'.join(lines)+'\n').encode()


def generate_gallery(entries, documents, root=ROOT):
    latest={}
    for entry in entries:
        previous=latest.get(entry['slug'])
        version=lambda e:tuple(map(int,e['version'].split('.')))
        if previous is None or version(entry)>version(previous):
            latest[entry['slug']]=entry
    ordered=[latest[slug] for slug in sorted(latest)]
    lines=['# Galerie des architectures — Old School 90s MMORPG Like','',
           f'**{len(ordered)} architectures** · Dernière version publiée de chaque modèle. '
           'Cliquer sur une image pour l’agrandir, ou sur le nom pour ouvrir la fiche.','',
           '[Toutes les versions et leurs recettes](README.md) · [Accueil du dépôt](../../README.md)','',
           'Aperçus des modèles de revue. Les fiches précisent les contrôles réalisés ; '
           'ces images ne certifient pas la compatibilité avec le serveur actif ni le photoréalisme global.','',
           '| Architecture | Architecture | Architecture |','|---|---|---|']
    cards=[]
    extra=[]
    for entry in ordered:
        spec=documents[entry['file']]['spec']
        name=spec['display_name'].replace('|','\\|')
        folder=Path(entry['file']).parent.relative_to(f'templates/{FAMILY}').as_posix()
        preview='../../'+spec['preview_file']
        links=f"[Plan JSON](../../{spec['recipe_file']})"
        assets=Path(spec['recipe_file']).parent
        if (root/assets/'surface-recipe.json').is_file():
            links+=f' · [Profil de surfaces](../../{assets.as_posix()}/surface-recipe.json)'
        cards.append(f'[![{name}]({preview})]({preview})<br>'
                     f"**[{name}]({folder}/README.md)**<br>v{entry['version']} · {links}")
        native=[]
        for filename,label in (('native-near-parallax.jpg','Parallax de proximité'),
                               ('native-interior-daylight.jpg','Intérieur sous éclairage de revue')):
            path=assets/filename
            if (root/path).is_file():
                url='../../'+path.as_posix()
                native.append((label,f'[![{label}]({url})]({url})<br>{label}'))
        if native:
            extra.extend(['',f"## {name} — vues dans Trammel privé, v{entry['version']}",'',
                          'Captures complémentaires du client privé. La vue intérieure utilise un profil temporaire de lumière de revue. '
                          f'[Détails des vérifications]({folder}/README.md).','',
                          '| '+' | '.join(label for label,_ in native)+' |',
                          '| '+' | '.join('---' for _ in native)+' |',
                          '| '+' | '.join(cell for _,cell in native)+' |'])
    for start in range(0,len(cards),3):
        row=cards[start:start+3]
        lines.append('| '+' | '.join(row+['']*(3-len(row)))+' |')
    lines.extend(extra)
    return ('\n'.join(lines)+'\n').encode()


def import_batch(root, batch, validator, *, apply):
    catalog=read(root/CATALOG)
    entries=catalog['entries']
    by_file={e['file']:e for e in entries}
    schema=(root/SCHEMA).read_bytes()
    pending={}
    incoming=[]
    if SCHEMA not in by_file:
        incoming.append({'name':FAMILY,'kind':'json-schema','version':'1.0.0','status':'experimental',
                         'file':SCHEMA,'sha256':sha(schema),'compatibility':[],
                         'validation_profile':'strict-schema-v1','contract_version':'1.0.0'})
    documents={e['file']:read(root/e['file']) for e in entries if e.get('family')==FAMILY}
    for row in batch:
        slug,version=row['slug'],row['version']
        if not KEBAB.fullmatch(slug) or len(slug)>64 or not SEMVER.fullmatch(version):
            raise ValueError('invalid slug or version')
        blueprint=read(Path(row['blueprint']))
        verify_recipe(blueprint)
        recipe=encoded(blueprint,compact=True)
        if len(recipe)>262144:
            raise ValueError('native input exceeds validator budget')
        preview=Path(row['preview']).read_bytes()
        if len(preview)>1_000_000 or not preview.startswith(b'\xff\xd8\xff') or not preview.endswith(b'\xff\xd9'):
            raise ValueError('capture must be a JPEG smaller than 1 MB')
        if not SHA.fullmatch(row['reviewed_model_sha256']):
            raise ValueError('missing reviewed model hash')
        with tempfile.TemporaryDirectory() as temp:
            candidate=Path(temp)/'blueprint.json'
            candidate.write_bytes(recipe)
            result=subprocess.run([str(validator),str(candidate)],capture_output=True,timeout=20)
        zig=decode_json_bytes(result.stdout or result.stderr)
        if result.returncode or zig.get('status')!='PASS' or not isinstance(zig.get('parts'),int):
            raise ValueError(f'Zig rejected {slug}')
        template=f'templates/{FAMILY}/{slug}/v{version}/template.json'
        assets=f'assets/{FAMILY}/{slug}/v{version}'
        spec={'display_name':blueprint['name'],'collection':COLLECTION,'recipe_format':'house-blueprint',
              'recipe_file':assets+'/blueprint.json','recipe_sha256':sha(recipe),
              'preview_file':assets+'/preview.jpg','preview_sha256':sha(preview),
              'reviewed_model_sha256':row['reviewed_model_sha256'],'zig_parts':zig['parts'],
              'evidence_scope':'local-zig-and-editor-preview'}
        document={'$schema':f'../../../schemas/{FAMILY}/v1.0.0/schema.json','contract_version':'1.0.0',
                  'id':f'{FAMILY}:{slug}','slug':slug,'family':FAMILY,'version':version,'authority':'declarative',
                  'intended_consumers':['architecture-editor'],'compatibility':[],'dependencies':[],
                  'spec_checksum':compute_spec_checksum(spec),'spec':spec}
        errors=validate_with_schema(root,SCHEMA,document)
        if errors:
            raise ValueError(f'{slug}: {errors}')
        members={template:encoded(document),spec['recipe_file']:recipe,spec['preview_file']:preview}
        if template in by_file:
            if any(not (root/k).is_file() or (root/k).read_bytes()!=v for k,v in members.items()):
                raise FileExistsError(f'{slug} v{version} is immutable; use another version')
            continue
        if any(k in pending or (root/k).exists() for k in members):
            raise FileExistsError(f'incomplete or duplicate version: {slug} v{version}')
        prev=[e for e in entries+incoming if e.get('id')==document['id']]
        ver=lambda v:tuple(map(int,v.split('.')))
        if prev and ver(version)<=max(ver(e['version']) for e in prev):
            raise ValueError(f'{slug} requires a strictly newer version')
        entry={k:document[k] for k in ('id','slug','family','version','contract_version','spec_checksum','intended_consumers','compatibility')}
        entry.update(name=slug,kind='architecture-editor-template',status='experimental',validation_profile='strict-v1',
                     file=template,schema_file=SCHEMA,sha256=sha(members[template]))
        if prev:
            entry['supersedes']=[f"{document['id']}@{max(prev,key=lambda e:ver(e['version']))['version']}"]
        incoming.append(entry)
        documents[template]=document
        pending.update(members)
        pending[template.replace('template.json','README.md')]=(
            f"# {blueprint['name']} — v{version}\n\n"
            "Statut expérimental. Consommateur : éditeur d’architecture. "
            "Plan vérifié par Zig en local et capture du modèle de revue. "
            "Aucune compatibilité avec le serveur de jeu actif n’est certifiée.\n\n"
            f"[Importer le JSON](../../../../{spec['recipe_file']})\n\n"
            f"![Capture du modèle de revue](../../../../{spec['preview_file']})\n"
        ).encode()
    if apply and incoming:
        for k,v in pending.items():
            target=root/k
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:
                f.write(v)
        entries.extend(incoming)
        (root/CATALOG).write_bytes(encoded(catalog))
        (root/INDEX).write_bytes(generate_index([e for e in entries if e.get('family')==FAMILY],documents))
        (root/GALLERY).write_bytes(generate_gallery([e for e in entries if e.get('family')==FAMILY],documents,root))
    return sum(e.get('family')==FAMILY for e in incoming)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path,help='private JSON array; keep local paths outside git')
    p.add_argument('--validator',required=True,type=Path,help='local Zig HouseBlueprint validator')
    p.add_argument('--apply',action='store_true',help='write new versions; default is dry run')
    args=p.parse_args()
    print(f'{import_batch(ROOT,read(args.manifest),args.validator.resolve(),apply=args.apply)} new recipes ({ "applied" if args.apply else "dry run"})')


if __name__=='__main__':
    main()
