import hashlib
import json
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


class CrabAssetsTest(unittest.TestCase):
    def test_catalogued_assets_and_registration(self):
        catalog = json.loads((ROOT / 'templates/catalog.json').read_text(encoding='utf8'))
        entries = [x for x in catalog['entries'] if x.get('id') == 'xeno-editor:giant-crab-original' and x.get('version') == '0.1.0']
        self.assertEqual(len(entries), 1)
        spec = json.loads((ROOT / entries[0]['file']).read_text(encoding='utf8'))['spec']
        assets = {}
        for name in ('genome', 'source_recipe', 'preview', 'godot_preview', 'registration'):
            path = PurePosixPath(spec[name + '_file'])
            self.assertEqual(path.parts[:2], ('assets', 'xeno-editor'))
            self.assertNotIn('..', path.parts)
            assets[name] = (ROOT / path).read_bytes()
            self.assertEqual(hashlib.sha256(assets[name]).hexdigest(), spec[name + '_sha256'])
        genome = json.loads(assets['genome'])
        registration = json.loads(assets['registration'])
        self.assertTrue(genome['review_only'])
        self.assertFalse(genome['server_authoritative'])
        self.assertEqual(genome['bestiary_provenance']['recipe_sha256'], spec['source_recipe_sha256'])
        self.assertTrue(assets['preview'].startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertTrue(assets['godot_preview'].startswith(b'\x89PNG\r\n\x1a\n'))
        by_id = {x['id']: x for x in spec['parts']}
        self.assertEqual(len(by_id), len(spec['parts']))
        self.assertEqual(set(by_id), {x['part_id'] for x in genome['parts']})
        self.assertEqual(set(by_id), {x['id'] for x in registration['assets']})
        for item in registration['assets']:
            part = by_id[item['id']]
            path = PurePosixPath(part['file'])
            self.assertEqual(path.parts[:2], ('assets', 'xeno-editor'))
            self.assertNotIn('..', path.parts)
            data = (ROOT / path).read_bytes()
            self.assertTrue(data.startswith(b'glTF'))
            self.assertEqual(hashlib.sha256(data).hexdigest(), part['sha256'])
            self.assertEqual(part['sha256'], item['sha256'])
            self.assertEqual(item['relative_path'], 'XenoParts/' + item['id'] + '.glb')


if __name__ == '__main__':
    unittest.main()
