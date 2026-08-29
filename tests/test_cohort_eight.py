import unittest
from pathlib import Path
from scripts.migrate_cohort_eight import build,convert
class Tests(unittest.TestCase):
 def test_minimal(self):
  r=convert("templates/energy/mana/v0.1.0/template.json",{"id":"mana","name":"Mana","max_capacity":100,"regeneration_rate":2},set());self.assertEqual(r.document["spec"],{"display_name":"Mana"});self.assertNotIn("max_capacity",str(r.document))
 def test_runtime(self):self.assertEqual(convert("templates/energy/node/v0.1.0/template.json",{"id":"node","name":"Node","position":{}},set()).disposition,"legacy-only-authoritative")
 def test_real(self):
  p=build(Path("."));self.assertEqual(len(p["results"]),32);self.assertEqual(p["counts"],{"legacy-only-authoritative":6,"migrated":26})
