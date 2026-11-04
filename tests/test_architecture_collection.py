"""Keep native recipes and their visual evidence bound to the registry catalog."""
import json
import re
from pathlib import Path
import unittest

from scripts.import_architecture_templates import FAMILY, ROOT, sha, verify_recipe, generate_index, generate_gallery


class ArchitectureCollectionTest(unittest.TestCase):
    def test_downloads_match_every_architecture_version(self):
        catalog=json.loads((ROOT/'templates/catalog.json').read_bytes())
        entries=[e for e in catalog['entries'] if e.get('family')==FAMILY]
        self.assertTrue(entries)
        documents={}
        for entry in entries:
            with self.subTest(template=entry['file']):
                document=json.loads((ROOT/entry['file']).read_bytes())
                documents[entry['file']]=document
                spec=document['spec']
                base=f"assets/{FAMILY}/{entry['slug']}/v{entry['version']}"
                self.assertEqual(spec['recipe_file'],f'{base}/blueprint.json')
                self.assertEqual(spec['preview_file'],f'{base}/preview.jpg')
                recipe=(ROOT/spec['recipe_file']).read_bytes()
                preview=(ROOT/spec['preview_file']).read_bytes()
                self.assertEqual(sha(recipe),spec['recipe_sha256'])
                self.assertEqual(sha(preview),spec['preview_sha256'])
                verify_recipe(json.loads(recipe))
                self.assertTrue(preview.startswith(b'\xff\xd8\xff'))
                self.assertTrue(preview.endswith(b'\xff\xd9'))
        self.assertEqual((ROOT/f'templates/{FAMILY}/README.md').read_bytes(),generate_index(entries,documents))
        gallery_path=ROOT/f'templates/{FAMILY}/GALERIE.md'
        gallery=gallery_path.read_text(encoding='utf-8')
        self.assertEqual(gallery_path.read_bytes(),generate_gallery(entries,documents))
        self.assertEqual(gallery.count('**['),len({e['slug'] for e in entries}))
        for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\s]+)\)',gallery):
            linked=(gallery_path.parent/target).resolve()
            self.assertTrue(linked.is_relative_to(ROOT.resolve()),target)
            self.assertTrue(linked.is_file(),target)

    def test_recipe_rejects_local_and_editor_metadata(self):
        base={'blueprint_id':'uo_regen_multi_0100_v1','name':'Tour',
              'lot':{'width':16,'depth':16},'floors':[{'level':0}]}
        verify_recipe(base)
        with self.assertRaises(ValueError):
            verify_recipe({**base,'preview_image':'data:image/png;base64,not-public'})
        with self.assertRaises(ValueError):
            verify_recipe({**base,'runtime_profile':{'hlod_scene':'res://private.tscn'}})
