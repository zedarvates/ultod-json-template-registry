import unittest
from pathlib import Path
from scripts.migrate_cohort_ten import build,convert
class Tests(unittest.TestCase):
 def test_minimal(self):
  r=convert("cosmetic","templates/cosmetic/wings/v0.1.0/template.json",{"id":"wings","name":"Wings","category":"Back","rarity_tier":"Epic","mesh_path":"x"},set());self.assertEqual(r.document["spec"],{"display_name":"Wings","category_tag":"back","rarity_tag":"epic"});self.assertNotIn("mesh_path",str(r.document))
 def test_authoritative(self):self.assertEqual(convert("ai","templates/ai/guard/v0.1.0/template.json",{"id":"guard","name":"Guard","behavior_tree":{}},set()).disposition,"legacy-only-authoritative")
 def test_real(self):
  p=build(Path("."));self.assertEqual(len(p["results"]),41);self.assertEqual(p["counts"],{"legacy-only-authoritative":36,"migrated":5})
